from __future__ import annotations

import pytest

from jsonschema import Draft202012Validator

from sutradara.genre import PaketGenre, ambil, daftar, daftarkan, dari_rencana, nama_dari_rencana
from sutradara.rencana.penjaga import SKEMA


def test_rencana_lama_tetap_memilih_kisah_islami():
    assert nama_dari_rencana({}) == "kisah_islami"
    assert nama_dari_rencana({"genre": "kisah_islami"}) == "kisah_islami"


def test_manifest_kisah_islami_dimuat_melalui_registri():
    paket = dari_rencana({})
    assert paket.nama == "kisah_islami"
    assert {"nur.pilar", "malaikat.berkas", "makhluk.kabut_tanpa_wujud", "dajjal.sosok", "akhir_zaman.buraq", "kartu_dalil.kartu"} <= set(paket.komponen)
    assert all(callable(fungsi) for fungsi in paket.komponen.values())
    assert paket.modul_dalil == "sutradara.dalil"
    assert paket.bawaan["bacaan_arab_tts"] is False
    assert paket.bawaan["terjemah_kartu_utuh"] is True


def test_paket_genre_tiruan_dapat_didaftarkan_tanpa_mengubah_inti():
    def gambar_benda_tiruan(*args, **kwargs):
        return '<circle cx="10" cy="10" r="2"/>'

    nama = "genre_tiruan_uji"
    paket = PaketGenre(nama=nama, komponen={"benda:lingkaran": gambar_benda_tiruan})
    daftarkan(paket)
    try:
        assert nama in daftar()
        assert ambil(nama).komponen["benda:lingkaran"]() == '<circle cx="10" cy="10" r="2"/>'
    finally:
        from sutradara import genre
        genre._PAKET.pop(nama, None)


def test_pendaftaran_ganda_ditolak_dan_bisa_diganti_secara_eksplisit():
    nama = "genre_tiruan_ganda_uji"
    pertama = PaketGenre(nama=nama, skema_tambahan={"contoh": {"type": "string"}})
    kedua = PaketGenre(nama=nama, validator=lambda r: [])
    daftarkan(pertama)
    try:
        with pytest.raises(ValueError, match="sudah terdaftar"):
            daftarkan(kedua)
        daftarkan(kedua, ganti=True)
        assert ambil(nama) is kedua
    finally:
        from sutradara import genre
        genre._PAKET.pop(nama, None)


@pytest.mark.parametrize("nama", ["", "../keluar", "Kisah Islami", "a-b"])
def test_nama_genre_tidak_boleh_mengandung_path_atau_spasi(nama):
    with pytest.raises(ValueError, match="nama genre"):
        daftarkan(PaketGenre(nama=nama, komponen={"x": lambda: ""}))


def test_genre_tidak_dikenal_ditolak_dengan_pesan_yang_jelas():
    with pytest.raises(ValueError, match="genre tidak dikenal"):
        ambil("genre_yang_tidak_ada")


def test_kontrak_paket_tidak_bisa_diubah_setelah_dibuat():
    fungsi = lambda: "<g/>"
    komponen = {"benda:uji": fungsi}
    bawaan = {"mode": "aman"}
    paket = PaketGenre(nama="genre_terkunci_uji", komponen=komponen, bawaan=bawaan)
    # Mutasi sumber setelah konstruksi tidak boleh mengubah manifest.
    komponen["benda:baru"] = fungsi
    bawaan["mode"] = "berubah"
    assert set(paket.komponen) == {"benda:uji"}
    assert paket.bawaan["mode"] == "aman"
    with pytest.raises(TypeError):
        paket.komponen["benda:baru"] = fungsi
    with pytest.raises(TypeError):
        paket.bawaan["mode"] = "berubah"


def test_skema_menerima_genre_opsional_dengan_nama_paket_generik():
    validator = Draft202012Validator(SKEMA)
    # Rencana lama tanpa genre tetap sah; nama genre baru tidak dikunci ke daftar Kisah Islami.
    assert validator.is_valid({"genre": "genre_tiruan_uji"}) is False  # properti lain tetap wajib
    assert "genre" not in SKEMA["required"]
    assert SKEMA["properties"]["genre"]["pattern"] == "^[a-z][a-z0-9_]*$"
