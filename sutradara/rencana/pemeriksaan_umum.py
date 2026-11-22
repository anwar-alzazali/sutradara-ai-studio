"""Pemeriksaan kontinuitas yang netral terhadap genre.

Modul ini hanya membandingkan identitas stabil pada kartu pemeran dengan atribut
yang dipakai per shot. Aturan cara tokoh ditampilkan tetap menjadi tanggung jawab
paket genre.
"""
from __future__ import annotations

from typing import Any

from .penjaga import Temuan


_KUNCI_IDENTITAS = {
    "jenis": "jenis",
    "usia": "usia",
    "zaman": "zaman",
    "indeks": "indeks",
    "warna_kulit": "warna_kulit",
    "warna_baju": "warna_baju",
    "warna_aksen": "warna_aksen",
    "rambut": "rambut",
    "janggut": "janggut",
    "warna_janggut": "warna_janggut",
    "aksesori": "aksesori",
    "suara": "suara",
    "ciri_wajah": "ciri_wajah",
    "kepala": "penutup_kepala",
}


def periksa_kontinuitas_identitas(rencana: dict[str, Any]) -> list[Temuan]:
    """Tandai pemeran yang tidak terdaftar dan perubahan ciri stabil antar-shot.

    Peran kolektif tidak dibandingkan dengan satu identitas contoh. Individu
    dalam kelompok tetap diaudit melalui pemeran_id yang stabil.
    """
    hasil: list[Temuan] = []
    peta_peran = {p["id"]: p for p in rencana.get("peran", [])}
    kartu_pemeran = {p["id"]: p for p in rencana.get("pemeran", [])}
    kartu = {pid: p.get("identitas", {}) for pid, p in peta_peran.items()}
    kartu.update({pid: p.get("identitas", {}) for pid, p in kartu_pemeran.items()})

    for bi, beat in enumerate(rencana.get("beat", [])):
        for si, shot in enumerate(beat.get("shot", [])):
            for tokoh in shot.get("tokoh", []):
                pid = tokoh.get("pemeran_id") or tokoh.get("peran")
                if tokoh.get("pemeran_id") and pid not in kartu_pemeran:
                    hasil.append(Temuan(
                        "GAGAL",
                        "PEMERAN_TAK_TERDAFTAR",
                        f"beat {bi} shot {si}: pemeran_id {pid!r} tidak memiliki kartu identitas",
                    ))
                    continue

                id_peran = tokoh.get("peran")
                definisi_peran = peta_peran.get(id_peran, {})
                if not tokoh.get("pemeran_id") and definisi_peran.get("kolektif", False):
                    identitas = {}
                else:
                    identitas = kartu.get(pid) or {}
                if not identitas:
                    continue

                beda = [
                    (field, identitas[acuan], tokoh[field])
                    for field, acuan in _KUNCI_IDENTITAS.items()
                    if field in tokoh and acuan in identitas and tokoh[field] != identitas[acuan]
                ]
                if beda:
                    rincian = ", ".join(f"{field}: {lama!r} -> {baru!r}" for field, lama, baru in beda)
                    hasil.append(Temuan(
                        "PERIKSA",
                        "IDENTITAS_BERUBAH",
                        f"beat {bi} shot {si} {pid}: ciri kartu pemeran berubah ({rincian}); "
                        "perbarui kartu hanya bila perubahan memang menjadi desain baru",
                    ))
    return hasil
