from pathlib import Path
from sutradara.gaya import tokoh
from sutradara.genre import PaketGenre, dari_rencana
from sutradara.rencana.penjaga import SKEMA, _skema_paket

def test_renderer_tokoh_inti_tidak_mengimpor_visual_genre():
    source = (Path(__file__).resolve().parents[1] / "sutradara" / "gaya" / "tokoh.py").read_text(encoding="utf-8")
    assert "from . import benda" not in source
    assert "sutradara.paket_genre" not in source
    assert "sahabat" not in source.lower()
    assert "malaikat" not in source.lower()
    assert "nabi" not in source.lower()

def test_renderer_tokoh_menerima_gambar_item_dari_paket():
    svg = tokoh.orang(500, 1500, barang=[{"jenis": "objek_uji", "tangan": "ka"}],
                      gambar_item=lambda *args, **kwargs: '<rect class="item-kontrak-uji"/>')
    assert 'class="item-kontrak-uji"' in svg

def test_kategori_dan_mode_visual_ditentukan_oleh_skema_paket():
    properti_inti = SKEMA["properties"]["peran"]["items"]["properties"]
    assert properti_inti["kategori"]["type"] == "string" and "enum" not in properti_inti["kategori"]
    assert properti_inti["tampil"]["type"] == "string" and "enum" not in properti_inti["tampil"]
    islami = _skema_paket(dari_rencana({}))["properties"]["peran"]["items"]["properties"]
    assert set(islami["kategori"]["enum"]) == {"nabi","malaikat","sahabat","manusia","makhluk_ghaib","dajjal","yajuj_majuj","hewan"}
    assert set(islami["tampil"]["enum"]) == {"nur","pakaian","siluet","kabut_tanpa_wujud","dajjal_b","hewan","cahaya_malaikat","wajah_cahaya"}
    netral = _skema_paket(PaketGenre(nama="genre_baru_uji"))
    properti_netral = netral["properties"]["peran"]["items"]["properties"]
    assert "enum" not in properti_netral["kategori"] and "enum" not in properti_netral["tampil"]
