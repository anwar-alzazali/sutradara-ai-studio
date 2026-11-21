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


# ---------------- validasi naskah ----------------
def validasi(n: dict) -> list[str]:
    """Galat format dalam bahasa awam (kosong = sah)."""
    g = []
    if not isinstance(n, dict):
        return ["naskah bukan objek JSON"]
    if not str(n.get("judul", "")).strip():
        g.append("judul kosong")
    beat = n.get("beat")
    if not isinstance(beat, list) or not beat:
        return g + ["tidak ada beat (bagian cerita)"]
    ids = set()
    for i, d in enumerate(n.get("dalil") or [], 1):
        if not d.get("id"):
            g.append(f"dalil ke-{i} tanpa id"); continue
        ids.add(d["id"])
        if d.get("jenis") == "quran":
            if not isinstance(d.get("surah"), int) or not (1 <= d["surah"] <= 114) or not re.fullmatch(r"\d+(-\d+)?", str(d.get("ayat", ""))):
                g.append(f"dalil {d['id']}: nomor surah/ayat tidak sah")
        elif d.get("jenis") == "hadis":
            if d.get("kitab") not in KITAB:
                g.append(f"dalil {d['id']}: kitab '{d.get('kitab')}' belum didukung (tersedia: {', '.join(KITAB)})")
            if not re.fullmatch(r"\d+[a-z]?", str(d.get("nomor", ""))):
                g.append(f"dalil {d['id']}: nomor hadis tidak sah")
        else:
            g.append(f"dalil {d['id']}: jenis harus 'quran' atau 'hadis'")
    for i, b in enumerate(beat, 1):
        if not str(b.get("narasi", "")).strip():
            g.append(f"beat {i}: narasi kosong")
        if _ARAB.search(str(b.get("narasi", ""))):
            g.append(f"beat {i}: ada huruf Arab di narasi (bacaan Arab tidak disuarakan AI; tampilkan lewat kartu dalil)")
        for r in b.get("dalil") or []:
            if r not in ids:
                g.append(f"beat {i}: merujuk dalil '{r}' yang tidak ada di daftar dalil")
        if b.get("suasana") and b["suasana"] not in SUASANA:
            g.append(f"beat {i}: suasana '{b['suasana']}' tidak dikenal ({', '.join(SUASANA)})")
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
- Tidak mengarang klaim; detail yang tidak ada di dalil tidak boleh disebut sebagai fakta. Bukan fatwa. Topik berat tidak dijadikan sensasi; selalu ada jalan keluar/hikmah.
- Narasi bahasa Indonesia, sapa penonton "kamu". Tidak ada huruf Arab di narasi.
- Mutu cerita: fakta terkuat yang menyangkut nasib penonton di kalimat pertama; satu video = cerita utuh (janji hook dijawab di video ini); setiap kalimat menambah informasi atau ketegangan, buang yang mengulang; durasi mengikuti cerita.
Keluarkan HANYA JSON valid berbentuk:
{{"judul": "...", "inti": "satu kalimat inti", "dalil": [{{"id": "hud50", "jenis": "quran", "label": "QS HUD 50", "surah": 11, "ayat": "50"}}, {{"id": "b3343", "jenis": "hadis", "label": "HR. BUKHARI 3343", "kitab": "bukhari", "nomor": "3343"}}], "beat": [{{"narasi": "...", "dalil": ["hud50"], "suasana": "senja|dhuha|malam|malam_merah|fajar", "kata_kunci": ["..."]}}]}}"""

SISTEM = {
    "ide": "Kamu penulis naskah video pendek Kisah Islami yang jujur dan kuat bercerita. Tulis naskah utuh dari topik pemilik.\n" + ATURAN,
    "tempel": """Kamu memetakan naskah yang SUDAH JADI dari pemilik. Paragrafnya sudah bernomor; kamu TIDAK menulis ulang narasi.
Kelompokkan paragraf berurutan menjadi beat (biasanya 1 paragraf = 1 beat), lalu isi dalil yang DISEBUT di naskah (jangan menambah dalil sendiri), suasana, dan kata kunci.
Rujukan dalil ditulis seperti aturan di bawah (QS = nomor surah + ayat; hadis = kitab + nomor).
Keluarkan HANYA JSON: {"judul": "...", "inti": "...", "dalil": [...], "beat": [{"paragraf": [1], "dalil": ["id"], "suasana": "...", "kata_kunci": ["..."]}]}
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


