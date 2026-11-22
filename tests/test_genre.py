from __future__ import annotations

import json
from pathlib import Path

import pytest

from jsonschema import Draft202012Validator

from sutradara.genre import PaketGenre, ambil, daftar, daftarkan, dari_rencana, nama_dari_rencana
from sutradara.rencana.penjaga import _skema_paket


def _rencana_tanpa_dalil():
    contoh = Path(__file__).resolve().parents[1] / "contoh" / "nuh_mengejek.json"
    rencana = json.loads(contoh.read_text(encoding="utf-8"))
    rencana.pop("dalil", None)
    for beat in rencana.get("beat", []):
        beat.pop("dalil", None)
    return rencana


def test_rencana_lama_tetap_memilih_kisah_islami():
    assert nama_dari_rencana({}) == "kisah_islami"
    assert nama_dari_rencana({"genre": "kisah_islami"}) == "kisah_islami"


def test_manifest_kisah_islami_dimuat_melalui_registri():
    paket = dari_rencana({})
    assert paket.nama == "kisah_islami"
    assert {"nur.pilar", "malaikat.berkas", "makhluk.kabut_tanpa_wujud", "dajjal.sosok", "akhir_zaman.buraq", "kartu_dalil.kartu"} <= set(paket.komponen)
    assert all(callable(fungsi) for fungsi in paket.komponen.values())
    assert paket.modul_dalil == "sutradara.paket_genre.kisah_islami.dalil"
    assert paket.renderer_adegan is not None and paket.adaptasi_shot is not None
    assert paket.durasi_shot is not None and paket.data_render is not None
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


def test_skema_tambahan_tidak_bisa_diubah_secara_tidak_langsung():
    skema = {
        "properties": {
            "muatan": {
                "type": "object",
                "required": ["kode"],
                "properties": {"kode": {"type": "string"}},
            }
        }
    }
    paket = PaketGenre(nama="genre_skema_terkunci_uji", skema_tambahan=skema)

    # Perubahan ke manifest asal atau objek bersarang yang terlihat tidak boleh mengubah kontrak.
    skema["properties"]["muatan"]["properties"]["kode"]["type"] = "integer"
    with pytest.raises(TypeError):
        paket.skema_tambahan["properties"]["muatan"]["properties"]["kode"]["type"] = "integer"
    with pytest.raises(TypeError):
        paket.skema_tambahan["properties"]["muatan"]["required"][0] = "lain"

    skema_efektif = _skema_paket(paket)
    assert skema_efektif["properties"]["muatan"]["properties"]["kode"]["type"] == "string"
    validator = Draft202012Validator(skema_efektif)
    rencana = _rencana_tanpa_dalil()
    rencana["muatan"] = {"kode": "teks"}
    assert validator.is_valid(rencana)
    rencana["muatan"] = {"kode": 123}
    assert not validator.is_valid(rencana)


def test_skema_menerima_genre_opsional_dengan_nama_paket_generik():
    validator = Draft202012Validator(_skema_paket(dari_rencana({})))
    contoh = Path(__file__).resolve().parents[1] / "contoh" / "nuh_mengejek.json"
    rencana_lama = json.loads(contoh.read_text(encoding="utf-8"))
    assert validator.is_valid(rencana_lama)
    rencana_baru = {**rencana_lama, "genre": "genre_tiruan_uji"}
    assert validator.is_valid(rencana_baru)
    assert "genre" not in _skema_paket(dari_rencana({}))["required"]
    assert _skema_paket(dari_rencana({}))["properties"]["genre"]["pattern"] == "^[a-z][a-z0-9_]*$"
    assert not validator.is_valid({**rencana_lama, "genre": "Nama Genre"})



def test_penjaga_mendelegasikan_validasi_ke_paket_genre():
    from sutradara.rencana.penjaga import periksa
    from sutradara import genre

    nama = "genre_tiruan_validator_uji"
    dipanggil = []

    def validator(rencana, *, final=False):
        dipanggil.append((rencana["genre"], final))
        from sutradara.rencana.penjaga import Temuan
        return [Temuan("PERIKSA", "VALIDATOR_TIRUAN", "validator paket dipanggil")]

    daftarkan(PaketGenre(nama=nama, validator=validator))
    try:
        rencana = _rencana_tanpa_dalil()
        rencana["genre"] = nama
        temuan = periksa(rencana, final=True)
        assert dipanggil == [(nama, True)]
        assert [x.kode for x in temuan] == ["VALIDATOR_TIRUAN"]
    finally:
        genre._PAKET.pop(nama, None)


