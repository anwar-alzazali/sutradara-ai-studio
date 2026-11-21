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
    assert max(im.getpixel((190, 1100))) > 240
    assert len(im.resize((54, 96)).getcolors(maxcolors=10000)) > 200
    assert 'filter="url(#kabur)"' not in adegan.susun(shot)
