"""Kontrak dan pemuat paket genre; inti hanya bergantung pada antarmuka ini."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
import re
from threading import RLock
from types import MappingProxyType
from typing import Any, Callable, Mapping

NamaValidator = Callable[[dict[str, Any]], list[Any]]
NamaRenderer = Callable[..., str]
RendererAdegan = Callable[[dict[str, Any], dict[str, Any], float, float], list[tuple[float, str]]]

@dataclass(frozen=True)
class PaketGenre:
    """Kontrak ekstensi. Referensi modul genre disimpan di paket, bukan di inti."""

    nama: str
    komponen: Mapping[str, NamaRenderer] = field(default_factory=dict)
    renderer_adegan: RendererAdegan | None = None
    validator: NamaValidator | None = None
    skema_tambahan: Mapping[str, Any] = field(default_factory=dict)
    modul_dalil: str | None = None
    panduan_gaya: str | None = None
    resep: str | None = None
    bawaan: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # frozen=True tidak membekukan dict di dalam dataclass; salin agar pemanggil
        # tidak dapat mengubah kontrak paket setelah paket didaftarkan.
        object.__setattr__(self, "komponen", MappingProxyType(dict(self.komponen)))
        object.__setattr__(self, "skema_tambahan", MappingProxyType(dict(self.skema_tambahan)))
        object.__setattr__(self, "bawaan", MappingProxyType(dict(self.bawaan)))

_PAKET: dict[str, PaketGenre] = {}
_POLA_NAMA = re.compile(r"^[a-z][a-z0-9_]*$")
_KUNCI = RLock()

def daftarkan(paket: PaketGenre, *, ganti: bool = False) -> None:
    """Daftarkan paket secara eksplisit; pendaftaran ganda ditolak secara default."""
    if not isinstance(paket, PaketGenre):
        raise TypeError("paket harus berupa PaketGenre")
    if not isinstance(paket.nama, str) or not _POLA_NAMA.fullmatch(paket.nama):
        raise ValueError(f"nama genre tidak sah: {paket.nama!r}")
    if not (paket.komponen or paket.renderer_adegan or paket.validator or paket.skema_tambahan or paket.modul_dalil
            or paket.panduan_gaya or paket.resep or paket.bawaan):
        raise ValueError("paket genre harus menyediakan minimal satu kemampuan")
    if any(not isinstance(k, str) or not k.strip() for k in paket.komponen):
        raise ValueError("nama komponen harus berupa teks yang tidak kosong")
    with _KUNCI:
        if paket.nama in _PAKET and not ganti:
            raise ValueError(f"genre sudah terdaftar: {paket.nama}")
        _PAKET[paket.nama] = paket

def ambil(nama: str) -> PaketGenre:
    """Ambil paket terdaftar atau muat modul paket berdasarkan nama tervalidasi.

    Kunci dipertahankan selama pemuatan agar dua thread yang pertama kali meminta
    genre yang sama tidak berlomba mendaftarkan manifest yang sama.
    """
    if not isinstance(nama, str) or not _POLA_NAMA.fullmatch(nama):
        raise ValueError("nama genre harus berupa nama paket yang sah")
    with _KUNCI:
        paket = _PAKET.get(nama)
        if paket is not None:
            return paket
        try:
            modul = import_module(f"sutradara.paket_genre.{nama}")
        except ModuleNotFoundError as exc:
            # Jangan menyamarkan ModuleNotFoundError dari dependensi internal paket.
            if exc.name != f"sutradara.paket_genre.{nama}":
                raise
            pilihan = ", ".join(sorted(_PAKET)) or "(belum ada)"
            raise ValueError(f"genre tidak dikenal: {nama!r}; tersedia: {pilihan}") from exc
        pembuat = getattr(modul, "buat_paket", None)
        if not callable(pembuat):
            raise TypeError(f"modul genre {nama!r} tidak menyediakan buat_paket()")
        paket = pembuat()
        if not isinstance(paket, PaketGenre) or paket.nama != nama:
            raise ValueError(f"manifest genre {nama!r} harus mengembalikan PaketGenre dengan nama yang sama")
        daftarkan(paket)
        return paket



def daftar() -> tuple[str, ...]:
    """Nama genre yang sudah terdaftar, dalam urutan deterministik."""
    with _KUNCI:
        return tuple(sorted(_PAKET))


def nama_dari_rencana(rencana: Mapping[str, Any]) -> str:
    """Rencana lama tanpa kolom genre tetap memakai paket Kisah Islami."""
    nama = rencana.get("genre", "kisah_islami")
    if not isinstance(nama, str) or not _POLA_NAMA.fullmatch(nama):
        raise ValueError("kolom genre harus berupa nama paket yang sah")
    return nama


def dari_rencana(rencana: Mapping[str, Any]) -> PaketGenre:
    """Resolusi satu pintu untuk rencana baru maupun rencana lama."""
    return ambil(nama_dari_rencana(rencana))