def test_renderer_paket_tiruan_menyumbang_elemen_tanpa_mengubah_inti():
    from sutradara import genre
    from sutradara.adegan import susun
    from sutradara.genre import HasilAdegan
    nama="genre_renderer_tiruan_uji"; dipanggil=[]
    def renderer(shot,hasil_evaluasi,waktu_lokal,waktu_global,data):
        dipanggil.append((waktu_lokal,waktu_global,data))
        return HasilAdegan(tengah=((hasil_evaluasi["tanah_y"],'<circle id="elemen-genre-tiruan" cx="540" cy="900" r="12"/>'),))
    daftarkan(PaketGenre(nama=nama,renderer_adegan=renderer))
    try:
        svg=susun({"preset":"senja","durasi":2,"tanah_y":1250},t=.5,tg=3.5,genre=nama)
        assert dipanggil==[(.5,3.5,{})] and 'id="elemen-genre-tiruan"' in svg
    finally: genre._PAKET.pop(nama,None)


def test_skema_tambahan_paket_digabung_dan_ditegakkan_penjaga():
    from sutradara.rencana.penjaga import periksa
    from sutradara import genre

    nama = "genre_skema_tiruan_uji"
    paket = PaketGenre(
        nama=nama,
        skema_tambahan={
            "properties": {
                "muatan_genre": {
                    "type": "object",
                    "required": ["kode"],
                    "additionalProperties": False,
                    "properties": {"kode": {"type": "string", "minLength": 2}},
                }
            },
            "required": ["muatan_genre"],
        },
    )
    daftarkan(paket)
    try:
        dasar = _rencana_tanpa_dalil()
        dasar["genre"] = nama

        sah = {**dasar, "muatan_genre": {"kode": "ok"}}
        assert periksa(sah) == []

        tanpa_muatan = periksa(dasar)
        assert any(t.kode == "SKEMA" and "muatan_genre" in t.pesan for t in tanpa_muatan)

        tipe_salah = periksa({**dasar, "muatan_genre": {"kode": 12}})
        assert any(t.kode == "SKEMA" for t in tipe_salah)
    finally:
        genre._PAKET.pop(nama, None)


def test_skema_tambahan_tidak_boleh_menimpa_properti_inti():
    from sutradara.rencana.penjaga import _skema_paket

    paket = PaketGenre(
        nama="genre_skema_bentrok_uji",
        skema_tambahan={"properties": {"judul": {"type": "integer"}}},
    )
    with pytest.raises(ValueError, match="menimpa properti inti"):
        _skema_paket(paket)


def test_renderer_inti_tidak_menyebut_elemen_khusus_genre():
    sumber=(Path(__file__).resolve().parents[1]/"sutradara"/"adegan.py").read_text(encoding="utf-8")
    for nama in ("nur","dajjal","buraq","kabut_tanpa_wujud","kartu_dalil","dalil"): assert nama not in sumber



def test_skema_dalil_hanya_dimiliki_paket_kisah_islami():
    from sutradara.rencana.penjaga import SKEMA

    assert "dalil" not in SKEMA["required"]
    assert "dalil" not in SKEMA["properties"]
    assert "dalil" not in SKEMA["properties"]["beat"]["items"]["properties"]

    islami = _skema_paket(dari_rencana({}))
    assert "dalil" in islami["required"]
    assert "dalil" in islami["properties"]
    assert "dalil" in islami["properties"]["beat"]["items"]["properties"]

    paket_tiruan = PaketGenre(nama="genre_tanpa_dalil_uji", komponen={"lingkaran": lambda: "<circle/>"})
    netral = _skema_paket(paket_tiruan)
    assert "dalil" not in netral["required"]
    assert "dalil" not in netral["properties"]
    assert "dalil" not in netral["properties"]["beat"]["items"]["properties"]


def test_akar_bukan_objek_jadi_temuan_skema_bukan_crash():
    from sutradara.rencana.penjaga import periksa
    for nilai in ([1, 2], "teks", 3, None):
        temuan = periksa(nilai)
        assert [t.kode for t in temuan] == ["SKEMA"], nilai
        assert temuan[0].tingkat == "GAGAL"
