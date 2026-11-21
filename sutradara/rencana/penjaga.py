"""Penjaga rencana: struktur (JSON Schema) + aturan keselamatan & resep yang TIDAK bisa ditawar lewat naskah.

Hasil berupa daftar Temuan. tingkat="GAGAL" menghentikan render final; "PERIKSA" = saran resep/estetika.
Aturan bersumber dari docs/PANDUAN_GAYA.md (batas wajib) dan docs/RESEP_SUTRADARA.md (resep).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

from ..dalil.segmen import kutipan_sah
from ..gaya.latar import PRESET

SKEMA = json.loads((Path(__file__).parent / "rencana.schema.json").read_text(encoding="utf-8"))
SAKRAL = {"nabi", "malaikat", "sahabat"}
# setengah lebar visual inti (px pada s=1) untuk mengukur jarak tepi; benda lain memakai BAWAAN
SETENGAH_LEBAR = {"bahtera": 350, "retakan_bumi": 140, "dua_sungai": 300}
SETENGAH_LEBAR_BAWAAN = 200
JARAK_PELAKU_MAKS = 160  # px dari tepi visual inti
PITA_KEDALAMAN = 180  # tokoh yang kakinya > 180 px di depan visual inti dianggap lewat di depan, bukan berdiri di sampingnya
ALASAN_SILUET = {"misteri", "kilas_balik", "kerumunan_sangat_jauh", "wajah_disembunyikan"}


@dataclass
class Temuan:
    tingkat: str  # GAGAL | PERIKSA
    kode: str
    pesan: str

    def __str__(self) -> str:
        return f"[{self.tingkat}] {self.kode}: {self.pesan}"


def periksa(rencana: dict, *, final: bool = False) -> list[Temuan]:
    """Periksa satu rencana. final=True: dalil berstatus 'belum' menjadi GAGAL (bukan sekadar PERIKSA)."""
    t: list[Temuan] = []
    for e in sorted(Draft202012Validator(SKEMA).iter_errors(rencana), key=lambda e: list(e.path)):
        t.append(Temuan("GAGAL", "SKEMA", f"{'/'.join(map(str, e.path)) or '(akar)'}: {e.message}"))
    if t:
        return t

    peran = {p["id"]: p for p in rencana["peran"]}
    for p in rencana["peran"]:
        k, tp = p["kategori"], p["tampil"]
        cara_wajib = {"nabi": "nur", "malaikat": "cahaya_malaikat", "sahabat": "wajah_cahaya"}
        kode_wajib = {"nabi": "TOKOH_SUCI", "malaikat": "MALAIKAT_TAMPIL", "sahabat": "SAHABAT_TAMPIL"}
        if k in cara_wajib and tp != cara_wajib[k]:
            t.append(Temuan("GAGAL", kode_wajib[k], f"{p['nama']} ({k}) wajib tampil '{cara_wajib[k]}', bukan '{tp}'"))
        if k not in SAKRAL and tp == "nur":
            t.append(Temuan("GAGAL", "NUR_KHUSUS", f"pilar cahaya khusus nabi tidak boleh dipakai untuk {p['nama']} ({k})"))
        elif k not in SAKRAL and tp in {"cahaya_malaikat", "wajah_cahaya"}:
            t.append(Temuan("GAGAL", "CAHAYA_KHUSUS", f"bentuk cahaya khusus tokoh mulia tidak boleh dipakai untuk {p['nama']} ({k})"))
        if k == "makhluk_ghaib" and not p.get("wujud_dalil") and tp != "kabut_tanpa_wujud":
            t.append(Temuan("GAGAL", "WUJUD_TAK_DIJELASKAN", f"wujud {p['nama']} tidak dijelaskan dalil sahih: harus 'kabut_tanpa_wujud'"))
        if k == "dajjal" and tp not in ("dajjal_b", "siluet"):
            t.append(Temuan("GAGAL", "DAJJAL", f"Dajjal hanya 'dajjal_b' (ciri hadis) atau 'siluet' (misteri), bukan '{tp}'"))
        if k == "yajuj_majuj" and tp not in ("pakaian", "siluet"):
            t.append(Temuan("GAGAL", "YAJUJ_MANUSIA", "Ya'juj Ma'juj adalah manusia (HR. Bukhari 3348): 'pakaian' atau 'siluet'"))
        if tp == "siluet" and p.get("alasan_siluet") not in ALASAN_SILUET:
            t.append(Temuan("PERIKSA", "SILUET_TANPA_ALASAN",
                            f"{p['nama']} siluet tanpa alasan sah ({', '.join(sorted(ALASAN_SILUET))}); bawaan tokoh biasa = 'pakaian'"))

    dalil = {d["id"]: d for d in rencana["dalil"]}
    for d in rencana["dalil"]:
        rujuk = (d.get("kitab") and d.get("nomor")) if d["jenis"] == "hadis" else (d.get("surah") and d.get("ayat"))
        if not rujuk:
            t.append(Temuan("GAGAL" if final else "PERIKSA", "DALIL_TANPA_RUJUKAN",
                            f"{d['label']}: isi {'kitab & nomor' if d['jenis'] == 'hadis' else 'surah & ayat'} supaya bisa diverifikasi"))
        sah = d["status"] == "terverifikasi" and str(d.get("diverifikasi_oleh", "")).startswith("sutradara.dalil")
        if not sah:
            t.append(Temuan("GAGAL" if final else "PERIKSA", "DALIL_BELUM_DICEK",
                            f"{d['label']} belum diverifikasi mesin ({d.get('alasan') or 'jalankan: python -m sutradara verifikasi'})"))
        if d["jenis"] == "hadis" and d["status"] == "terverifikasi" and d.get("derajat") not in ("sahih", "hasan"):
            t.append(Temuan("GAGAL", "DERAJAT_HADIS", f"{d['label']}: derajat {d.get('derajat')}; hanya hadis sahih/hasan"))
        if d.get("berbeda"):
            t.append(Temuan("PERIKSA", "DERAJAT_DIPERSELISIHKAN", f"{d['label']}: dinilai daif oleh {', '.join(d['berbeda'])}"))
        for kunci, sumber in (("kutipan_ar", "teks_ar"), ("kutipan_id", "terjemah")):
            if d.get(kunci) and d.get(sumber) and not kutipan_sah(d[kunci], d[sumber]):
                t.append(Temuan("GAGAL", "KUTIPAN_TIDAK_ADA_DI_SUMBER", f"{d['label']}: {kunci} bukan potongan persis {sumber} terverifikasi"))
        if d.get("bukan_marfu"):
            t.append(Temuan("PERIKSA", "BUKAN_MARFU", f"{d['label']}: mauquf/maqtu (ucapan sahabat/tabi'in), jangan disebut sabda Nabi ﷺ"))
        if d.get("label_saran"):
            t.append(Temuan("PERIKSA", "LABEL_DALIL", f"{d['label']}: label yang cocok dengan sumber '{d['label_saran']}'"))

    vi = rencana["visual_inti"]
    jalur = vi["jalur_keadaan"]
    beat = rencana["beat"]
    if not (0 <= rencana["hook"]["dari_beat"] < len(beat)):
        t.append(Temuan("GAGAL", "HOOK", f"hook.dari_beat={rencana['hook']['dari_beat']} di luar jumlah beat ({len(beat)})"))
    dipakai = set()
    for i, b in enumerate(beat):
        if b["preset"] not in PRESET:
            t.append(Temuan("GAGAL", "PRESET", f"beat {i}: preset '{b['preset']}' tak dikenal ({', '.join(PRESET)})"))
        if b["keadaan"] not in jalur:
            t.append(Temuan("GAGAL", "KEADAAN", f"beat {i}: keadaan '{b['keadaan']}' tidak ada di visual_inti.jalur_keadaan"))
        dipakai.add(b["keadaan"])
        for did in b.get("dalil", []):
            if did not in dalil:
                t.append(Temuan("GAGAL", "DALIL_TAK_TERDAFTAR", f"beat {i}: dalil '{did}' tidak ada di daftar dalil"))
        for pid in b.get("peran_tampil", []):
            if pid not in peran:
                t.append(Temuan("GAGAL", "PERAN_TAK_TERDAFTAR", f"beat {i}: peran '{pid}' tidak terdaftar"))
        for j, s in enumerate(b["shot"]):
            lokasi = f"beat {i} shot {j}"
            t += _periksa_shot(s, peran, lokasi)
            for tk in s.get("tokoh", []):
                pid = tk.get("peran")
                if pid in peran and peran[pid]["kategori"] in {"nabi", "malaikat"}:
                    t.append(Temuan("GAGAL", "TOKOH_SUCI_BERTUBUH",
                                    f"{lokasi}: {peran[pid]['nama']} tidak boleh dirender sebagai tubuh; gunakan bentuk cahaya khusus"))
            for cahaya in s.get("nur", []):
                pid = cahaya.get("peran")
                if pid not in peran:
                    t.append(Temuan("GAGAL", "CAHAYA_TANPA_PERAN",
                                    f"{lokasi}: setiap bentuk cahaya harus merujuk id peran nabi atau malaikat"))
                elif peran[pid]["kategori"] == "sahabat":
                    t.append(Temuan("GAGAL", "SAHABAT_BERTIANG",
                                    f"{lokasi}: sahabat harus tubuh berbaju dengan wajah cahaya, bukan pilar/berkas"))
                elif peran[pid]["kategori"] not in {"nabi", "malaikat"}:
                    t.append(Temuan("GAGAL", "CAHAYA_KHUSUS",
                                    f"{lokasi}: bentuk cahaya tidak boleh dipakai oleh {peran[pid]['nama']}"))
                elif peran[pid]["kategori"] == "nabi" and peran[pid]["tampil"] != "nur":
                    t.append(Temuan("GAGAL", "NABI_BUKAN_PILAR",
                                    f"{lokasi}: nabi harus memakai pilar cahaya"))
                elif peran[pid]["kategori"] == "malaikat" and peran[pid]["tampil"] != "cahaya_malaikat":
                    t.append(Temuan("GAGAL", "MALAIKAT_BUKAN_BERKAS",
                                    f"{lokasi}: malaikat harus memakai berkas cahaya tanpa wujud"))
            for bi, buraq in enumerate(s.get("buraq", [])):
                if "penunggang" in buraq or buraq.get("naik_di") == "buraq":
                    t.append(Temuan("GAGAL", "PENUNGGANG_BURAQ",
                                    f"beat {i} shot {j} Buraq {bi}: Buraq tidak boleh digambar dengan penunggang; hadirkan pilar nur terpisah bila diperlukan"))
                for tokoh in s.get("tokoh", []):
                    tx, ty = tokoh.get("x"), tokoh.get("y")
                    bs = float(buraq.get("s", 1)) if isinstance(buraq.get("s", 1), (int, float)) else 1.0
                    bx, by = buraq.get("x"), buraq.get("y")
                    if tokoh.get("naik_di") == "buraq" or (
                        isinstance(tx, (int, float)) and isinstance(ty, (int, float))
                        and isinstance(bx, (int, float)) and isinstance(by, (int, float))
                        and abs(tx - bx) < 150 * bs and by - 330 * bs < ty < by - 80 * bs
                    ):
                        t.append(Temuan("GAGAL", "PENUNGGANG_BURAQ",
                                        f"beat {i} shot {j}: tokoh berada di area punggung Buraq; penunggang tidak boleh digambar sebagai manusia"))
            t += _periksa_kartu(s, dalil, final, f"beat {i} shot {j}")
            if b.get("pelaku"):
                t += _periksa_penataan(s, b["pelaku"], vi["benda"], peran, f"beat {i} shot {j}")
        if len(b["shot"]) < len(b.get("potong_di", [])) + 1:
            t.append(Temuan("PERIKSA", "POTONG_DI_KATA", f"beat {i}: {len(b.get('potong_di', []))} kata potong tapi hanya {len(b['shot'])} shot"))
    if len(dipakai) < 2:
        t.append(Temuan("PERIKSA", "VISUAL_INTI_DIAM", f"'{vi['benda']}' hanya tampil dalam satu keadaan; resep A1 meminta keadaannya berubah"))
    if beat and rencana["hook"]["dari_beat"] == 0 and len(beat) > 3:
        t.append(Temuan("PERIKSA", "HOOK_KRONOLOGIS", "hook diambil dari beat pertama; resep A3: pindahkan momen paling dramatis ke depan"))
    t += _periksa_identitas(rencana)
    t += _periksa_barang(rencana, peran)
    return t


def peran_mode(peta_peran: dict, pid: str) -> str:
    return "siluet" if (peta_peran.get(pid) or {}).get("tampil") == "siluet" else "pakaian"


def _periksa_identitas(rencana: dict) -> list[Temuan]:
    """Bandingkan ciri stabil shot dengan kartu pemeran dan pisahkan drift dari perubahan gaya.

    Asal: adaptasi konsep pemeriksaan kontinuitas dari
    mesin-video/papan/intelligence.py (feat/short-term-production-intelligence),
    terutama profil atribut stabil dan REVIEW alih-alih ERROR untuk perubahan desain.
    Identitas di repo ini menggunakan peran.id + peran.identitas, tanpa registri/SQLite lama.
    """
    hasil = []
    kunci = {
        "jenis": "jenis", "usia": "usia", "zaman": "zaman", "indeks": "indeks",
        "warna_kulit": "warna_kulit", "warna_baju": "warna_baju",
        "warna_aksen": "warna_aksen", "rambut": "rambut", "janggut": "janggut",
        "warna_janggut": "warna_janggut", "aksesori": "aksesori", "suara": "suara",
        "ciri_wajah": "ciri_wajah", "kepala": "penutup_kepala",
    }
    peta_peran = {p["id"]: p for p in rencana.get("peran", [])}
    kartu_pemeran = {p["id"]: p for p in rencana.get("pemeran", [])}
    kartu = {pid: p.get("identitas", {}) for pid, p in peta_peran.items()}
    kartu.update({pid: p.get("identitas", {}) for pid, p in kartu_pemeran.items()})
    for bi, beat in enumerate(rencana.get("beat", [])):
        for si, shot in enumerate(beat.get("shot", [])):
            for tokoh in shot.get("tokoh", []):
                pid = tokoh.get("pemeran_id") or tokoh.get("peran")
                if tokoh.get("pemeran_id") and pid not in kartu_pemeran:
                    hasil.append(Temuan("GAGAL", "PEMERAN_TAK_TERDAFTAR",
                                        f"beat {bi} shot {si}: pemeran_id {pid!r} tidak memiliki kartu identitas"))
                    continue
                ident = kartu.get(pid) or {}
                if not ident:
                    continue
                beda = [(field, ident[acuan], tokoh[field]) for field, acuan in kunci.items()
                        if field in tokoh and acuan in ident and tokoh[field] != ident[acuan]]
                if beda:
                    rincian = ", ".join(f"{f}: {a!r} -> {b!r}" for f, a, b in beda)
                    hasil.append(Temuan("PERIKSA", "IDENTITAS_BERUBAH",
                                        f"beat {bi} shot {si} {pid}: ciri kartu pemeran berubah ({rincian}); perbarui kartu hanya bila perubahan memang menjadi desain baru"))
                id_peran = tokoh.get("peran")
                mode_dasar = peran_mode(peta_peran, id_peran)
                mode_shot = tokoh.get("mode", mode_dasar)
                if mode_shot != mode_dasar:
                    alasan = str(tokoh.get("perubahan_gaya", "")).strip()
                    if alasan:
                        hasil.append(Temuan("PERIKSA", "PERUBAHAN_GAYA_DISENGAJA",
                                            f"beat {bi} shot {si} {pid}: gaya {mode_dasar} -> {mode_shot}; alasan: {alasan}"))
                    else:
                        hasil.append(Temuan("PERIKSA", "IDENTITAS_GAYA_BERUBAH",
                                            f"beat {bi} shot {si} {pid}: gaya {mode_dasar} -> {mode_shot} tanpa perubahan_gaya yang menjelaskan pengungkapan/perubahan visual"))
    return hasil


def _periksa_barang(rencana: dict, peran: dict) -> list[Temuan]:
    """Jaga kepemilikan, serah-terima, dan keberlanjutan barang antar-shot."""
    hasil, sebelumnya = [], {}
    for bi, beat in enumerate(rencana.get("beat", [])):
        for si, shot in enumerate(beat.get("shot", [])):
            lokasi = f"beat {bi} shot {si}"
            sekarang = {}
            for item in shot.get("barang", []):
                iid, pemilik = item.get("id"), item.get("pemilik")
                if not iid or iid in sekarang:
                    hasil.append(Temuan("GAGAL", "ID_BARANG", f"{lokasi}: id barang kosong atau duplikat ({iid})"))
                    continue
                sekarang[iid] = item
                if pemilik not in peran:
                    hasil.append(Temuan("GAGAL", "PEMILIK_BARANG", f"{lokasi}: pemilik {pemilik!r} tidak terdaftar"))
                    continue
                if item.get("tangan", "ka") not in {"ka", "ki"}:
                    hasil.append(Temuan("GAGAL", "TANGAN_BARANG", f"{lokasi} {iid}: tangan harus ka/ki"))
                kategori = peran[pemilik]["kategori"]
                if kategori == "nabi":
                    if not any(n.get("peran") == pemilik for n in shot.get("nur", [])):
                        hasil.append(Temuan("GAGAL", "BARANG_NABI_TANPA_PILAR", f"{lokasi} {iid}: barang milik nabi harus tampil di sisi pilarnya, tanpa tangan"))
                elif not any(tk.get("peran") == pemilik for tk in shot.get("tokoh", [])):
                    hasil.append(Temuan("PERIKSA", "PEMILIK_BARANG_TAK_TAMPIL", f"{lokasi} {iid}: pemilik {pemilik} tidak tampak pada shot"))
                aksi = item.get("aksi", "pegang")
                if aksi in {"ulurkan", "terima"}:
                    if not item.get("titik_serah") or len(item["titik_serah"]) != 2:
                        hasil.append(Temuan("GAGAL", "TITIK_SERAH_BARANG", f"{lokasi} {iid}: aksi {aksi} perlu titik_serah [x,y]"))
                    pasangan = item.get("penerima") if aksi == "ulurkan" else item.get("pemberi")
                    if pasangan not in peran:
                        hasil.append(Temuan("GAGAL", "PASANGAN_SERAH_TERIMA", f"{lokasi} {iid}: pasangan serah-terima tidak terdaftar"))
                    elif peran[pasangan]["kategori"] == "nabi" and not any(n.get("peran") == pasangan for n in shot.get("nur", [])):
                        hasil.append(Temuan("GAGAL", "PILAR_PASANGAN_TAK_TAMPIL", f"{lokasi} {iid}: pilar nabi {pasangan} tidak tampak pada serah-terima"))
                    elif peran[pasangan]["kategori"] != "nabi" and not any(tk.get("peran") == pasangan for tk in shot.get("tokoh", [])):
                        hasil.append(Temuan("PERIKSA", "PASANGAN_TAK_TAMPIL", f"{lokasi} {iid}: pasangan {pasangan} tidak tampak"))
                if iid in sebelumnya:
                    lama = sebelumnya[iid]
                    pemilik_lama = lama.get("pemilik")
                    if pemilik_lama != pemilik:
                        sah = (lama.get("aksi") == "ulurkan" and lama.get("penerima") == pemilik
                               and aksi == "terima" and item.get("pemberi") == pemilik_lama)
                        if not sah:
                            hasil.append(Temuan("GAGAL", "PEMILIK_BARANG_BERUBAH",
                                                f"{lokasi} {iid}: pemilik berubah {pemilik_lama} -> {pemilik} tanpa pasangan ulurkan/terima"))
                elif aksi == "terima":
                    hasil.append(Temuan("PERIKSA", "BARANG_TANPA_ADEGAN_ULUR",
                                        f"{lokasi} {iid}: adegan terima tidak punya shot ulurkan sebelumnya"))
            for iid, lama in sebelumnya.items():
                if iid not in sekarang:
                    hasil.append(Temuan("PERIKSA", "BARANG_TIDAK_DIBAWA",
                                        f"{lokasi}: barang {iid} dari shot sebelumnya tidak dicantumkan; periksa kesinambungan"))
            sebelumnya = sekarang
    return hasil


def _periksa_kartu(s: dict, dalil: dict, final: bool, lokasi: str) -> list[Temuan]:
    kd = s.get("kartu_dalil")
    if not kd:
        return []
    d = dalil.get(kd.get("dalil"))
    if d is None:
        return [Temuan("GAGAL", "KARTU_DALIL", f"{lokasi}: kartu merujuk dalil '{kd.get('dalil')}' yang tidak terdaftar")]
    t = []
    if not (d.get("teks_ar") and d.get("terjemah")):
        t.append(Temuan("GAGAL" if final else "PERIKSA", "KARTU_TANPA_TEKS", f"{lokasi}: {d['label']} belum punya teks terverifikasi (jalankan verifikasi)"))
    if d["jenis"] == "hadis" and not (d.get("kutipan_ar") and d.get("kutipan_id")):
        t.append(Temuan("PERIKSA", "KARTU_HADIS_TANPA_KUTIPAN", f"{lokasi}: {d['label']} tanpa kutipan -> sanad ikut tampil; isi kutipan_ar/kutipan_id"))
    return t


def _periksa_shot(s: dict, peran: dict, lokasi: str) -> list[Temuan]:
    t = []
    for tk in s.get("tokoh", []):
        pid = tk.get("peran")
        if pid and pid in peran and peran[pid]["kategori"] in {"nabi", "malaikat"}:
            t.append(Temuan("GAGAL", "TOKOH_SUCI", f"{lokasi}: '{peran[pid]['nama']}' tidak boleh digambar sebagai tubuh; gunakan bentuk cahaya khusus"))
    if s.get("preset") not in PRESET:
        t.append(Temuan("GAGAL", "PRESET", f"{lokasi}: preset '{s.get('preset')}' tak dikenal"))
    return t


def _posisi_pelaku(s: dict, pid: str, peran: dict) -> tuple[float, float] | None:
    p = peran.get(pid)
    if not p:
        return None
    if p["tampil"] == "nur":
        return (s["nur"][0]["x"], s["nur"][0]["y"]) if s.get("nur") else None
    for tk in s.get("tokoh", []):
        if tk.get("peran") == pid:
            return tk["x"], tk["y"]
    return None


def _periksa_penataan(s: dict, pid: str | list[str], inti: str, peran: dict, lokasi: str) -> list[Temuan]:
    """Semua pelaku bersama harus dekat dengan visual inti; tokoh non-pelaku yang lebih dekat tetap ditandai."""
    benda = next((b for b in s.get("benda", []) if b.get("jenis") == inti), None)
    if benda is None or not isinstance(benda.get("x"), (int, float)):
        return []
    ids = [pid] if isinstance(pid, str) else list(pid)
    posisi = [(aktor, _posisi_pelaku(s, aktor, peran)) for aktor in ids]
    posisi = [(aktor, pos) for aktor, pos in posisi if pos is not None and isinstance(pos[0], (int, float))]
    if not posisi:
        return []
    hw = SETENGAH_LEBAR.get(inti, SETENGAH_LEBAR_BAWAAN) * float(benda.get("s", 1) if isinstance(benda.get("s", 1), (int, float)) else 1)
    jarak = lambda x: max(0.0, abs(x - benda["x"]) - hw)
    t = []
    jarak_pelaku = {aktor: jarak(pos[0]) for aktor, pos in posisi}
    jauh = [(aktor, jp) for aktor, jp in jarak_pelaku.items() if jp > JARAK_PELAKU_MAKS]
    if jauh:
        nama = ", ".join(peran[aktor]["nama"] for aktor, _ in jauh)
        t.append(Temuan("PERIKSA", "PELAKU_JAUH", f"{lokasi}: {nama} berbuat pada {inti} tetapi terlalu jauh dari tepinya"))
    jp_terdekat = min(jarak_pelaku.values())
    id_pelaku = set(ids)
    lain = [tk for tk in s.get("tokoh", []) if tk.get("peran") not in id_pelaku and isinstance(tk.get("x"), (int, float))]
    lebih_dekat = [tk for tk in lain if jarak(tk["x"]) + 1 < jp_terdekat and abs(tk["y"] - benda.get("y", tk["y"])) < PITA_KEDALAMAN]
    if lebih_dekat:
        t.append(Temuan("PERIKSA", "BUKAN_PELAKU_DEKAT", f"{lokasi}: {len(lebih_dekat)} tokoh non-pelaku lebih dekat ke {inti} daripada pelaku terdekat"))
    return t


def ringkas(temuan: list[Temuan]) -> str:
    if not temuan:
        return "LULUS: tidak ada temuan"
    g = sum(1 for x in temuan if x.tingkat == "GAGAL")
    return ("GAGAL" if g else "LULUS dengan catatan") + f" ({g} gagal, {len(temuan) - g} periksa)\n" + "\n".join(map(str, temuan))
