"""Verifikasi dalil dalam rencana: mengisi status, derajat, teks Arab, terjemahan, dan tautan dari sumber resmi.

Hanya modul ini yang boleh menulis `status: "terverifikasi"` (ditandai `diverifikasi_oleh`). Penjaga mode final menolak
dalil tanpa tanda itu, jadi status tidak bisa diketik tangan.

Yang DIJAMIN mesin: dalil ada di sumber, nomor/ayat benar, derajat hadis sahih/hasan (aturan di hadis.py).
Yang TIDAK dijamin: dalil dipakai dengan makna yang tepat dalam cerita -> selalu ditandai `makna: perlu_tinjauan_pemilik`.

Bentuk dalil di rencana (contoh):
  {"id": "hud38", "jenis": "quran", "label": "QS HUD 38", "surah": 11, "ayat": "38", "status": "belum"}
  {"id": "m2934", "jenis": "hadis", "label": "HR. MUSLIM 2934", "kitab": "muslim", "nomor": "2934", "status": "belum"}
"""
from __future__ import annotations

import copy
import datetime as _dt
import re

from . import hadis as H

PENANDA = "sutradara.dalil"


def _rentang(ayat) -> list[int]:
    s = str(ayat).strip()
    m = re.fullmatch(r"(\d+)\s*(?:-\s*(\d+))?", s)
    if not m:
        return []
    a = int(m.group(1)); b = int(m.group(2) or a)
    return list(range(a, b + 1)) if b >= a and b - a <= 30 else []


def _huruf(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("al-", "").replace("an-", "").replace("at-", "").replace("ash-", ""))


def _tanda(d: dict) -> None:
    d["diverifikasi_oleh"] = f"{PENANDA} {_dt.date.today().isoformat()}"
    # Persetujuan makna oleh pemilik tidak dihapus oleh verifikasi ulang.
    if not str(d.get("makna", "")).startswith("disetujui_pemilik"):
        d["makna"] = "perlu_tinjauan_pemilik"


def verifikasi_quran(d: dict, quran) -> str:
    surah, ayat = d.get("surah"), _rentang(d.get("ayat", ""))
    if not isinstance(surah, int) or not ayat:
        d.update(status="belum", alasan="surah/ayat tidak terisi atau tidak sah")
        return f"✗ {d['label']}: surah/ayat tidak sah"
    hasil = [quran.ayat(surah, a) for a in ayat]
    if any(h is None for h in hasil):
        d.update(status="belum", alasan="ayat tidak ditemukan di Quran Foundation")
        return f"✗ {d['label']}: ayat tidak ditemukan"
    nama = hasil[0].nama_surah
    d.update(status="terverifikasi", teks_ar=" ".join(h.ar for h in hasil), terjemah=" ".join(h.terjemah for h in hasil),
             sumber_teks=f"Quran Foundation · {hasil[0].sumber_terjemah}", rujukan=hasil[0].tautan)
    # Pasangan hanya disimpan bila setiap kata memiliki terjemah word-by-word dari API.
    if hasil and all(h.kata for h in hasil):
        d["pasangan_kata"] = [pasangan for h in hasil for pasangan in h.kata]
    else:
        d.pop("pasangan_kata", None)
    d.pop("alasan", None)
    _tanda(d)
    nomor_ayat = str(d["ayat"]).replace(" ", "")
    if nama and (_huruf(nama) not in _huruf(d["label"]) or nomor_ayat not in d["label"].replace(" ", "")):
        d["label_saran"] = f"QS {nama.upper()} {nomor_ayat}"
        return f"✓ {d['label']} (label disarankan: {d['label_saran']})"
    return f"✓ {d['label']}"


def verifikasi_hadis(d: dict) -> str:
    kitab, nomor = d.get("kitab"), d.get("nomor")
    if not H.kitab_baku(kitab or ""):
        d.update(status="belum", alasan=f"kitab '{kitab}' belum ada di dataset (tersedia: {', '.join(H.KITAB)})")
        return f"✗ {d['label']}: kitab tidak tersedia"
    riwayat = H.cari(kitab, nomor)
    if not riwayat:
        d.update(status="belum", alasan="nomor tidak ditemukan di dataset sunnah.com")
        return f"✗ {d['label']}: nomor tidak ditemukan"
    r = riwayat[0]
    drj, berbeda = H.derajat(kitab, r.penilaian)
    terjemah = r.id or r.en
    d.update(status="terverifikasi", derajat=drj, teks_ar=r.ar, terjemah=terjemah,
             sumber_teks=f"sunnah.com · {H.KITAB[r.kitab]}" + ("" if r.id else " (terjemah Inggris)"),
             rujukan=r.tautan, riwayat=len(riwayat))
    if berbeda:
        d["berbeda"] = berbeda
    if H.bukan_marfu(r.penilaian):
        d["bukan_marfu"] = True
    d.pop("alasan", None)
    _tanda(d)
    if drj not in ("sahih", "hasan"):
        return f"✗ {d['label']}: derajat {drj}"
    return f"✓ {d['label']} ({drj}{', dinilai daif oleh ' + ', '.join(berbeda) if berbeda else ''})"


def verifikasi(rencana: dict, *, quran=None) -> tuple[dict, list[str]]:
    """Kembalikan (rencana baru, laporan). `quran`: objek dengan .ayat(surah, ayat) (mis. QuranFoundation)."""
    r = copy.deepcopy(rencana)
    laporan = []
    for d in r.get("dalil", []):
        if d["jenis"] == "quran":
            if quran is None:
                laporan.append(f"… {d['label']}: dilewati (klien Quran tidak tersedia)")
                continue
            try:
                laporan.append(verifikasi_quran(d, quran))
            except RuntimeError as e:  # gangguan layanan/izin: ayat ini tetap 'belum', yang lain jalan terus
                d.update(status="belum", alasan=f"Quran Foundation: {e}")
                laporan.append(f"✗ {d['label']}: {e}")
        else:
            laporan.append(verifikasi_hadis(d))
    return r, laporan
