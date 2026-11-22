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


def _gabung_skema(target: dict[str, Any], tambahan: dict[str, Any], *, paket: str, lokasi: str = "") -> None:
    """Gabungkan ekstensi secara rekursif, termasuk properti bertingkat, tanpa override diam-diam."""
    for kunci, nilai in tambahan.items():
        jalur = f"{lokasi}.{kunci}" if lokasi else kunci
        if kunci == "properties":
            if not isinstance(nilai, dict):
                raise TypeError(f"skema_tambahan paket {paket!r}: {jalur} harus berupa objek")
            dasar = target.setdefault("properties", {})
            if not isinstance(dasar, dict):
                raise TypeError(f"skema inti {jalur} bukan objek")
            for nama, skema_properti in nilai.items():
                lokasi_properti = f"{jalur}.{nama}"
                if nama not in dasar:
                    dasar[nama] = copy.deepcopy(skema_properti)
                elif isinstance(dasar[nama], dict) and isinstance(skema_properti, dict):
                    _gabung_skema(dasar[nama], skema_properti, paket=paket, lokasi=lokasi_properti)
                else:
                    raise ValueError(
                        f"skema_tambahan paket {paket!r} menimpa properti inti: {lokasi_properti}"
                    )
        elif kunci == "required":
            if not isinstance(nilai, list) or any(not isinstance(n, str) for n in nilai):
                raise TypeError(f"skema_tambahan paket {paket!r}: {jalur} harus berupa daftar nama")
            target[kunci] = list(dict.fromkeys([*target.get(kunci, []), *nilai]))
        elif kunci in target and isinstance(target[kunci], dict) and isinstance(nilai, dict):
            _gabung_skema(target[kunci], nilai, paket=paket, lokasi=jalur)
        elif kunci in target and target[kunci] != nilai:
            jenis = "properti inti" if lokasi.startswith("properties.") or ".properties." in lokasi else "aturan inti"
            raise ValueError(f"skema_tambahan paket {paket!r} menimpa {jenis}: {jalur}")
        else:
            target[kunci] = copy.deepcopy(nilai)


def _skema_paket(paket) -> dict[str, Any]:
    """Gabungkan ekstensi skema paket ke skema inti tanpa mengizinkan override diam-diam."""
    hasil = copy.deepcopy(SKEMA)
    tambahan = dict(paket.skema_tambahan)
    _gabung_skema(hasil, tambahan, paket=paket.nama)
    return hasil


def periksa(rencana: dict, *, final: bool = False) -> list[Temuan]:
    """Periksa skema inti + ekstensi paket, lalu delegasikan aturan domain."""
    from ..genre import dari_rencana

    if not isinstance(rencana, dict):
        # Akar harus objek: kembalikan temuan skema yang terbaca, jangan crash saat memilih paket genre.
        return [Temuan("GAGAL", "SKEMA", f"(akar): rencana harus berupa objek JSON, bukan {type(rencana).__name__}")]
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
