from sutradara.rencana.pemeriksaan_umum import periksa_kedekatan_pelaku, periksa_lintasan_dan_interaksi


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
        pelaku=[("aktor-1", "Pelaku", 1190, 1200)],
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


def test_gerak_jalan_tanpa_lintasan_gagal_kecuali_di_tempat_dengan_alasan():
    rencana = {"peran": [{"id": "tokoh", "nama": "Tokoh"}], "beat": [{"shot": [
        {"tokoh": [{"peran": "tokoh", "gerak": "jalan", "x": 420, "y": 1300, "tujuan": "tepi:kiri"}]}
    ]}]}
    assert "LINTASAN_TAK_ADA" in {t.kode for t in periksa_lintasan_dan_interaksi(rencana)}
    rencana["beat"][0]["shot"][0]["tokoh"][0].update(di_tempat=True, alasan_di_tempat="kamera mengikuti tokoh")
    assert "LINTASAN_TAK_ADA" not in {t.kode for t in periksa_lintasan_dan_interaksi(rencana)}


def test_lintasan_keyframe_diakui_dan_arah_interaksi_diberi_periksa():
    rencana = {
        "peran": [{"id": "a", "nama": "A"}, {"id": "b", "nama": "B"}],
        "beat": [{"dialog": [{"pembicara": "a", "penjawab": "b"}], "shot": [{"tokoh": [
            {"peran": "a", "gerak": "jalan", "x": [[0, 300], [2, 500]], "y": 1300, "tujuan": "tokoh:b",
             "bicara": [[0, 1]], "arah": "depan"},
            {"peran": "b", "gerak": "berdiri", "x": 700, "y": 1300,
             "bicara": [[1, 2]], "arah": "depan"},
        ]}]}],
    }
    codes = {t.kode for t in periksa_lintasan_dan_interaksi(rencana)}
    assert "LINTASAN_TAK_ADA" not in codes
    assert "INTERAKSI_MENGHADAP_KAMERA" in codes


def test_dialog_terstruktur_yang_tidak_memiliki_cakupan_diberi_periksa():
    rencana = {"peran": [{"id": "a", "nama": "A"}], "beat": [{
        "dialog": [{"pembicara": "a", "ucapan": "Jawab."}], "shot": [{"tokoh": []}]
    }]}
    assert "DIALOG_TANPA_LIPUTAN" in {t.kode for t in periksa_lintasan_dan_interaksi(rencana)}
