from sutradara.gaya import tokoh


def test_fitur_wajah_dirender_di_atas_penutup_kepala_imamah():
    svg = tokoh.orang(500, 1500, kepala="imamah", arah="depan", wajah="datar")
    penutup = svg.index('M-37 -8 Q -40 -48')
    mata = svg.index('cx="-11" cy="-6"')
    alis = svg.index('M-18 -17')
    assert penutup < mata < alis


def test_fitur_wajah_dirender_di_atas_penutup_kepala_kain():
    svg = tokoh.orang(500, 1500, kepala="kain", arah="depan", wajah="datar")
    penutup = svg.index('M-40 2 Q -44 -52')
    mata = svg.index('cx="-11" cy="-6"')
    assert penutup < mata
