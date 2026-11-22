"""Paket Kisah Islami.

Manifest ini menjadi pemilik komponen khas genre. Implementasi lama masih dipertahankan
sementara sebagai sumber kompatibilitas; pemindahan fisiknya dilakukan bersama adaptasi impor.
"""

from sutradara.genre import PaketGenre


def buat_paket() -> PaketGenre:
    """Bangun kontrak genre dengan fungsi render, bukan modul sebagai nilai."""
    from sutradara.gaya import akhir_zaman, benda, dajjal, kartu, malaikat, makhluk, nur

    return PaketGenre(
        nama="kisah_islami",
        komponen={
            "nur.pilar": nur.pilar,
            "malaikat.berkas": malaikat.berkas,
            "makhluk.kabut_tanpa_wujud": makhluk.kabut_tanpa_wujud,
            "makhluk.retakan": makhluk.retakan,
            "dajjal.sosok": dajjal.sosok,
            "dajjal.belakang": dajjal.belakang,
            "akhir_zaman.buraq": akhir_zaman.buraq,
            "akhir_zaman.dinding_yajuj": akhir_zaman.dinding_yajuj,
            "akhir_zaman.danau_surut": akhir_zaman.danau_surut,
            "akhir_zaman.tanda_wajah": akhir_zaman.tanda_wajah,
            "benda.bahtera": benda.bahtera,
            "benda.sungai": benda.sungai,
            "kartu_dalil.kartu": kartu.kartu,
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
