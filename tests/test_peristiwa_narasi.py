from sutradara.paket_genre.kisah_islami.peristiwa import analisis_peristiwa, aksi_utama


def test_peristiwa_mengikat_aksi_ke_objek_yang_disebut_naskah():
    hasil = analisis_peristiwa("Tanah di atasmu terbelah.", ["kamu"], 2)

    assert len(hasil) == 1
    assert hasil[0]["aksi"] == "terbelah"
    assert hasil[0]["sasaran"] == "bumi"
    assert hasil[0]["perubahan_keadaan"] == {"objek": "bumi", "keadaan": "terbelah"}
    assert hasil[0]["bukti_narasi"] == "terbelah"
    assert hasil[0]["aktor"] == ["kamu"]


def test_peristiwa_mengenali_gerak_dan_tujuan_objek():
    hasil = analisis_peristiwa("Kamu berjalan menuju matahari.", ["kamu"])

    assert aksi_utama(hasil) == "jalan"
    assert hasil[0]["sasaran"] == "matahari"
    assert hasil[0]["perubahan_keadaan"] is None


def test_peristiwa_tidak_mengubah_keadaan_karena_urutan_beat():
    hasil = analisis_peristiwa("Kamu melihat bahtera yang masih utuh.", ["kamu"], 8)

    assert hasil == []


def test_peristiwa_mengabaikan_aksi_yang_dinegasikan():
    hasil = analisis_peristiwa("Matahari tidak didekatkan kepadamu.", ["kamu"])

    assert hasil == []


def test_peristiwa_tanpa_pola_tidak_mengarang_aksi():
    hasil = analisis_peristiwa("Kamu menyaksikan padang yang sangat luas.", ["kamu"])

    assert aksi_utama(hasil) is None
    assert hasil == []
