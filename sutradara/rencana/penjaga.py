"""Penjaga rencana: struktur (JSON Schema) + aturan keselamatan & resep yang TIDAK bisa ditawar lewat naskah.

Hasil berupa daftar Temuan. tingkat="GAGAL" menghentikan render final; "PERIKSA" = saran resep/estetika.
Aturan bersumber dari docs/PANDUAN_GAYA.md (batas wajib) dan docs/RESEP_SUTRADARA.md (resep).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

from ..gaya.latar import PRESET

SKEMA = json.loads((Path(__file__).parent / "rencana.schema.json").read_text(encoding="utf-8"))
SAKRAL = {"nabi", "malaikat", "sahabat"}
# setengah lebar visual inti (px pada s=1) untuk mengukur jarak tepi; benda lain memakai BAWAAN
SETENGAH_LEBAR = {"bahtera": 500, "retakan_bumi": 140, "dua_sungai": 300}
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
        if k in SAKRAL and tp != "nur":
            t.append(Temuan("GAGAL", "TOKOH_SUCI", f"{p['nama']} ({k}) harus tampil 'nur' (pilar cahaya), bukan '{tp}'"))
        if k not in SAKRAL and tp == "nur":
            t.append(Temuan("GAGAL", "NUR_KHUSUS", f"pilar cahaya hanya untuk nabi/malaikat/sahabat, bukan {p['nama']} ({k})"))
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
            t += _periksa_shot(s, peran, f"beat {i} shot {j}")
            if b.get("pelaku"):
                t += _periksa_penataan(s, b["pelaku"], vi["benda"], peran, f"beat {i} shot {j}")
        if len(b["shot"]) < len(b.get("potong_di", [])) + 1:
            t.append(Temuan("PERIKSA", "POTONG_DI_KATA", f"beat {i}: {len(b.get('potong_di', []))} kata potong tapi hanya {len(b['shot'])} shot"))
    if len(dipakai) < 2:
        t.append(Temuan("PERIKSA", "VISUAL_INTI_DIAM", f"'{vi['benda']}' hanya tampil dalam satu keadaan; resep A1 meminta keadaannya berubah"))
    if beat and rencana["hook"]["dari_beat"] == 0 and len(beat) > 3:
        t.append(Temuan("PERIKSA", "HOOK_KRONOLOGIS", "hook diambil dari beat pertama; resep A3: pindahkan momen paling dramatis ke depan"))
    return t


def _periksa_shot(s: dict, peran: dict, lokasi: str) -> list[Temuan]:
    t = []
    for tk in s.get("tokoh", []):
        pid = tk.get("peran")
        if pid and pid in peran and peran[pid]["kategori"] in SAKRAL:
            t.append(Temuan("GAGAL", "TOKOH_SUCI", f"{lokasi}: '{peran[pid]['nama']}' digambar sebagai tokoh; pakai 'nur'"))
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


def _periksa_penataan(s: dict, pid: str, inti: str, peran: dict, lokasi: str) -> list[Temuan]:
    """Penataan panggung: pelaku aksi harus berdiri di dekat visual inti yang ia kerjakan, dan tidak ada tokoh lain
    yang lebih dekat ke visual inti daripada pelaku (kalau ada, penonton salah membaca siapa yang berbuat)."""
    benda = next((b for b in s.get("benda", []) if b.get("jenis") == inti), None)
    pos = _posisi_pelaku(s, pid, peran)
    if benda is None or pos is None or not isinstance(benda.get("x"), (int, float)) or not isinstance(pos[0], (int, float)):
        return []
    hw = SETENGAH_LEBAR.get(inti, SETENGAH_LEBAR_BAWAAN) * float(benda.get("s", 1) if isinstance(benda.get("s", 1), (int, float)) else 1)
    jarak = lambda x: max(0.0, abs(x - benda["x"]) - hw)
    t = []
    jp = jarak(pos[0])
    if jp > JARAK_PELAKU_MAKS:
        t.append(Temuan("PERIKSA", "PELAKU_JAUH", f"{lokasi}: {peran[pid]['nama']} berbuat pada {inti} tapi berdiri {jp:.0f} px dari tepinya"))
    lain = [tk for tk in s.get("tokoh", []) if tk.get("peran") != pid and isinstance(tk.get("x"), (int, float))]
    lebih_dekat = [tk for tk in lain if jarak(tk["x"]) + 1 < jp and abs(tk["y"] - benda.get("y", tk["y"])) < PITA_KEDALAMAN]
    if lebih_dekat:
        t.append(Temuan("PERIKSA", "BUKAN_PELAKU_DEKAT", f"{lokasi}: {len(lebih_dekat)} tokoh lain lebih dekat ke {inti} daripada {peran[pid]['nama']}"))
    return t


def ringkas(temuan: list[Temuan]) -> str:
    if not temuan:
        return "LULUS: tidak ada temuan"
    g = sum(1 for x in temuan if x.tingkat == "GAGAL")
    return ("GAGAL" if g else "LULUS dengan catatan") + f" ({g} gagal, {len(temuan) - g} periksa)\n" + "\n".join(map(str, temuan))
