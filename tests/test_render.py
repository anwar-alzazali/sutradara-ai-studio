import json
from pathlib import Path

from PIL import Image

from sutradara import adegan, render

CONTOH = Path(__file__).resolve().parents[1] / "contoh"


def test_susun_svg_semua_shot_contoh():
    for f in CONTOH.glob("*.json"):
        r = json.loads(f.read_text(encoding="utf-8"))
        dl = {d["id"]: d for d in r["dalil"]}
        for b in r["beat"]:
            for s in b["shot"]:
                svg = adegan.susun(s, dalil=dl)
                assert svg.startswith("<svg") and 'viewBox="0 0 1080 1920"' in svg


def test_render_png_berukuran_9x16_dan_tidak_kosong(tmp_path):
    r = json.loads((CONTOH / "nuh_mengejek.json").read_text(encoding="utf-8"))
    shot = dict(r["beat"][1]["shot"][1]); shot.pop("kamera", None)  # tanpa kamera: koordinat dunia = layar
    out = render.png(adegan.susun(shot), tmp_path / "x.png")
    im = Image.open(out).convert("RGB")
    assert im.size == (1080, 1920)
    # Uji pusat pilar yang diposisikan di x=190 pada contoh Nuh.
    assert max(im.getpixel((205, 1100))) > 240
    assert len(im.resize((54, 96)).getcolors(maxcolors=10000)) > 200
    assert 'filter="url(#kabur)"' not in adegan.susun(shot)

def test_visual_kapal_nuh_memiliki_kontur_tegas_dan_batu_depan_tanpa_blur():
    from sutradara.gaya import benda, latar
    kapal = benda.bahtera(650, 1235, s=0.9, jadi=0.9)
    batu = latar.batu_depan()
    assert 'stroke="#160d08" stroke-width="22"' in kapal
    assert 'stroke="#f0bd79" stroke-width="7"' in kapal
    assert 'filter="url(#kabur)"' not in batu
    assert 'stroke-width="8"' in batu


def test_pendar_nur_lebih_terlokalisasi_dan_inti_pilar_tetap_terang():
    from sutradara.gaya import nur
    svg = nur.pilar(205, 1330)
    assert 'rx="155.0" ry="190.0"' in svg
    assert 'opacity=".42"' in svg
    assert 'fill="#ffffff"' in svg


def test_tekstur_tanah_deterministik_perspektif_dan_jenis():
    from sutradara.gaya import latar
    a = latar.tekstur_tanah("senja", 1250, jenis="tanah_berbatu", seed=17)
    b = latar.tekstur_tanah("senja", 1250, jenis="tanah_berbatu", seed=17)
    c = latar.tekstur_tanah("senja", 1250, jenis="tanah_berbatu", seed=18)
    pasir = latar.tekstur_tanah("senja", 1250, jenis="pasir", seed=17)
    assert a == b
    assert a != c and a != pasir
    assert 'clip-path="url(#tanah_tekstur_clip)"' in a
    assert 'filter="url(#kabur)"' not in a
    assert "ellipse" in a


def test_rencana_bisa_memilih_permukaan_dan_tanah_bawaan_bertekstur():
    from sutradara import adegan
    from sutradara.gaya import latar
    shot = {"preset": "dhuha", "belakang": [], "permukaan_tanah": "pasir",
            "seed_tanah": 29, "tokoh": [{"x": 540, "y": 1500}]}
    svg = adegan.susun(shot)
    assert latar.PERMUKAAN_BAWAAN["dhuha"] == "tanah_berbatu"
    assert "tanah_tekstur_clip" in svg
    assert svg.index("tanah_tekstur_clip") < svg.index('stroke-width="26"')
    assert 'filter="url(#kabur)"' not in svg