def buat_naskah(mode: str, masukan: str, naskah_lama: dict | None = None, *, tanya=tanya_claude) -> tuple[dict, int]:
    if mode == "tempel":  # narasi diambil APA ADANYA dari teks pemilik; AI hanya memetakan beat & dalil
        judul, par = paragraf(masukan)
        isi = "Naskah dari pemilik (paragraf bernomor):\n" + "\n".join(f"[{i}] {p}" for i, p in enumerate(par, 1))
        isi += "\n\nCatatan rujukan dalil asli dari pemilik:\n" + "\n".join(m.group(0).strip() for m in _RUJUKAN.finditer(masukan))
        teks, token = tanya(SISTEM["tempel"], isi, model=os.environ.get("MODEL_RAPIKAN", MODEL_RAPIKAN))
        peta = baca_json(teks)
        dipakai, beat = set(), []
        for b in peta.get("beat", []):
            nomor = [int(x) for x in b.get("paragraf", []) if str(x).isdigit() and 1 <= int(x) <= len(par) and int(x) not in dipakai]
            if not nomor:
                continue
            dipakai.update(nomor)
            beat.append({"narasi": " ".join(par[i - 1] for i in nomor), "dalil": b.get("dalil", []),
                         "suasana": b.get("suasana"), "kata_kunci": b.get("kata_kunci", [])})
        for i in range(1, len(par) + 1):  # paragraf yang terlewat AI tidak boleh hilang
            if i not in dipakai:
                beat.append({"narasi": par[i - 1], "dalil": []}); dipakai.add(i)
        urut = {p: i for i, p in enumerate(par)}
        beat.sort(key=lambda b: min(urut.get(p, 0) for p in par if p in b["narasi"]))
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
    out = [f"📝 {n['judul']}" + (f"\nInti: {n['inti']}" if n.get("inti") else "")]
    for i, b in enumerate(n["beat"], 1):
        s = f"\n{i}. {b['narasi']}"
        for r in b.get("dalil") or []:
            d = dl.get(r, {})
            tanda = "✅" if d.get("status") == "terverifikasi" and d.get("derajat", "sahih") in ("sahih", "hasan") else "⚠️"
            s += f"\n   {tanda} {d.get('label', r)}" + (f" ({d['derajat']})" if d.get("derajat") else "")
            if d.get("alasan"):
                s += f": {d['alasan']}"
            elif d.get("terjemah"):
                s += f": “{d['terjemah'][:220]}{'…' if len(d['terjemah']) > 220 else ''}”"
        out.append(s)
    out.append("\nCek: apakah setiap kalimat sesuai makna dalilnya? Lalu ketuk ✅ Lanjut / ✏️ Revisi / ❌ Batal di kartu status.")
    potong, buf = [], ""
    for bagian in out:  # batas pesan Telegram 4096
        if len(buf) + len(bagian) > 3800:
            potong.append(buf); buf = ""
        buf += bagian + "\n"
    return potong + [buf]


# ---------------- proses satu antrean ----------------
def proses(id_: str, mode: str, *, folder: Path = ANTREAN, tanya=tanya_claude, quran=None, kirim_tg: bool = True) -> dict:
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
        galat = validasi(n)
        if mode == "tempel" and not galat:
            galat = narasi_utuh(n, masukan)
    except Exception as e:  # noqa: BLE001 - pesan untuk pemilik
        atur(st, "diterima", "gagal", f"gagal menyusun naskah: {str(e)[:150]}")
        _tulis(d, st, None, kirim_tg)
        return st
    st["judul"] = n.get("judul") or st.get("judul")
    st["token_ai"] = st.get("token_ai", 0) + token
    if galat:
        atur(st, "diterima", "gagal", "; ".join(galat)[:300])
        _tulis(d, st, n, kirim_tg)
        return st
    atur(st, "diterima", "selesai", f"{len(n['beat'])} beat, {len(n.get('dalil', []))} dalil")
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
    print(kartu(hasil))
    sys.exit(1 if "gagal" in hasil["tahap"]["diterima"] else 0)
