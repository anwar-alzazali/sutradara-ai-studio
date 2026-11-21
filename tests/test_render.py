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

def test_visual_kapal_nuh_memiliki_kontur_tegas_dan_batu_depan_eksplisit_tanpa_blur():
    from sutradara.gaya import benda, latar
    kapal = benda.bahtera(650, 1235, s=0.9, jadi=0.9)
    batu = latar.batu_depan()
    assert 'stroke="#160d08" stroke-width="22"' in kapal
    assert 'stroke="#f0bd79" stroke-width="7"' in kapal
    assert 'filter="url(#kabur)"' not in batu
    assert 'stroke-width="8"' in batu
    svg = adegan.susun({"preset": "senja", "belakang": [], "depan": True})
    assert "M-60 1920" in svg


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


def test_tekstur_tanah_cukup_terlihat_di_layar_kecil_dan_batu_membesar_ke_depan():
    import re
    from sutradara.gaya import latar
    svg = latar.tekstur_tanah("senja", 1250, jenis="tanah_berbatu", seed=3)
    opasitas = [float(x) for x in re.findall(r'opacity="([0-9.]+)"', svg)]
    assert 'opacity=".72"' in svg
    assert 'opacity=".38"' in svg
    assert 'stroke-opacity=".42"' in svg
    radii = [float(x) for x in re.findall(r'rx="([0-9.]+)"', svg)]
    assert max(radii) > 60  # batu besar di bidang dekat kamera
    dhuha = latar.tekstur_tanah("dhuha", 1250, jenis="tanah_berbatu", seed=3)
    assert 'opacity=".72"' not in dhuha  # tekstur Dabbah tidak ikut diubah


def test_shot_pembuka_nuh_memuat_seluruh_haluan_dalam_bingkai():
    rencana = json.loads((CONTOH / "nuh_mengejek.json").read_text(encoding="utf-8"))
    shot = rencana["beat"][0]["shot"][0]
    kamera = shot["kamera"]
    zoom = kamera["zoom"][-1][1]
    pusat = kamera["x"]
    kapal = shot["benda"][0]
    kiri = kapal["x"] - 460 * kapal["s"]
    kanan = kapal["x"] + 530 * kapal["s"]
    assert 540 + (kiri - pusat) * zoom > 0
    assert 540 + (kanan - pusat) * zoom < 1080


def test_pilar_nuh_shot_terakhir_berjarak_dari_ujung_lambung():
    rencana = json.loads((CONTOH / "nuh_mengejek.json").read_text(encoding="utf-8"))
    shot = rencana["beat"][-1]["shot"][-1]
    kapal = shot["benda"][0]
    pilar = shot["nur"][0]
    ujung_kiri_lambung = kapal["x"] - 460 * kapal["s"]
    tepi_pendar_pilar = pilar["x"] + pilar.get("pendar_rx", 155)
    assert ujung_kiri_lambung - tepi_pendar_pilar >= 20
    kamera = shot["kamera"]
    zoom = kamera["zoom"][-1][1]
    pusat_layar = 540 + (pilar["x"] - kamera["x"]) * zoom
    assert pusat_layar > 100  # label/pilar tidak terpotong tepi kiri
    assert pilar["x"] == 205  # posisi pelaku tetap dekat dengan kapal
    assert pilar["lebar"] == 72 and pilar["pendar_rx"] == 45


def test_lapis_depan_tidak_muncul_bawaan_dan_hanya_aktif_jika_diminta():
    bawaan = adegan.susun({"preset": "senja", "belakang": []})
    eksplisit = adegan.susun({"preset": "senja", "belakang": [], "depan": True})
    assert "M-60 1920" not in bawaan
    assert "M-60 1920" in eksplisit


def test_kabut_jauh_berada_di_belakang_bahtera_dan_npc():
    rencana = json.loads((CONTOH / "nuh_mengejek.json").read_text(encoding="utf-8"))
    shot = rencana["beat"][1]["shot"][0]
    svg = adegan.susun(shot)
    kabut = 'fill="#a5546a" opacity="0.38"'
    kapal = 'stroke="#160d08" stroke-width="22"'
    npc = 'stroke-width="26"'
    assert kabut in svg and kapal in svg
    assert svg.index(kabut) < svg.index(kapal)
    assert svg.index(kabut) < svg.index(npc)


def test_sebaran_kerikil_memiliki_gerombol_dan_area_kosong():
    from sutradara.gaya import latar
    import random
    posisi = latar._sebaran_kerikil(random.Random(31), 1250, 136)
    # Petakan bidang dunia menjadi 8 kolom; gerombol membuat kepadatan berbeda,
    # sementara beberapa kolom tetap jarang/kosong, bukan kisi seragam.
    kolom = [0] * 8
    for x, _ in posisi:
        idx = min(7, max(0, int((x + 1080) / 3240 * 8)))
        kolom[idx] += 1
    assert max(kolom) >= min(kolom) * 1.6
    assert max(kolom) - min(kolom) >= 8
    assert len({round(x, 1) for x, _ in posisi}) == len(posisi)


def test_pilar_pembuka_nuh_utuh_di_bingkai_dan_di_belakang_bahtera():
    rencana = json.loads((CONTOH / "nuh_mengejek.json").read_text(encoding="utf-8"))
    shot = rencana["beat"][0]["shot"][0]
    pilar = shot["nur"][0]
    kamera = shot["kamera"]
    zoom = kamera["zoom"][-1][1]
    pusat = kamera["x"]
    x_layar = 540 + (pilar["x"] - pusat) * zoom
    setengah_kapsul = (pilar["lebar"] / 2 + 10) * zoom
    setengah_nama = 125 * zoom
    setengah_pendar = pilar["pendar_rx"] * zoom
    assert x_layar - setengah_kapsul > 0 and x_layar + setengah_kapsul < 1080
    assert x_layar - setengah_nama > 0 and x_layar + setengah_nama < 1080
    assert x_layar - setengah_pendar > 0
    assert pilar["di_belakang_benda"] is True
    svg = adegan.susun(shot)
    assert svg.index('<g class="nur">') < svg.index('stroke="#160d08" stroke-width="22"')
