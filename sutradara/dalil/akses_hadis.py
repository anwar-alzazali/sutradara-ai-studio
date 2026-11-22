"""Shim kompatibilitas ke modul paket; identitas modul dipertahankan untuk monkeypatch lama."""
from importlib import import_module as _import_module
import sys as _sys

_modul = _import_module("sutradara.paket_genre.kisah_islami.dalil.akses_hadis")
_sys.modules[__name__] = _modul
