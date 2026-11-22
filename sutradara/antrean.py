"""Antrean naskah: ide/naskah dari bot Telegram -> naskah terstruktur -> verifikasi dalil -> tinjauan pemilik.

Bot (bot/worker.js) hanya menyimpan masukan ke `antrean/<id>/` lalu memicu workflow `naskah` (workflow_dispatch).
Pekerjaan berat ada di sini (Python, teruji):
- `ide`    : topik -> naskah oleh Claude (aturan Kisah Islami; dalil HANYA rujukan, teksnya diambil verifikasi);
- `tempel` : naskah jadi dari pemilik -> dirapikan ke format (narasi TIDAK diubah; dicek otomatis);
- `revisi` : naskah + catatan pemilik -> naskah baru;
lalu: validasi format, tolak huruf Arab di narasi, verifikasi dalil (Quran Foundation + dataset hadis),
tulis `naskah.json` + `status.json`, perbarui kartu status di Telegram, kirim naskah untuk ditinjau.

FORMAT NASKAH (dipakai bot sekarang dan sutradara otomatis Tahap D nanti; subset dari rencana tanpa `shot`):
{
  "judul": "Nabi Hud dan Kaum 'Ad",
  "inti": "satu kalimat inti cerita",
  "dalil": [{"id": "hud50", "jenis": "quran", "label": "QS HUD 50", "surah": 11, "ayat": "50"},
            {"id": "b3343", "jenis": "hadis", "label": "HR. BUKHARI 3343", "kitab": "bukhari", "nomor": "3343"}],
  "beat": [{"narasi": "…", "dalil": ["hud50"], "suasana": "senja", "kata_kunci": ["kaum", "angin"]}]
}
Status: antrean/<id>/status.json -> kartu status (sama persis dengan bot/worker.js `kartuStatus`, diuji dengan fixture).
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

AKAR = Path(__file__).resolve().parents[1]
ANTREAN = AKAR / "antrean"
SUASANA = ["senja", "dhuha", "malam", "malam_merah", "fajar"]
KITAB = ["bukhari", "muslim", "abudawud", "tirmidhi", "nasai", "ibnmajah"]
TAHAP = [("diterima", "Naskah diterima"), ("dalil", "Dalil diverifikasi"), ("tinjau", "Disetujui pemilik"),
         ("narasi", "Narasi"), ("sutradara", "Sutradara"), ("render", "Render"), ("periksa", "Pemeriksaan"),
         ("kirim", "Dikirim untuk persetujuan")]
IKON = {"selesai": "✅", "jalan": "⏳", "gagal": "❌", "tunggu": "⏸", "belum": "▫️"}
MODEL_IDE = "claude-sonnet-4-5"
MODEL_RAPIKAN = "claude-haiku-4-5-20251001"
_ARAB = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")


# ---------------- status & kartu ----------------
def status_baru(id_: str, judul: str, sumber: str) -> dict:
    return {"id": id_, "judul": judul, "sumber": sumber, "tahap": {k: "belum" for k, _ in TAHAP}, "ket": {},
            "dibuat": _sekarang(), "diperbarui": _sekarang()}


def kartu(st: dict) -> str:
    """Teks kartu status. HARUS identik dengan kartuStatus() di bot/worker.js (tests/data/kartu_status.json)."""
    baris = [f"🎬 {st.get('judul') or st['id']}"]
    for k, label in TAHAP:
        keadaan = st["tahap"].get(k, "belum")
        ket = (st.get("ket") or {}).get(k)
        baris.append(f"{IKON[keadaan]} {label}" + (f" — {ket}" if ket else ""))
    return "\n".join(baris)


def atur(st: dict, tahap: str, keadaan: str, ket: str | None = None) -> dict:
    st["tahap"][tahap] = keadaan
    if ket:
        st.setdefault("ket", {})[tahap] = ket
    else:
        st.setdefault("ket", {}).pop(tahap, None)
    st["diperbarui"] = _sekarang()
    return st


def _sekarang() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


# ---------------- normalisasi & validasi naskah ----------------
_JENIS = {"quran": "quran", "qs": "quran", "ayat": "quran", "al-quran": "quran", "alquran": "quran", "al quran": "quran",
          "hadis": "hadis", "hadits": "hadis", "hadith": "hadis", "hr": "hadis"}


def normalisasi(n: dict) -> dict:
    """Rapikan salah ketik yang aman tanpa menutupi kesalahan struktur untuk validator."""
    if not isinstance(n, dict):
        return n
    daftar_dalil = n.get("dalil")
    if not isinstance(daftar_dalil, list):
        return n
    for d in daftar_dalil:
        if not isinstance(d, dict):
            continue
        j = _JENIS.get(str(d.get("jenis", "")).strip().lower())
        if j:
            d["jenis"] = j
        if d.get("jenis") == "quran" and str(d.get("surah", "")).strip().isdigit():
            d["surah"] = int(str(d["surah"]).strip())
        if "ayat" in d:
            d["ayat"] = str(d["ayat"]).replace(" ", "")
        if "nomor" in d:
            d["nomor"] = str(d["nomor"]).strip().lower()
        if "kitab" in d:
            d["kitab"] = re.sub(r"[^a-z]", "", str(d["kitab"]).lower()).replace("sahih", "").replace("sunan", "")
        d.setdefault("label", d.get("id", "dalil"))
    daftar_beat = n.get("beat")
    if not isinstance(daftar_beat, list):
        return n
    ada = {d.get("id") for d in daftar_dalil if isinstance(d, dict) and isinstance(d.get("id"), str)}
    for i, b in enumerate(daftar_beat, 1):
        if not isinstance(b, dict):
            continue
        rujukan = b.get("dalil")
        if isinstance(rujukan, list):
            hilang = [r for r in rujukan if isinstance(r, str) and r not in ada]
            if hilang:
                # Jangan menghapus rujukan yang tidak dikenal: validator harus melihatnya
                # agar beat faktual tidak lolos setelah kehilangan satu-satunya dalil.
                peringatan = n.get("peringatan")
                if not isinstance(peringatan, list):
                    peringatan = []
                    n["peringatan"] = peringatan
                peringatan.append(
                    f"beat {i}: rujukan {', '.join(map(str, hilang))} tidak ditemukan di daftar dalil")
        if b.get("suasana") not in SUASANA:
            b.pop("suasana", None)
    return n

def validasi(n: dict) -> list[str]:
    """Validasi format naskah dan beri petunjuk berbahasa Indonesia yang bisa ditindaklanjuti."""
    if not isinstance(n, dict):
        return ["naskah harus berupa objek JSON, bukan teks atau daftar"]
    g: list[str] = []
    if not isinstance(n.get("judul"), str) or not n["judul"].strip():
        g.append("judul kosong; isi dengan judul cerita")
    if not isinstance(n.get("inti"), str) or not n["inti"].strip():
        g.append("inti kosong; tulis satu kalimat tentang pesan/peristiwa utama cerita")

    daftar = n.get("dalil", [])
    if not isinstance(daftar, list):
        g.append("dalil harus berupa daftar rujukan; gunakan [] bila tidak ada")
        daftar = []
    ids: set[str] = set()
    for i, d in enumerate(daftar, 1):
        if not isinstance(d, dict):
            g.append(f"dalil ke-{i} harus berupa objek dengan id, jenis, label, dan rujukan")
            continue
        id_ = d.get("id")
        if not isinstance(id_, str) or not id_.strip():
            g.append(f"dalil ke-{i} tanpa id; beri id singkat yang unik")
        elif id_ in ids:
            g.append(f"id dalil '{id_}' dipakai lebih dari sekali; satukan rujukan yang sama")
        else:
            ids.add(id_)
        if not isinstance(d.get("label"), str) or not d["label"].strip():
            g.append(f"dalil ke-{i}: label kosong; tulis label rujukan yang mudah dibaca")
        if d.get("jenis") == "quran":
            if (not isinstance(d.get("surah"), int) or isinstance(d.get("surah"), bool)
                    or not (1 <= d["surah"] <= 114)
                    or not re.fullmatch(r"\d+(-\d+)?", str(d.get("ayat", "")))):
                g.append(f"dalil {id_ or i}: nomor surah/ayat tidak sah; gunakan surah 1–114 dan ayat angka atau rentang, misalnya '37-38'")
        elif d.get("jenis") == "hadis":
            if d.get("kitab") not in KITAB:
                g.append(f"dalil {id_ or i}: kitab '{d.get('kitab')}' belum didukung; pilih {', '.join(KITAB)}")
            if not re.fullmatch(r"\d+[a-z]?", str(d.get("nomor", ""))):
                g.append(f"dalil {id_ or i}: nomor hadis tidak sah; gunakan nomor dari sumber rujukan")
        else:
            g.append(f"dalil {id_ or i}: jenis harus 'quran' atau 'hadis'")

    beat = n.get("beat")
    if not isinstance(beat, list) or not beat:
        return g + ["beat kosong; pecah cerita menjadi satu atau beberapa bagian (beat)"]
    for i, b in enumerate(beat, 1):
        if not isinstance(b, dict):
            g.append(f"beat {i} harus berupa objek JSON")
            continue
        narasi = b.get("narasi")
        if not isinstance(narasi, str) or not narasi.strip():
            g.append(f"beat {i}: narasi kosong; tulis kalimat bahasa Indonesia")
        elif _ARAB.search(narasi):
            g.append(f"beat {i}: ada huruf Arab di narasi; bacaan Arab tidak disuarakan AI, tampilkan melalui sumber/kartu dalil")
        kata = b.get("kata_kunci")
        if not isinstance(kata, list) or any(not isinstance(x, str) or not x.strip() for x in kata):
            g.append(f"beat {i}: kata_kunci harus berupa daftar kata/frasa singkat; gunakan [] bila tidak ada")
        peran = b.get("peran")
        if not isinstance(peran, list) or any(not isinstance(x, str) or not x.strip() for x in peran):
            g.append(f"beat {i}: peran harus berupa daftar nama tokoh/pihak yang hadir atau dibahas; gunakan [] bila tidak ada")
        dialog = b.get("dialog", [])
        if not isinstance(dialog, list):
            g.append(f"beat {i}: dialog harus berupa daftar giliran bicara; gunakan [] bila tidak ada")
        else:
            nama_peran = {x for x in peran if isinstance(x, str)} if isinstance(peran, list) else set()
            for j, giliran in enumerate(dialog, 1):
                if not isinstance(giliran, dict):
                    g.append(f"beat {i} dialog {j}: harus berupa objek dengan pembicara dan ucapan")
                    continue
                for kunci in ("pembicara", "ucapan"):
                    if not isinstance(giliran.get(kunci), str) or not giliran[kunci].strip():
                        g.append(f"beat {i} dialog {j}: {kunci} kosong; isi nama peran/ucapan")
                if giliran.get("penjawab") is not None and not isinstance(giliran.get("penjawab"), str):
                    g.append(f"beat {i} dialog {j}: penjawab harus berupa nama peran atau null")
                for sisi in ("pembicara", "penjawab"):
                    nama = giliran.get(sisi)
                    if isinstance(nama, str) and nama.strip() and nama not in nama_peran:
                        g.append(f"beat {i} dialog {j}: {sisi} '{nama}' belum tercantum di peran; tambahkan agar bisa ditata dan digambar dengan aman")
                    if isinstance(nama, str) and _polos(nama) in {"allah", "tuhan"}:
                        g.append(f"beat {i} dialog {j}: Allah tidak digambarkan sebagai tokoh; gunakan narasi atau cahaya tanpa sosok")
        rujukan = b.get("dalil")
        if not isinstance(rujukan, list) or any(not isinstance(x, str) for x in rujukan):
            g.append(f"beat {i}: dalil harus berupa daftar id rujukan; gunakan [] bila beat bukan pernyataan fakta")
        else:
            for r in rujukan:
                if isinstance(r, str) and r not in ids:
                    g.append(f"beat {i}: id dalil '{r}' tidak ditemukan; periksa ejaan atau tambahkan rujukannya")
        suasana = b.get("suasana")
        if suasana is not None and suasana not in SUASANA:
            g.append(f"beat {i}: suasana '{suasana}' tidak dikenal; pilih {', '.join(SUASANA)}")
    return g

def _polos(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def narasi_utuh(n: dict, sumber: str) -> list[str]:
    """Naskah tempelan: setiap narasi harus ada di teks asli (narasi pemilik tidak boleh diubah AI). Pengaman kedua;
    jalur tempel mengambil narasi langsung dari teks pemilik."""
    asal = _polos(" ".join(paragraf(sumber)[1]))
    return [f"beat {i}: narasi tidak sama dengan naskah asli (\"{b['narasi'][:60]}…\")"
            for i, b in enumerate(n["beat"], 1) if _polos(b["narasi"]) not in asal]


# ---------------- AI (Claude) ----------------
ATURAN = f"""Aturan WAJIB (akun TikTok/FB "Alzazali | Kisah Islami"):
- Hanya dalil sahih/hasan. Untuk setiap dalil tulis RUJUKAN saja (QS nomor surah + ayat, atau hadis dari kitab {', '.join(KITAB)} + nomor sunnah.com). JANGAN menulis teks Arab atau terjemah dalil; teksnya diambil mesin dari sumber resmi. Ragu nomornya = jangan dicantumkan.
- Setiap beat yang menceritakan peristiwa/fakta kisah WAJIB punya dalil yang memuat fakta itu. Beat tanpa dalil hanya untuk pembuka, renungan, atau ajakan. Fakta yang tidak ada di Al-Qur'an/hadis sahih (cerita populer, israiliyat, tafsir, detail tambahan seperti bendungan, kekeringan, jumlah tahun) JANGAN ditulis.
- Tidak mengarang klaim; detail yang tidak ada di dalil tidak boleh disebut sebagai fakta. Bukan fatwa. Topik berat tidak dijadikan sensasi; selalu ada jalan keluar/hikmah.
- Narasi bahasa Indonesia, sapa penonton "kamu". Tidak ada huruf Arab di narasi.
- Mutu cerita: fakta terkuat yang menyangkut nasib penonton di kalimat pertama; satu video = cerita utuh (janji hook dijawab di video ini); setiap kalimat menambah informasi atau ketegangan, buang yang mengulang; durasi mengikuti cerita.
- Setiap beat berisi narasi, kata_kunci, dalil (id rujukan saja), suasana, dan peran (nama tokoh/pihak yang hadir atau dibahas; [] bila tidak ada).
- Bila ada ucapan langsung, tambahkan `dialog`: daftar `{{"pembicara": "nama peran", "ucapan": "...", "penjawab": "nama peran"}}`. Jangan membuat dialog baru yang tidak didukung sumber.
- Setiap beat yang menyatakan fakta/peristiwa wajib merujuk dalil yang benar-benar mendukungnya. Tanpa dalil hanya untuk pembuka nonfaktual, renungan, atau ajakan; jangan mengubah dugaan menjadi fakta.
- Jangan menebak nomor dalil. Jika ragu, jangan mencantumkannya dan beri catatan bahwa rujukan perlu diperiksa pemilik.
Keluarkan HANYA JSON valid berbentuk:
{{"judul": "...", "inti": "satu kalimat inti", "dalil": [{{"id": "hud50", "jenis": "quran", "label": "QS HUD 50", "surah": 11, "ayat": "50"}}, {{"id": "b3343", "jenis": "hadis", "label": "HR. BUKHARI 3343", "kitab": "bukhari", "nomor": "3343"}}], "beat": [{{"narasi": "...", "kata_kunci": ["..."], "dalil": ["hud50"], "suasana": "senja|dhuha|malam|malam_merah|fajar", "peran": ["Nabi Hud", "kaum 'Ad"], "dialog": [{{"pembicara": "Nabi Hud", "ucapan": "...", "penjawab": "kaum 'Ad"}}]}}]}}"""

SISTEM = {
    "ide": "Kamu penulis naskah video pendek Kisah Islami yang jujur dan kuat bercerita. Tulis naskah utuh dari topik pemilik.\n" + ATURAN,
    "tempel": """Kamu memetakan naskah yang SUDAH JADI dari pemilik. Paragrafnya sudah bernomor; kamu TIDAK menulis ulang narasi.
