from sutradara.paket_genre.kisah_islami.peristiwa import analisis_peristiwa, aksi_utama


def test_peristiwa_pasif_mengikat_pasien_tanpa_mengarang_pelaku():
    hasil = analisis_peristiwa("Tanah di atasmu terbelah.", ["kamu"], 2)
    assert len(hasil) == 1
    assert hasil[0]["aksi"] == "terbelah"
    assert hasil[0]["sasaran"] == "bumi"
    assert hasil[0]["perubahan_keadaan"] == {"objek": "bumi", "keadaan": "terbelah"}
    assert hasil[0]["bukti_narasi"] == "terbelah"
    assert hasil[0]["aktor"] == []


def test_perjalanan_membedakan_tujuan_dari_pasien():
    hasil = analisis_peristiwa("Kamu berjalan menuju matahari.", ["kamu"])
    assert aksi_utama(hasil) == "jalan"
    assert hasil[0]["sasaran"] is None
    assert hasil[0]["tujuan"] == "matahari"
    assert hasil[0]["aktor"] == ["kamu"]


def test_peristiwa_tidak_mengubah_keadaan_karena_urutan_beat():
    assert analisis_peristiwa("Kamu melihat bahtera yang masih utuh.", ["kamu"], 8) == []


def test_peristiwa_mengabaikan_aksi_yang_dinegasikan():
    assert analisis_peristiwa("Matahari tidak didekatkan kepadamu.", ["kamu"]) == []


def test_peristiwa_tanpa_pola_tidak_mengarang_aksi():
    hasil = analisis_peristiwa("Kamu menyaksikan padang yang sangat luas.", ["kamu"])
    assert aksi_utama(hasil) is None
    assert hasil == []


def test_peran_yang_hanya_hadir_bukan_pelaku():
    hasil = analisis_peristiwa(
        "Pengikut beriman membangun bahtera; kaum penentang berdiri di seberang.",
        ["pengikut beriman", "kaum penentang"],
    )
    bangun = next(x for x in hasil if x["aksi"] == "membangun")
    assert bangun["aktor"] == ["pengikut beriman"]


def test_negasi_tidak_bocor_ke_klausa_berikutnya():
    hasil = analisis_peristiwa("Matahari tidak mendekat. Kerumunan berkumpul.", ["kamu"])
    assert [x["aksi"] for x in hasil] == ["berkumpul"]


def test_pasien_dipilih_dari_frasa_sebelum_aksi():
    hasil = analisis_peristiwa("Dinding itu runtuh setelah digali.", [])
    assert hasil[0]["sasaran"] == "dinding"
    assert hasil[0]["perubahan_keadaan"] == {"objek": "dinding", "keadaan": "runtuh"}
