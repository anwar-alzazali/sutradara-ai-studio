"""Registri paket genre; inti hanya mengenal kontrak ini, bukan isi genre."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Callable, Mapping


NamaValidator = Callable[[dict[str, Any]], list[Any]]
NamaRenderer = Callable[..., str]


@dataclass(frozen=True)
class PaketGenre:
    """Kontrak ekstensi genre yang didaftarkan tanpa mengubah modul inti."""

    nama: str
    komponen: Mapping[str, NamaRenderer] = field(default_factory=dict)
    validator: NamaValidator | None = None
    skema_tambahan: Mapping[str, Any] = field(default_factory=dict)


_PAKET: dict[str, PaketGenre] = {}
_POLA_NAMA = re.compile(r"^[a-z][a-z0-9_]*$")


def daftarkan(paket: PaketGenre, *, ganti: bool = False) -> None:
    """Daftarkan satu paket; nama dan kunci komponen harus stabil dan aman."""
    if not isinstance(paket, PaketGenre):
        raise TypeError("paket harus berupa PaketGenre")
    if not _POLA_NAMA.fullmatch(paket.nama):
        raise ValueError(f"nama genre tidak sah: {paket.nama!r}")
    if not paket.komponen and paket.validator is None and not paket.skema_tambahan:
        raise ValueError("paket genre harus menyediakan komponen, validator, atau skema")
    if any(not isinstance(k, str) or not k.strip() for k in paket.komponen):
        raise ValueError("nama komponen harus berupa teks yang tidak kosong")
    if paket.nama in _PAKET and not ganti:
        raise ValueError(f"genre sudah terdaftar: {paket.nama}")
    _PAKET[paket.nama] = paket


def ambil(nama: str) -> PaketGenre:
    """Ambil paket yang telah didaftarkan; tidak pernah memilih paket secara diam-diam."""
    try:
        return _PAKET[nama]
    except KeyError as exc:
        pilihan = ", ".join(sorted(_PAKET)) or "(belum ada)"
        raise ValueError(f"genre tidak dikenal: {nama!r}; tersedia: {pilihan}") from exc


def daftar() -> tuple[str, ...]:
    """Nama genre yang sudah terdaftar, dalam urutan deterministik."""
    return tuple(sorted(_PAKET))


def nama_dari_rencana(rencana: Mapping[str, Any]) -> str:
    """Rencana lama tanpa kolom genre tetap memakai paket Kisah Islami."""
    nama = rencana.get("genre", "kisah_islami")
    if not isinstance(nama, str) or not _POLA_NAMA.fullmatch(nama):
        raise ValueError("kolom genre harus berupa nama paket yang sah")
    return nama