Kelompokkan paragraf berurutan menjadi beat (biasanya 1 paragraf = 1 beat), lalu isi dalil yang DISEBUT di naskah (jangan menambah dalil sendiri), suasana, dan kata kunci.
Rujukan dalil ditulis seperti aturan di bawah (QS = nomor surah + ayat; hadis = kitab + nomor).
suasana HANYA salah satu: senja, dhuha, malam, malam_merah, fajar (waktu/cahaya adegan, bukan emosi).
Keluarkan HANYA JSON:
{"judul": "...", "inti": "...",
 "dalil": [{"id": "hud38", "jenis": "quran", "label": "QS HUD 38", "surah": 11, "ayat": "38"},
           {"id": "b3343", "jenis": "hadis", "label": "HR. BUKHARI 3343", "kitab": "bukhari", "nomor": "3343"}],
 "beat": [{"paragraf": [1], "dalil": ["hud38"], "suasana": "senja", "kata_kunci": ["..."], "peran": ["Nabi Nuh", "kaum pengejek"]}]}
Dalil yang sama (surah+ayat sama) cukup SATU id, dipakai di beberapa beat.
""" + ATURAN.split("Keluarkan HANYA JSON")[0],
    "revisi": "Kamu merevisi naskah sesuai catatan pemilik. Ubah HANYA yang diminta catatan; bagian lain tetap kata per kata.\n" + ATURAN,
}


def tanya_claude(sistem: str, isi: str, *, model: str, maks: int = 4000) -> tuple[str, int]:
    kunci = os.environ.get("ANTHROPIC_API_KEY")
    if not kunci:
        raise RuntimeError("ANTHROPIC_API_KEY belum diisi di GitHub Secrets repo ini")
    badan = {"model": model, "max_tokens": maks, "system": sistem, "messages": [{"role": "user", "content": isi}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(badan).encode(), method="POST",
                                 headers={"x-api-key": kunci, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        j = json.load(urllib.request.urlopen(req, timeout=240))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Claude galat {e.code}") from None
    u = j.get("usage") or {}
    return "".join(c.get("text", "") for c in j.get("content", [])), u.get("input_tokens", 0) + u.get("output_tokens", 0)


# ---------------- Gemini (gratis) dengan cadangan Claude ----------------
GEMINI = "https://generativelanguage.googleapis.com/v1beta"
_GEMINI_TERPILIH: dict = {}


def urutan_model_gemini(nama: list[str]) -> list[str]:
    """Model Gemini stabil (bukan preview/exp/image/tts/live), urut: Flash versi tertinggi dulu, lalu Flash-Lite.
    Model kedua dipakai bila yang pertama sedang penuh (503) atau kena batas (429)."""
    flash, lite = [], []
    for n in nama:
        n = n.split("/")[-1]
        m = re.fullmatch(r"gemini-(\d+(?:\.\d+)?)-flash(-lite)?", n)
        if m:
            (lite if m.group(2) else flash).append((float(m.group(1)), n))
    return [n for _, n in sorted(flash, reverse=True)[:2]] + [n for _, n in sorted(lite, reverse=True)[:1]]


def pilih_model_gemini(nama: list[str]) -> str | None:
    u = [n for n in urutan_model_gemini(nama) if not n.endswith("-lite")]
    return u[0] if u else None


def _gemini_req(path: str, kunci: str, badan: dict | None = None) -> dict:
    req = urllib.request.Request(f"{GEMINI}/{path}", data=json.dumps(badan).encode() if badan else None,
                                 method="POST" if badan else "GET",
                                 headers={"x-goog-api-key": kunci, "content-type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=150))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Gemini galat {e.code}") from None
    except (TimeoutError, urllib.error.URLError) as e:  # waktu habis/putus: model ini lambat -> coba model berikutnya
        raise RuntimeError(f"Gemini galat 504 ({str(e)[:60]})") from None


def tanya_gemini(sistem: str, isi: str, *, model: str | None = None, maks: int = 8000) -> tuple[str, int]:
    kunci = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not kunci:
        raise RuntimeError("GEMINI_API_KEY belum diisi")
    if os.environ.get("GEMINI_MODEL"):
        urutan = [os.environ["GEMINI_MODEL"]]
    else:
        if "urutan" not in _GEMINI_TERPILIH:
            daftar = _gemini_req("models?pageSize=200", kunci).get("models", [])
            _GEMINI_TERPILIH["urutan"] = urutan_model_gemini(
                [x["name"] for x in daftar if "generateContent" in x.get("supportedGenerationMethods", [])])
        urutan = _GEMINI_TERPILIH["urutan"]
    if not urutan:
        raise RuntimeError("tidak ada model Gemini Flash yang tersedia untuk kunci ini")
    badan = {"systemInstruction": {"parts": [{"text": sistem}]}, "contents": [{"role": "user", "parts": [{"text": isi}]}],
             "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": maks, "temperature": 0.7}}
    galat, j = None, None
    for m in urutan:  # model penuh/kena batas -> tunggu sebentar & coba lagi; lambat -> langsung model berikutnya
        for jeda in (0, 8, 20):
            time.sleep(jeda)
            try:
                j = _gemini_req(f"models/{m}:generateContent", kunci, badan)
                break
            except RuntimeError as e:
                galat = e
                if not re.search(r"galat (429|500|503|504)", str(e)):
                    raise
                if "504" in str(e):
                    break
        if j is not None:
            _GEMINI_TERPILIH["m"] = m
            break
    if j is None:
        raise galat or RuntimeError("Gemini tidak menjawab")
    teks = "".join(p.get("text", "") for c in j.get("candidates", [])[:1] for p in c.get("content", {}).get("parts", []))
    if not teks.strip():
        raise RuntimeError(f"Gemini tidak memberi jawaban ({(j.get('candidates') or [{}])[0].get('finishReason', '?')})")
    return teks, (j.get("usageMetadata") or {}).get("totalTokenCount", 0)


def tanya_otomatis(sistem: str, isi: str, *, model: str, maks: int = 4000) -> tuple[str, int]:
    """Gemini gratis dulu; bila tidak ada kunci, kena batas, atau gagal -> Claude (berbayar). Penyedia dicatat.
    NASKAH_CADANGAN=0 mematikan cadangan berbayar (untuk uji Gemini tanpa biaya)."""
    try:
        teks, token = tanya_gemini(sistem, isi)
        PENYEDIA["terakhir"] = f"Gemini {_GEMINI_TERPILIH.get('m') or os.environ.get('GEMINI_MODEL', '')} (gratis)"
        return teks, token
    except Exception as e:  # noqa: BLE001
        PENYEDIA["catatan"] = f"Gemini gagal ({str(e)[:80]}), pindah ke Claude"
        if os.environ.get("NASKAH_CADANGAN", "1") == "0":
            raise RuntimeError(f"Gemini gagal: {str(e)[:120]} (cadangan Claude dimatikan)") from None
    teks, token = tanya_claude(sistem, isi, model=model, maks=maks)
    PENYEDIA["terakhir"] = f"Claude {model}"
    return teks, token


PENYEDIA: dict = {}


def baca_json(teks: str) -> dict:
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", teks.strip())
    return json.loads(t[t.index("{"): t.rindex("}") + 1])


_RUJUKAN = re.compile(r"\s*[\(\[]\s*(?:QS|Q\.S\.|HR|H\.R\.|Hadis|Hadits)[^\)\]]*[\)\]]", re.I)


def paragraf(teks: str) -> tuple[str | None, list[str]]:
    """Naskah tempelan -> (judul bila ada baris 'Judul:', paragraf narasi tanpa catatan rujukan dalam kurung)."""
    judul, isi = None, []
    for p in re.split(r"\n\s*\n", teks.strip()):
        p = " ".join(p.split())
        m = re.match(r"(?i)^judul\s*:\s*(.+)$", p)
        if m and judul is None and not isi:
            judul = m.group(1).strip(); continue
        p = _RUJUKAN.sub("", p).strip()
        if p:
            isi.append(p)
    return judul, isi


def buat_naskah(mode: str, masukan: str, naskah_lama: dict | None = None, *, tanya=None) -> tuple[dict, int]:
    tanya = tanya or tanya_otomatis
    if mode == "tempel":  # narasi diambil APA ADANYA dari teks pemilik; AI hanya memetakan beat & dalil
        judul, par = paragraf(masukan)
        isi = "Naskah dari pemilik (paragraf bernomor):\n" + "\n".join(f"[{i}] {p}" for i, p in enumerate(par, 1))
        isi += "\n\nCatatan rujukan dalil asli dari pemilik:\n" + "\n".join(m.group(0).strip() for m in _RUJUKAN.finditer(masukan))
        teks, token = tanya(SISTEM["tempel"], isi, model=os.environ.get("MODEL_RAPIKAN", MODEL_RAPIKAN))
        peta = baca_json(teks)
        dipakai, beat_berurut = set(), []
        for b in peta.get("beat", []):
            nomor = [int(x) for x in b.get("paragraf", []) if str(x).isdigit() and 1 <= int(x) <= len(par) and int(x) not in dipakai]
            if not nomor:
                continue
            dipakai.update(nomor)
            beat_berurut.append((min(nomor), {"narasi": " ".join(par[i - 1] for i in nomor), "dalil": b.get("dalil", []),
                                               "suasana": b.get("suasana"), "kata_kunci": b.get("kata_kunci", []),
                                               "peran": b.get("peran", []), "dialog": b.get("dialog", [])}))
        for i in range(1, len(par) + 1):  # paragraf yang terlewat AI tidak boleh hilang
            if i not in dipakai:
                beat_berurut.append((i, {"narasi": par[i - 1], "dalil": [], "kata_kunci": [], "peran": [], "dialog": []}))
                dipakai.add(i)
        beat = [b for _, b in sorted(beat_berurut, key=lambda pasangan: pasangan[0])]
        for b in beat:
            if not b.get("suasana"):
                b.pop("suasana", None)
        return {"judul": judul or peta.get("judul") or par[0][:60], "inti": peta.get("inti", ""),
                "dalil": peta.get("dalil", []), "beat": beat}, token
    if mode == "revisi":
        isi = f"NASKAH SAAT INI:\n{json.dumps(naskah_lama, ensure_ascii=False)}\n\nCATATAN PEMILIK:\n{masukan}"
    else:
        isi = f"Topik/ide dari pemilik:\n{masukan}"
    teks, token = tanya(SISTEM[mode], isi, model=os.environ.get("MODEL_IDE", MODEL_IDE))
    return baca_json(teks), token


# ---------------- Telegram ----------------
def tg(metode: str, badan: dict) -> dict:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        return {"ok": False}
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{metode}", data=json.dumps(badan).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        return {"ok": False, "kode": e.code}


def tombol_kartu(st: dict) -> list:
    i = st["id"]
    if st["tahap"]["tinjau"] in ("belum", "jalan") and st["tahap"]["dalil"] in ("selesai", "gagal"):
        return [[{"text": "✅ Lanjut", "callback_data": f"nl:{i}"}, {"text": "✏️ Revisi", "callback_data": f"nr:{i}"}],
                [{"text": "❌ Batal", "callback_data": f"nb:{i}"}, {"text": "🏠 Menu", "callback_data": "menu"}]]
    return [[{"text": "🏠 Menu", "callback_data": "menu"}]]


def perbarui_kartu(st: dict) -> None:
    chat = st.get("chat") or (os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    if not chat:
        return
    badan = {"chat_id": chat, "text": kartu(st), "reply_markup": {"inline_keyboard": tombol_kartu(st)}}
    if st.get("pesan_kartu"):
        r = tg("editMessageText", {**badan, "message_id": st["pesan_kartu"]})
        if r.get("ok") or "not modified" in str(r):
            return
    r = tg("sendMessage", badan)
    if r.get("ok"):
        st["pesan_kartu"] = r["result"]["message_id"]


def teks_tinjauan(n: dict) -> list[str]:
    """Naskah untuk dibaca pemilik: per beat + status dalil + terjemah resmi (agar makna bisa dinilai)."""
    dl = {d["id"]: d for d in n.get("dalil", [])}
    out = [f"📝 {n['judul']}" + (f"\nInti: {n['inti']}" if n.get("inti") else "")
           + "".join(f"\n⚠️ {p}" for p in n.get("peringatan", []))]
    sudah = set()  # terjemah dalil yang sama cukup ditampilkan sekali
    for i, b in enumerate(n["beat"], 1):
        s = f"\n{i}. {b['narasi']}"
        if not b.get("dalil"):
            s += "\n   ▫️ tanpa dalil: pastikan bukan klaim karangan"
        for r in b.get("dalil") or []:
            d = dl.get(r, {})
            tanda = "✅" if d.get("status") == "terverifikasi" and d.get("derajat", "sahih") in ("sahih", "hasan") else "⚠️"
            s += f"\n   {tanda} {d.get('label', r)}" + (f" ({d['derajat']})" if d.get("derajat") else "")
            if d.get("alasan"):
                s += f": {d['alasan']}"
            elif r in sudah:
                s += " (terjemah di atas)"
            elif d.get("terjemah"):
                s += f": “{d['terjemah'][:220]}{'…' if len(d['terjemah']) > 220 else ''}”"
            sudah.add(r)
        out.append(s)
    out.append("\nCek: apakah setiap kalimat sesuai makna dalilnya? Lalu ketuk ✅ Lanjut / ✏️ Revisi / ❌ Batal di kartu status.")
    potong, buf = [], ""
    for bagian in out:  # batas pesan Telegram 4096
        if len(buf) + len(bagian) > 3800:
            potong.append(buf); buf = ""
        buf += bagian + "\n"
    return potong + [buf]


# ---------------- proses satu antrean ----------------
def proses(id_: str, mode: str, *, folder: Path = ANTREAN, tanya=None, quran=None, kirim_tg: bool = True) -> dict:
    d = folder / id_
    st = json.loads((d / "status.json").read_text(encoding="utf-8"))
    masukan = (d / ("catatan.txt" if mode == "revisi" else "masukan.txt")).read_text(encoding="utf-8")
    lama = json.loads((d / "naskah.json").read_text(encoding="utf-8")) if mode == "revisi" else None
    atur(st, "diterima", "jalan", "naskah sedang disusun AI" if mode != "tempel" else "naskah sedang dirapikan")
    for k in ("dalil", "tinjau"):
        atur(st, k, "belum")
    _tulis(d, st, None, kirim_tg)
    try:
        n, token = buat_naskah(mode, masukan, lama, tanya=tanya)
        n = normalisasi(n)
        galat = validasi(n)
        if mode == "tempel" and not galat:
            galat = narasi_utuh(n, masukan)
    except Exception as e:  # noqa: BLE001 - pesan untuk pemilik
        atur(st, "diterima", "gagal", f"gagal menyusun naskah: {str(e)[:150]}")
        _tulis(d, st, None, kirim_tg)
        return st
    st["judul"] = n.get("judul") or st.get("judul")
    st["token_ai"] = st.get("token_ai", 0) + token
    if PENYEDIA.get("terakhir"):
        st["penyedia_ai"] = PENYEDIA["terakhir"] + (f" — {PENYEDIA['catatan']}" if PENYEDIA.get("catatan") else "")
    if galat:
        atur(st, "diterima", "gagal", "; ".join(galat)[:300])
        _tulis(d, st, n, kirim_tg)
        return st
    atur(st, "diterima", "selesai", f"{len(n['beat'])} beat, {len(n.get('dalil', []))} dalil"
         + (f" · {PENYEDIA['terakhir'].split(' (')[0].split(' ')[0]}" if PENYEDIA.get("terakhir") else ""))
    atur(st, "dalil", "jalan")
    _tulis(d, st, n, kirim_tg)
    from .dalil.verifikasi import verifikasi
    n, laporan = verifikasi(n, quran=quran)
    lolos = [x for x in n.get("dalil", []) if x.get("status") == "terverifikasi" and x.get("derajat", "sahih") in ("sahih", "hasan")]
    total = len(n.get("dalil", []))
    if total and len(lolos) < total:
        atur(st, "dalil", "gagal", f"{len(lolos)}/{total} lolos; yang ⚠️ harus diganti atau dibuang")
    else:
        atur(st, "dalil", "selesai", f"{len(lolos)}/{total}" if total else "tanpa dalil")
    atur(st, "tinjau", "jalan", "menunggu Anda membaca naskah")
    st["laporan_dalil"] = laporan
    _tulis(d, st, n, kirim_tg)
    if kirim_tg:
        chat = st.get("chat") or os.environ.get("TELEGRAM_CHAT_ID", "").strip()
        for t in teks_tinjauan(n):
            tg("sendMessage", {"chat_id": chat, "text": t})
        if st.get("pesan_kartu"):  # kartu dipindah ke bawah naskah supaya tombolnya dekat dengan yang dibaca
            tg("deleteMessage", {"chat_id": chat, "message_id": st.pop("pesan_kartu")})
        perbarui_kartu(st)
        _tulis(d, st, n, False)
    return st


def _tulis(d: Path, st: dict, naskah: dict | None, kirim_tg: bool) -> None:
    if kirim_tg:
        perbarui_kartu(st)
    if naskah is not None:
        (d / "naskah.json").write_text(json.dumps(naskah, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (d / "status.json").write_text(json.dumps(st, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":  # python -m sutradara.antrean <id> <ide|tempel|revisi>
    from .dalil.quran import QuranBertingkat, QuranComPublik, QuranFoundation
    q = QuranBertingkat(QuranFoundation() if os.environ.get("QURAN_FOUNDATION_CLIENT_ID") else None, QuranComPublik())
    hasil = proses(sys.argv[1], sys.argv[2], quran=q)
    print(kartu(hasil)); print("penyedia AI:", hasil.get("penyedia_ai", "-"))
    sys.exit(1 if "gagal" in hasil["tahap"]["diterima"] else 0)
