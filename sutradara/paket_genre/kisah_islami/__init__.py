"""Paket Kisah Islami.

Modul ini menjadi manifest pemilik aturan, dalil, gaya, resep, dan bawaan genre.
Pemindahan implementasi dari modul lama dilakukan bertahap tanpa mengubah hasil render.
"""

from sutradara.genre import PaketGenre


def buat_paket() -> PaketGenre:
    """Bangun kontrak genre; jalur modul dipertahankan eksplisit untuk audit."""
    from sutradara.gaya import akhir_zaman, benda, dajjal, kartu, malaikat, makhluk, nur

    return PaketGenre(
        nama="kisah_islami",
        komponen={
            "akhir_zaman": akhir_zaman,
            "benda_kisah": benda,
            "dajjal": dajjal,
            "kartu_dalil": kartu,
            "malaikat": malaikat,
            "makhluk": makhluk,
            "nur": nur,
        },
        modul_dalil="sutradara.dalil",
        panduan_gaya="docs/PANDUAN_GAYA.md",
        resep="docs/RESEP_SUTRADARA.md",
        bawaan={
            "genre_lama": "kisah_islami",
            "bacaan_arab_tts": False,
            "terjemah_kartu_utuh": True,
        },
    )
