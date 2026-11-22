"""Penjaga inti rencana: skema umum dan delegasi ke validator paket genre.

Nama-nama lama tetap diekspor sebagai shim agar integrasi dan pengujian terdahulu
tidak putus selama pemisahan implementasi.
"""
from __future__ import annotations

import copy
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SKEMA = json.loads((Path(__file__).parent / "rencana.schema.json").read_text(encoding="utf-8"))


@dataclass
class Temuan:
    tingkat: str  # GAGAL | PERIKSA
    kode: str
    pesan: str

    def __str__(self) -> str:
        return f"[{self.tingkat}] {self.kode}: {self.pesan}"


def _skema_paket(paket) -> dict[str, Any]:
    """Gabungkan ekstensi skema paket ke skema inti tanpa mengizinkan override diam-diam."""
    hasil = copy.deepcopy(SKEMA)
    tambahan = dict(paket.skema_tambahan)
    properti = tambahan.pop("properties", {})
    if not isinstance(properti, dict):
        raise TypeError(f"skema_tambahan paket {paket.nama!r}: properties harus berupa objek")
    inti = hasil.setdefault("properties", {})
    bentrok = set(inti).intersection(properti)
    if bentrok:
        raise ValueError(
            f"skema_tambahan paket {paket.nama!r} menimpa properti inti: {', '.join(sorted(bentrok))}"
        )
    inti.update(properti)

    wajib = tambahan.pop("required", [])
    if not isinstance(wajib, list) or any(not isinstance(n, str) for n in wajib):
        raise TypeError(f"skema_tambahan paket {paket.nama!r}: required harus berupa daftar nama")
    if wajib:
        hasil["required"] = list(dict.fromkeys([*hasil.get("required", []), *wajib]))

    # Kata kunci JSON Schema lain tetap didukung sebagai batas tambahan,
    # bukan pengganti aturan inti.
    if tambahan:
        hasil = {"allOf": [hasil, tambahan]}
    return hasil


def periksa(rencana: dict, *, final: bool = False) -> list[Temuan]:
    """Periksa skema inti + ekstensi paket, lalu delegasikan aturan domain."""
    from ..genre import dari_rencana

    paket = dari_rencana(rencana)
    skema = _skema_paket(paket)
    temuan = [
        Temuan("GAGAL", "SKEMA", f"{'/'.join(map(str, e.path)) or '(akar)'}: {e.message}")
        for e in sorted(Draft202012Validator(skema).iter_errors(rencana), key=lambda e: list(e.path))
    ]
    if temuan:
        return temuan

    if paket.validator is None:
        return []
    hasil = paket.validator(rencana, final=final)
    if not isinstance(hasil, list) or any(not isinstance(item, Temuan) for item in hasil):
        raise TypeError(f"validator genre {paket.nama!r} harus mengembalikan list[Temuan]")
    return hasil


def ringkas(temuan: list[Temuan]) -> str:
    if not temuan:
        return "LULUS: tidak ada temuan"
    g = sum(1 for x in temuan if x.tingkat == "GAGAL")
    return ("GAGAL" if g else "LULUS dengan catatan") + f" ({g} gagal, {len(temuan) - g} periksa)\n" + "\n".join(map(str, temuan))


def __getattr__(nama: str) -> Any:
    """Shim lazy untuk konstanta/helper lama yang kini dimiliki paket Kisah Islami."""
    if nama.startswith("__"):
        raise AttributeError(nama)
    modul = importlib.import_module("sutradara.paket_genre.kisah_islami.penjaga")
    try:
        return getattr(modul, nama)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {nama!r}") from None
