"""Penghubung netral dari naskah antrean ke sutradara yang didaftarkan paket genre."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from . import genre
from .antrean import validasi as validasi_naskah
from .rencana import periksa


def rancang(naskah: dict, *, gunakan_model: bool | None = None,
            model: Callable[[dict, dict], tuple[dict, dict]] | None = None,
            biaya_ke: Path | None = None) -> dict:
    """Rancang rencana dengan aturan lokal; model hanya dipanggil bila diaktifkan dan paket ragu.

    Adapter model menerima (naskah, kandidat) dan mengembalikan (rencana, biaya),
    sehingga tes dan pemakaian bawaan tidak pernah membuat panggilan jaringan.
    """
    salah = validasi_naskah(naskah)
    if salah:
        raise ValueError("naskah tidak sah:\n- " + "\n- ".join(salah))
    paket = genre.ambil(naskah.get("genre", genre.GENRE_BAWAAN))
    if paket.sutradara is None:
        raise ValueError(f"paket genre {paket.nama!r} belum menyediakan sutradara")
    kandidat, yakin = paket.sutradara(naskah)
    aktif = (os.environ.get("SUTRADARA_AI_AKTIF", "").strip().lower() in {"1", "true", "ya"}
             if gunakan_model is None else gunakan_model)
    if aktif and yakin < 0.7:
        if model is None:
            raise RuntimeError("aturan sutradara ragu dan SUTRADARA_AI_AKTIF menyala, tetapi adapter model tidak tersedia")
        kandidat, biaya = model(naskah, kandidat)
        _catat_biaya(kandidat, biaya, biaya_ke)
    kandidat["dibuat_otomatis"] = True
    temuan = periksa(kandidat)
    gagal = [str(t) for t in temuan if t.tingkat == "GAGAL"]
    if gagal:
        raise ValueError("rencana hasil sutradara belum lolos penjaga:\n- " + "\n- ".join(gagal))
    return kandidat


def _catat_biaya(rencana: dict, biaya: dict, tujuan: Path | None) -> None:
    """Catat pemakaian model tanpa menyimpan kunci atau isi prompt."""
    if tujuan is None:
        tujuan = Path("data/biaya/sutradara.jsonl")
    tujuan = Path(tujuan)
    tujuan.parent.mkdir(parents=True, exist_ok=True)
    catatan = {
        "waktu": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "judul": rencana.get("judul", ""),
        "penyedia": str(biaya.get("penyedia", "tidak_diketahui")),
        "model": str(biaya.get("model", "tidak_diketahui")),
        "input_token": int(biaya.get("input_token", 0)),
        "output_token": int(biaya.get("output_token", 0)),
        "biaya_usd": float(biaya.get("biaya_usd", 0.0)),
    }
    with tujuan.open("a", encoding="utf-8") as f:
        f.write(json.dumps(catatan, ensure_ascii=False) + "\n")
