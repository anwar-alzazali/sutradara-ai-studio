import math

import pytest

from sutradara import gerak as G
from sutradara.gaya import tokoh as TK


def _ujung(a1, a2):
    ex, ey = G.LENGAN_A * math.sin(math.radians(a1)), G.LENGAN_A * math.cos(math.radians(a1))
    return ex + G.LENGAN_B * math.sin(math.radians(a2)), ey + G.LENGAN_B * math.cos(math.radians(a2))


@pytest.mark.parametrize("target", [(-4, -50), (-30, -48), (-36, -32), (-6, 96), (26, -46), (60, 0)])
def test_ik_tangan_sampai_tujuan(target):
    x, y = _ujung(*G.ik(*target))
    assert math.hypot(x - target[0], y - target[1]) < 1.5


@pytest.mark.parametrize("nama", G.SEMUA)
def test_semua_gerak_bisa_digambar(nama):
    for t in (0.0, 0.37, 1.1):
        svg = TK.orang(540, 1500, 1.0, gerak=nama, t=t)
        assert svg.startswith("<g") and "nan" not in svg


def test_gerak_berulang_benar_benar_bergerak():
    for nama in ("jalan", "lari", "joget", "lompat", "melambai", "palu"):
        assert TK.orang(0, 0, gerak=nama, t=0.1) != TK.orang(0, 0, gerak=nama, t=0.25)


def test_jadwal_bercampur_halus():
    spec = [[0, "berdiri"], [1.0, "angkat"]]
    awal, tengah, akhir = (G.pada(spec, t)["la_ka"] for t in (0.99, 1.0 + G.CAMPUR / 2, 1.0 + G.CAMPUR + .01))
    assert awal < tengah < akhir


def test_duduk_menggambar_bangku_dan_lompat_terangkat():
    assert "#8a5a3a" in TK.orang(0, 0, gerak="duduk", t=.5)
    assert G.pada("lompat", 0.55)["naik"] < -100


@pytest.mark.parametrize("wajah", TK.WAJAH)
def test_semua_ekspresi(wajah):
    assert TK.orang(0, 0, wajah=wajah, t=1.0)


def test_jadwal_wajah_dan_mulut_bicara():
    spec = [[0, "senyum"], [2, "marah"]]
    assert TK.orang(0, 0, wajah=spec, t=1.0) != TK.orang(0, 0, wajah=spec, t=2.5)
    diam, bicara = TK.orang(0, 0, t=1.1), TK.orang(0, 0, t=1.1, bicara=[[1.0, 2.0]])
    assert diam != bicara


def test_nama_salah_ditolak():
    with pytest.raises(ValueError):
        TK.orang(0, 0, gerak="terbang")
    with pytest.raises(ValueError):
        TK.orang(0, 0, wajah="bingung", t=1)
