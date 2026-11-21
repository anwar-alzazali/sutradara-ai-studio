from sutradara.gaya import akhir_zaman
from sutradara.gaya import tokoh


def test_buraq_putih_tanpa_sayap_dan_wajah_manusia():
    svg = akhir_zaman.buraq(540, 1200)
    assert 'class="buraq"' in svg
    assert "#f7f4e9" in svg
    assert "<path" in svg
    assert "wing" not in svg.lower()
    assert "penunggang" not in svg.lower()


def test_lubang_dinding_yajuj_membesar():
    kecil = akhir_zaman.dinding_yajuj(540, 1200, lubang=0.1)
    besar = akhir_zaman.dinding_yajuj(540, 1200, lubang=0.9)
    assert 'rx="27.5"' in kecil
    assert 'rx="167.5"' in besar


def test_danau_menyusut_dengan_keyframe():
    penuh = akhir_zaman.danau_surut(540, 1200, surut=0)
    surut = akhir_zaman.danau_surut(540, 1200, surut=1)
    assert penuh != surut


def test_tanda_wajah_diberi_label_ilustrasi():
    assert "ILUSTRASI TANDA" in akhir_zaman.tanda_wajah(540, 1200)


def test_arah_tokoh_memiliki_transisi_halus():
    assert tokoh._arah_derajat("depan", 0) == 0
    assert tokoh._arah_derajat("belakang", 0) == 180
    assert tokoh._arah_derajat([[0, "depan"], [2, "belakang"]], 1) == 90


def test_anak_tokoh_memakai_skala_lebih_kecil():
    dewasa = tokoh.orang(300, 1200, usia="dewasa")
    anak = tokoh.orang(300, 1200, usia="anak")
    assert "scale(1.0000,1.0000)" in dewasa
    assert "scale(0.7200,0.7200)" in anak
