"""Pencarian hadis di dataset lokal (data/hadis, dibangun oleh `unduh_hadis`) + penilaian derajat.

Nomor = penomoran sunnah.com (yang dikutip di layar). Kitab: bukhari, muslim, abudawud, tirmidhi, nasai, ibnmajah.
Musnad Ahmad dan kitab lain BELUM ada di dataset -> verifikasi menandainya "tidak ditemukan" (tidak pernah dianggap lulus).

Aturan derajat (dikunci, lihat AGENTS.md):
- Bukhari & Muslim: sahih (kesepakatan ulama atas kedua kitab).
- Kitab lain: penilai utama Al-Albani. Sahih/hasan (termasuk "Hasan Sahih", "... li ghairihi") -> diterima.
  Daif/munkar/maudu/syadz menurut Al-Albani -> ditolak. Tanpa nilai Al-Albani -> suara mayoritas penilai; seri -> ditolak.
- Bila penilai lain menyatakan daif padahal Al-Albani menerima: tetap diterima, tetapi dicatat `berbeda` untuk ditinjau.
"""
from __future__ import annotations

import gzip
import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .unduh_hadis import AKAR, KITAB

DATA = AKAR / "data/hadis"
NAMA_LAYAR = {"bukhari": "BUKHARI", "muslim": "MUSLIM", "abudawud": "ABU DAWUD", "tirmidhi": "TIRMIDZI",
              "nasai": "NASA'I", "ibnmajah": "IBNU MAJAH"}
ALIAS = {"bukhari": "bukhari", "al-bukhari": "bukhari", "muslim": "muslim", "abu dawud": "abudawud", "abudawud": "abudawud",
         "abi dawud": "abudawud", "tirmidzi": "tirmidhi", "tirmidhi": "tirmidhi", "at-tirmidzi": "tirmidhi",
         "nasai": "nasai", "nasa'i": "nasai", "an-nasai": "nasai", "ibnu majah": "ibnmajah", "ibn majah": "ibnmajah", "ibnmajah": "ibnmajah"}
_TERIMA = re.compile(r"\b(sahih|saheeh|sahīh|hasan)\b", re.I)
_TOLAK = re.compile(r"\b(da['’]?if|daeef|dha['’]?if|munkar|maud[uū]['’]?|mawdu|shadh|syadz|batil|matruk|mursal)\b", re.I)
_BUKAN_MARFU = re.compile(r"\b(maqtu|mauquf|mawquf|muquf)\b", re.I)


@dataclass
class Hadis:
    kitab: str
    nomor: str
    sub: str
    n: int
    ar: str
    id: str
    en: str
    penilaian: list = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"HR. {NAMA_LAYAR[self.kitab]} {self.nomor}"

    @property
    def tautan(self) -> str:
        return f"https://sunnah.com/{self.kitab}:{self.nomor}{self.sub}"


def kitab_baku(nama: str) -> str | None:
    return ALIAS.get((nama or "").strip().lower())


@lru_cache(maxsize=None)
def _muat(kitab: str, folder: str) -> dict:
    f = Path(folder) / f"{kitab}.json.gz"
    if not f.exists():
        raise FileNotFoundError(f"dataset {f} belum ada; jalankan: python -m sutradara.dalil.unduh_hadis")
    with gzip.open(f, "rt", encoding="utf-8") as g:
        return json.load(g)["hadis"]


def cari(kitab: str, nomor, *, folder: Path | None = None) -> list[Hadis]:
    """Semua riwayat di bawah satu nomor sunnah.com. Nomor boleh berakhiran huruf ('2934b') untuk satu riwayat saja."""
    k = kitab_baku(kitab)
    if not k:
        return []
    m = re.fullmatch(r"\s*(\d+)\s*([a-z]?)\s*", str(nomor))
    if not m:
        return []
    pokok, sub = m.group(1), m.group(2)
    hasil = [Hadis(k, pokok, e["sub"], e["n"], e["ar"], e["id"], e["en"], e["derajat"]) for e in _muat(k, str(folder or DATA)).get(pokok, [])]
    return [h for h in hasil if h.sub == sub] if sub else hasil


def bukan_marfu(penilaian: list[dict]) -> bool:
    """True bila penilai utama menyebut riwayat ini mauquf/maqtu (ucapan sahabat/tabi'in, bukan sabda Nabi ﷺ)."""
    utama = [p for p in penilaian if "albani" in p.get("name", "").lower()] or penilaian
    return any(_BUKAN_MARFU.search(p.get("grade", "")) for p in utama)


def derajat(kitab: str, penilaian: list[dict]) -> tuple[str, list[str]]:
    """Kembalikan (derajat, berbeda). derajat: 'sahih' | 'hasan' | 'daif' | 'tidak_dinilai'. `berbeda` = penilai yang menolak."""
    k = kitab_baku(kitab)
    if k in ("bukhari", "muslim"):
        return "sahih", []
    def jenis(g: str) -> str | None:
        if _TOLAK.search(g):
            return "daif"
        if _TERIMA.search(g):
            return "sahih" if re.search(r"sah[iī]h|saheeh", g, re.I) else "hasan"
        return None
    nilai = [(p.get("name", ""), jenis(p.get("grade", ""))) for p in penilaian]
    nilai = [(n, j) for n, j in nilai if j]
    albani = next((j for n, j in nilai if "albani" in n.lower()), None)
    if albani:
        utama = albani
    elif nilai:
        terima = sum(1 for _, j in nilai if j != "daif"); tolak = len(nilai) - terima
        utama = ("sahih" if any(j == "sahih" for _, j in nilai) else "hasan") if terima > tolak else "daif"
    else:
        return "tidak_dinilai", []
    berbeda = [n for n, j in nilai if j == "daif"] if utama != "daif" else []
    return utama, berbeda
