"""Koreksi terjemah yang memerlukan persetujuan eksplisit pemilik sebelum masuk ke layar."""

from __future__ import annotations

import json
from pathlib import Path

BERKAS = Path(__file__).resolve().parents[2] / "data/koreksi_terjemah.json"


def daftar(path: Path = BERKAS) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("koreksi", [])


def terapkan_terjemah(dalil: dict, teks: str, *, koreksi: list[dict] | None = None) -> str:
    """Terapkan hanya koreksi berstatus disetujui_pemilik dan tepat satu kecocokan teks asli."""
    if dalil.get("jenis") != "hadis":
        return teks
    kitab = str(dalil.get("kitab", "")).strip().lower()
    nomor = str(dalil.get("nomor", "")).strip().lower()
    hasil = teks
    for item in daftar() if koreksi is None else koreksi:
        if item.get("status") != "disetujui_pemilik":
            continue
        if item.get("kitab") != kitab or str(item.get("nomor", "")).lower() != nomor:
            continue
        asli, usulan = item.get("teks_asli", ""), item.get("teks_koreksi", "")
        if not asli or not usulan or hasil.count(asli) != 1:
            continue
        hasil = hasil.replace(asli, usulan, 1)
    return hasil
