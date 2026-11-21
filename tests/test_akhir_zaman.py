from sutradara.gaya import akhir_zaman
from sutradara.gaya import tokoh, dajjal
import xml.etree.ElementTree as ET
from sutradara import adegan


def test_buraq_putih_tanpa_sayap_dan_wajah_manusia():
    svg = akhir_zaman.buraq(540, 1200)
    ET.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg">{svg}</svg>')
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

def test_dajjal_tampak_belakang_tidak_memperlihatkan_wajah_depan():
    svg = dajjal.belakang(540, 1200, t=1.0, jalan=True, jubah_berkibar=0.8, buka=0.7)
    assert 'class="dajjal belakang"' in svg
    assert "ك ف ر" not in svg
    assert "M-82 -296" in svg
    ET.fromstring(f'<svg xmlns="http://www.w3.org/2000/svg">{svg}</svg>')


def test_shot_buraq_dan_dajjal_belakang_valid_sebagai_svg():
    buraq = adegan.susun({"preset":"dhuha","belakang":[],"buraq":[{"x":540,"y":1450,"s":1}],"depan":False},0.5)
    dajjal_belakang = adegan.susun({"preset":"malam_merah","belakang":[],"dajjal":[{"x":540,"y":1450,"s":0.8,"arah":"belakang","jalan":True,"jubah_berkibar":0.8,"buka":0.8}],"depan":False},0.5)
    ET.fromstring(buraq)
    ET.fromstring(dajjal_belakang)
    assert 'class="buraq"' in buraq
    assert 'class="dajjal belakang"' in dajjal_belakang


def test_jubah_dajjal_berubah_saat_berkibar():
    tenang = dajjal.belakang(540, 1200, jubah_berkibar=0)
    berkibar = dajjal.belakang(540, 1200, jubah_berkibar=1)
    assert tenang != berkibar
