from sutradara.rencana.pemeriksaan_umum import periksa_kedekatan_pelaku


def test_geometri_panggung_menandai_pelaku_yang_terlalu_jauh():
    temuan = periksa_kedekatan_pelaku(
        visual_x=500,
        visual_y=900,
        setengah_lebar=100,
        pelaku=[("aktor-1", "Pelaku", 900, 900)],
        tokoh_lain=[],
        jarak_maks=160,
        pita_kedalaman=180,
        label_visual="objek",
        lokasi="tes",
    )
    assert [t.kode for t in temuan] == ["PELAKU_JAUH"]


def test_geometri_panggung_mendeteksi_tokoh_lain_yang_menghalangi_blocking():
    temuan = periksa_kedekatan_pelaku(
        visual_x=540,
        visual_y=1200,
        setengah_lebar=500,
        pelaku=[("aktor-1", "Pelaku", 1240, 1200)],
        tokoh_lain=[("aktor-2", 1030, 1200)],
        jarak_maks=160,
        pita_kedalaman=180,
        label_visual="objek",
        lokasi="tes",
    )
    assert [t.kode for t in temuan] == ["BUKAN_PELAKU_DEKAT"]


def test_geometri_panggung_tidak_mengasumsikan_kategori_atau_representasi_tokoh():
    temuan = periksa_kedekatan_pelaku(
        visual_x=500,
        visual_y=900,
        setengah_lebar=100,
        pelaku=[("peran-x", "Pemeran", 650, 900)],
        tokoh_lain=[],
        jarak_maks=160,
        pita_kedalaman=180,
        label_visual="objek generik",
        lokasi="tes netral",
    )
    assert temuan == []
