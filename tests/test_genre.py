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


def test_paket_kisah_islami_mendaftarkan_hook_waktu_baca_dan_efek():
    paket = dari_rencana({})
    shot = {"kartu_dalil": {"mulai": 0.7}}
    assert paket.sisipan_waktu_baca(shot)
    assert paket.waktu_tetap(shot, "kartu_dalil")
    assert paket.efek_kemunculan(shot) == [
        {"berkas": "kilau_cahaya", "offset": 0.7, "vol": 0.35}
    ]


def test_inti_waktu_dan_suara_tidak_menyebut_elemen_kisah_islami():
    akar = Path(__file__).resolve().parents[1] / "sutradara"
    for rel in ("garis_waktu.py", "suara/campur.py"):
        sumber = (akar / rel).read_text(encoding="utf-8")
        assert "kartu_dalil" not in sumber
        assert "kilau_cahaya" not in sumber


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


def test_paket_dapat_didaftarkan_hanya_dengan_hook_generik():
    from sutradara import genre

    nama = "genre_hook_saja_uji"
    paket = PaketGenre(nama=nama, sisipan_waktu_baca=lambda shot: bool(shot.get("baca")))
    daftarkan(paket)
    try:
        assert ambil(nama) is paket
    finally:
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



def test_gerak_aksi_hanya_diberikan_kepada_pelaku():
    from sutradara.paket_genre.kisah_islami.sutradara import rancang

    naskah = {
        "judul": "Pembangunan bahtera",
        "inti": "bahtera",
        "beat": [{
            "narasi": "Pengikut beriman membangun bahtera; kaum penentang berdiri di seberang.",
            "peran": ["pengikut beriman", "kaum penentang"],
        }],
    }
    rencana, _ = rancang(naskah)
    aktor = rencana["beat"][0]["shot"][0]["tokoh"]
    gerak = {a["peran"]: a["gerak"] for a in aktor}
    assert gerak["pengikut_beriman"] == "palu"
    assert gerak["kaum_penentang"] == "berdiri"


def test_dialog_menggunakan_shot_reverse_shot_dekat_dengan_kamera_mengikuti_pembicara():
    from sutradara.paket_genre.kisah_islami.sutradara import rancang

    naskah = {
        "judul": "Seruan Nabi Nuh",
        "beat": [{
            "narasi": "Nabi Nuh menyeru seorang penentang, lalu penentang itu menjawab.",
            "peran": ["Nabi Nuh", "penentang"],
            "dialog": [{"pembicara": "Nabi Nuh", "penjawab": "penentang", "ucapan": "Dengarkan seruanku."}],
        }],
    }
    rencana, _ = rancang(naskah)
    shots = rencana["beat"][0]["shot"]
    assert len(shots) == 2
    assert [shot["kamera"]["x"] for shot in shots] == [380, 820]
    assert all(shot["kamera"]["zoom"] == 2.45 for shot in shots)
    assert all(shot["kamera"]["y"] == 1330 for shot in shots)


def test_pengejar_dan_yang_dikejar_bergerak_searah():
    from sutradara.paket_genre.kisah_islami.sutradara import rancang

    naskah = {
        "judul": "Pengejaran",
        "beat": [{
            "narasi": "Penjaga mengejar pengelana ke kanan.",
            "peran": ["penjaga", "pengelana"],
        }],
    }
    rencana, _ = rancang(naskah)
    tokoh = rencana["beat"][0]["shot"][0]["tokoh"]
    lintasan = {a["peran"]: a["lintasan"] for a in tokoh}
    tujuan = {a["peran"]: a["tujuan"] for a in tokoh}
    arah = {
        pid: (lintasan[pid][-1][1] > lintasan[pid][0][1]) -
             (lintasan[pid][-1][1] < lintasan[pid][0][1])
        for pid in lintasan
    }
    assert arah == {"penjaga": 1, "pengelana": 1}
    assert tujuan == {"penjaga": "tepi:kanan", "pengelana": "tepi:kanan"}



def test_dialog_menyisipkan_reaksi_pendengar_yang_disebut_eksplisit():
    from sutradara.paket_genre.kisah_islami.sutradara import rancang

    naskah = {
        "judul": "Seruan dan jawaban",
        "beat": [{
            "narasi": "Nabi Nuh menyeru seorang penentang; penentang itu terkejut lalu menjawab.",
            "peran": ["Nabi Nuh", "penentang"],
            "dialog": [{
                "pembicara": "Nabi Nuh",
                "penjawab": "penentang",
                "ucapan": "Dengarkan seruanku.",
            }],
        }],
    }
    rencana, _ = rancang(naskah)
    shots = rencana["beat"][0]["shot"]
    # Pembicara -> reaksi pendengar -> giliran penjawab.
    assert len(shots) == 3
    reaksi = shots[1]
    assert reaksi["kamera"]["x"] == 820
    pendengar = next(a for a in reaksi["tokoh"] if a["peran"] == "penentang")
    assert pendengar["wajah"] == "kaget"
    assert pendengar["gerak"] == "kaget"
    assert "bicara" not in pendengar


def test_pengejaran_ke_kiri_menggerakkan_kedua_tokoh_searah_dengan_margin():
    from sutradara.paket_genre.kisah_islami.sutradara import rancang

    naskah = {
        "judul": "Pengejaran ke kiri",
        "beat": [{
            "narasi": "Penjaga mengejar pengelana ke kiri.",
            "peran": ["penjaga", "pengelana"],
        }],
    }
    rencana, _ = rancang(naskah)
    tokoh = {a["peran"]: a for a in rencana["beat"][0]["shot"][0]["tokoh"]}
    for pid in ("penjaga", "pengelana"):
        lintasan = tokoh[pid]["lintasan"]
        assert lintasan[0][1] > lintasan[-1][1]
        assert lintasan[-1][1] >= 200
        assert tokoh[pid]["tujuan"] == "tepi:kiri"
        assert tokoh[pid]["gerak"] == "lari"


def test_cadence_jalan_dihitung_dari_kecepatan_lintasan():
    from sutradara.paket_genre.kisah_islami.sutradara import rancang

    naskah = {
        "judul": "Perjalanan",
        "beat": [{
            "narasi": "Pengelana berjalan menuju tepi kanan.",
            "peran": ["Pengelana"],
        }],
    }
    rencana, _ = rancang(naskah)
    aktor = rencana["beat"][0]["shot"][0]["tokoh"][0]
    lintasan = aktor["lintasan"]
    jarak = ((lintasan[-1][1] - lintasan[0][1]) ** 2 +
             (lintasan[-1][2] - lintasan[0][2]) ** 2) ** 0.5
    durasi = lintasan[-1][0] - lintasan[0][0]
    assert aktor["faktor_gerak"] == pytest.approx(round(max(.45, min(2.5, (jarak / durasi) / 74.0)), 3))
    assert aktor["faktor_gerak"] > 0
