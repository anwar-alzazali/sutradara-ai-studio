"""Regresi khusus uji audio nyata D2; seluruh tes memakai data tiruan tanpa API."""
import pytest

from scripts.uji_audio_nyata_d2 import periksa_alignment_sumber


def test_ekor_alignment_diisi_hening_bukan_dianggap_audio_hilang():
    data = {"beat": [[[0.0, 1.0, "awal"], [13.0, 13.60, "akhir"]]]}
    potongan = [{"a0": 0.0, "a1": 13.95, "di": 0.35}]

    padding = periksa_alignment_sumber(data, 13.52, potongan)

    assert padding == pytest.approx(0.43)


def test_kata_yang_benar_benar_melewati_audio_tetap_ditolak():
    data = {"beat": [[[0.0, 1.0, "awal"], [13.0, 13.68, "akhir"]]]}
    potongan = [{"a0": 0.0, "a1": 14.03, "di": 0.35}]

    with pytest.raises(AssertionError, match="alignment kata melewati"):
        periksa_alignment_sumber(data, 13.52, potongan)


def test_tidak_menambah_hening_bila_semua_potongan_muatt():
    data = {"beat": [[[0.0, 1.0, "awal"], [12.0, 12.5, "akhir"]]]}
    potongan = [{"a0": 0.0, "a1": 12.85, "di": 0.35}]

    assert periksa_alignment_sumber(data, 13.52, potongan) == 0.0
