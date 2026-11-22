"""Kontrak netral dan pemuat paket genre."""
from __future__ import annotations
from dataclasses import dataclass, field
from importlib import import_module
import re
from threading import RLock
from types import MappingProxyType
from typing import Any, Callable, Mapping
GENRE_BAWAAN="kisah_islami"
@dataclass(frozen=True)
class HasilAdegan:
    """Lapisan hasil render generik."""
    latar: tuple[str,...]=()
    tengah: tuple[tuple[float,str],...]=()
    overlay: tuple[str,...]=()
    barang_pemilik: Mapping[str,tuple[dict[str,Any],...]]=field(default_factory=dict)
    target_tangan: Mapping[str,Mapping[str,tuple[float,float]]]=field(default_factory=dict)
    overlay_ui: tuple[str,...]=()
    sembunyikan_judul: bool=False
@dataclass(frozen=True)
class PaketGenre:
    nama: str
    komponen: Mapping[str,Callable[...,str]]=field(default_factory=dict)
    renderer_adegan: Callable[...,HasilAdegan]|None=None
    adaptasi_shot: Callable[[dict[str,Any],dict[str,Any]],dict[str,Any]]|None=None
    durasi_shot: Callable[[dict[str,Any],dict[str,Any]],float|None]|None=None
    data_render: Callable[[dict[str,Any]],dict[str,Any]]|None=None
    validator: Callable[...,list[Any]]|None=None
    skema_tambahan: Mapping[str,Any]=field(default_factory=dict)
    modul_dalil: str|None=None
    panduan_gaya: str|None=None
    resep: str|None=None
    bawaan: Mapping[str,Any]=field(default_factory=dict)
    sisipan_waktu_baca: Callable[[dict[str,Any]],bool]|None=None
    waktu_tetap: Callable[[dict[str,Any],str],bool]|None=None
    efek_kemunculan: Callable[[dict[str,Any]],list[dict[str,Any]]]|None=None
    def __post_init__(self):
        object.__setattr__(self,"komponen",MappingProxyType(dict(self.komponen)))
        object.__setattr__(self,"skema_tambahan",MappingProxyType(dict(self.skema_tambahan)))
        object.__setattr__(self,"bawaan",MappingProxyType(dict(self.bawaan)))
_PAKET={}; _POLA_NAMA=re.compile(r"^[a-z][a-z0-9_]*$"); _KUNCI=RLock()
def daftarkan(paket,*,ganti=False):
    if not isinstance(paket,PaketGenre): raise TypeError("paket harus berupa PaketGenre")
    if not isinstance(paket.nama,str) or not _POLA_NAMA.fullmatch(paket.nama): raise ValueError(f"nama genre tidak sah: {paket.nama!r}")
    if not any((paket.komponen,paket.renderer_adegan,paket.adaptasi_shot,paket.durasi_shot,paket.data_render,paket.validator,paket.skema_tambahan,paket.modul_dalil,paket.panduan_gaya,paket.resep,paket.bawaan)): raise ValueError("paket genre harus menyediakan minimal satu kemampuan")
    if any(not isinstance(k,str) or not k.strip() for k in paket.komponen): raise ValueError("nama komponen harus berupa teks yang tidak kosong")
    with _KUNCI:
        if paket.nama in _PAKET and not ganti: raise ValueError(f"genre sudah terdaftar: {paket.nama}")
        _PAKET[paket.nama]=paket
def ambil(nama=None):
    nama=GENRE_BAWAAN if nama is None else nama
    if not isinstance(nama,str) or not _POLA_NAMA.fullmatch(nama): raise ValueError("nama genre harus berupa nama paket yang sah")
    with _KUNCI:
        paket=_PAKET.get(nama)
        if paket is not None: return paket
        try: modul=import_module(f"sutradara.paket_genre.{nama}")
        except ModuleNotFoundError as exc:
            if exc.name!=f"sutradara.paket_genre.{nama}": raise
            pilihan=", ".join(sorted(_PAKET)) or "(belum ada)"
            raise ValueError(f"genre tidak dikenal: {nama!r}; tersedia: {pilihan}") from exc
        pembuat=getattr(modul,"buat_paket",None)
        if not callable(pembuat): raise TypeError(f"modul genre {nama!r} tidak menyediakan buat_paket()")
        paket=pembuat()
        if not isinstance(paket,PaketGenre) or paket.nama!=nama: raise ValueError(f"manifest genre {nama!r} harus mengembalikan PaketGenre dengan nama yang sama")
        daftarkan(paket); return paket
def daftar():
    with _KUNCI: return tuple(sorted(_PAKET))
def nama_dari_rencana(rencana):
    nama=rencana.get("genre",GENRE_BAWAAN)
    if not isinstance(nama,str) or not _POLA_NAMA.fullmatch(nama): raise ValueError("kolom genre harus berupa nama paket yang sah")
    return nama
def dari_rencana(rencana): return ambil(nama_dari_rencana(rencana))
