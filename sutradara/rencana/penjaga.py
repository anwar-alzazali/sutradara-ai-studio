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
        if d["status"] != "terverifikasi":
            t.append(Temuan("GAGAL" if final else "PERIKSA", "DALIL_BELUM_DICEK", f"{d['label']} belum diverifikasi ke sumber resmi"))
        if d["jenis"] == "hadis" and d.get("derajat") not in ("sahih", "hasan"):
            t.append(Temuan("GAGAL", "DERAJAT_HADIS", f"{d['label']}: hanya hadis sahih/hasan"))

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


def ringkas(temuan: list[Temuan]) -> str:
    if not temuan:
        return "LULUS: tidak ada temuan"
    g = sum(1 for x in temuan if x.tingkat == "GAGAL")
    return ("GAGAL" if g else "LULUS dengan catatan") + f" ({g} gagal, {len(temuan) - g} periksa)\n" + "\n".join(map(str, temuan))
