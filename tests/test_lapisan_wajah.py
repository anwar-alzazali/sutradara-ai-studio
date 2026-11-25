from sutradara.gaya import tokoh


def test_fitur_wajah_dirender_di_atas_penutup_kepala_imamah():
    svg = tokoh.orang(500, 1500, kepala="imamah", arah="depan", wajah="datar", t=0.5)
    penutup = svg.index('M-37 -8 Q -40 -48')
    mata = svg.index('cx="-11" cy="-6"')
    alis = svg.index('M-18 -17')
    assert penutup < mata < alis


def test_fitur_wajah_dirender_di_atas_penutup_kepala_kain():
    svg = tokoh.orang(500, 1500, kepala="kain", arah="depan", wajah="datar", t=0.5)
    penutup = svg.index('M-40 2 Q -44 -52')
    mata = svg.index('cx="-11" cy="-6"')
    assert penutup < mata


def test_rambut_pendek_tampak_depan_dirender_pada_kepala_terbuka():
    svg = tokoh.orang(500, 1500, kepala="tanpa", model_rambut="pendek", arah="depan")
    assert 'M-34 -8 Q-42 -48 0 -51' in svg


def test_model_rambut_ikal_memiliki_siluet_berbeda():
    pendek = tokoh.orang(500, 1500, kepala="tanpa", model_rambut="pendek", arah="depan")
    ikal = tokoh.orang(500, 1500, kepala="tanpa", model_rambut="ikal", arah="depan")
    assert pendek != ikal
    assert "model_rambut" not in pendek


def test_rambut_tampak_belakang_mengikuti_model():
    pendek = tokoh.orang(500, 1500, kepala="tanpa", model_rambut="pendek", arah="belakang")
    panjang = tokoh.orang(500, 1500, kepala="tanpa", model_rambut="panjang", arah="belakang")
    assert pendek != panjang
    assert "L42 55" in panjang


def test_model_rambut_botak_tidak_menggambar_lapisan_rambut():
    botak = tokoh.orang(500, 1500, kepala="tanpa", model_rambut="botak", arah="depan")
    pendek = tokoh.orang(500, 1500, kepala="tanpa", model_rambut="pendek", arah="depan")
    assert botak != pendek


def test_mata_memiliki_sklera_iris_pupil_dan_highlight():
    svg = tokoh.orang(500, 1500, kepala="tanpa", arah="depan", wajah="datar", t=0.2)
    assert 'fill="#fffdf8"' in svg
    assert 'fill="#3a241b"' in svg
    assert 'fill="#171319"' in svg
    assert 'opacity=".92"' in svg
    assert 'stroke-width="1.9"' in svg


def test_kedipan_menutup_mata_tanpa_menggeser_wajah():
    terbuka = tokoh.orang(500, 1500, kepala="tanpa", arah="depan", wajah="datar", t=0.2)
    tertutup = tokoh.orang(500, 1500, kepala="tanpa", arah="depan", wajah="datar", t=0.0)
    assert 'fill="#fffdf8"' in terbuka
    assert 'fill="#fffdf8"' not in tertutup
    assert 'M-18 -6 Q-11 -2.5 -4 -6' in tertutup


def test_mata_dan_alis_profil_tetap_satu_sisi():
    svg = tokoh.orang(500, 1500, kepala="tanpa", arah="samping", wajah="curiga", t=0.2)
    assert 'cx="-11" cy="-6"' in svg
    assert 'cx="11" cy="-6"' not in svg
    assert 'Q-12' in svg
