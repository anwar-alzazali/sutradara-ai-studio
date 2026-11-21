"""Render bukti visual Tahap B menjadi lembar JPG kecil, tanpa MP4."""
from __future__ import annotations
import json
from pathlib import Path
import sys
AKAR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AKAR))
from PIL import Image, ImageDraw
from sutradara import adegan, render

OUT = Path("keluaran-bukti/tahap-b")
OUT.mkdir(parents=True, exist_ok=True)

def main():
    nuh = json.loads(Path("contoh/nuh_mengejek.json").read_text(encoding="utf-8"))
    dabbah = json.loads(Path("contoh/dabbah_dhuha.json").read_text(encoding="utf-8"))
    yajuj = json.loads(Path("contoh/yajuj_majjuj.json").read_text(encoding="utf-8"))
    dajjal = json.loads(Path("contoh/dajjal_dua_sungai.json").read_text(encoding="utf-8"))
    shots = [
        ("Nuh", nuh["beat"][0]["shot"][0], 1.0),
        ("Dabbah: kabut tanpa wujud", dabbah["beat"][1]["shot"][0], 1.0),
        ("Buraq + nur", {"preset":"dhuha","belakang":[],"tanah_y":1300,
         "buraq":[{"x":540,"y":1450,"s":1.0}],
         "nur":[{"x":540,"y":1120,"nama":"Nabi Muhammad ﷺ","tinggi":280}],"depan":False}, 0.8),
        ("Ya'juj menggali", yajuj["beat"][0]["shot"][0], 2.0),
        ("Ya'juj turun dari bukit", yajuj["beat"][1]["shot"][0], 2.0),
        ("Danau Tiberias surut", yajuj["beat"][2]["shot"][0], 3.0),
        ("Dajjal belakang + pengikut", dajjal["beat"][0]["shot"][0], 3.0),
        ("Tokoh profil + gali", {"preset":"senja","belakang":[],"tokoh":[{"x":540,"y":1450,"s":1.0,"gerak":"gali","arah":"samping","kepala":"imamah","jenis":"pria"}],"depan":False}, 0.8),
        ("Tokoh membelakangi", {"preset":"senja","belakang":[],"tokoh":[{"x":540,"y":1450,"s":1.0,"gerak":"jalan","arah":"belakang","kepala":"kain","jenis":"pria"}],"depan":False}, 0.8),
        ("Perempuan berkerudung", {"preset":"dhuha","belakang":[],"tokoh":[{"x":540,"y":1450,"s":1.0,"gerak":"berdiri","arah":"belakang","kepala":"kerudung","jenis":"wanita"}],"depan":False}, 0.8),
        ("Anak Mesir kuno", {"preset":"dhuha","belakang":[],"tokoh":[{"x":360,"y":1450,"s":1.0,"usia":"anak","zaman":"mesir_kuno","kepala":"kain"},{"x":700,"y":1450,"s":1.0,"usia":"lansia","zaman":"umum","kepala":"imamah"}],"depan":False}, 0.8),
    ]
    gambar=[]
    with render.peramban() as pg:
        for i,(label,shot,t) in enumerate(shots):
            path=OUT/("bingkai_%02d.jpg" % i)
            render.png(adegan.susun(shot,t),path,halaman=pg)
            im=Image.open(path).convert("RGB")
            im.thumbnail((270,480))
            kanvas=Image.new("RGB",(290,525),"white")
            kanvas.paste(im,((290-im.width)//2,30))
            ImageDraw.Draw(kanvas).text((10,8),label,fill="black")
            gambar.append(kanvas)
        # Bukti pasangan sebelum/sesudah memakai browser yang sama; render.png tidak memiliki browser sendiri.
        for nama, shot in (("nuh", nuh["beat"][0]["shot"][0]),
                           ("dabbah", dabbah["beat"][1]["shot"][0])):
            sebelum = dict(shot)
            sebelum["permukaan_tanah"] = "tanpa"
            sesudah = dict(shot)
            sesudah.pop("permukaan_tanah", None)
            render.png(adegan.susun(sebelum, 1.0), OUT / f"{nama}-sebelum.jpg", halaman=pg)
            render.png(adegan.susun(sesudah, 1.0), OUT / f"{nama}-sesudah.jpg", halaman=pg)
    baris=(len(gambar)+2)//3
    lembar=Image.new("RGB",(290*3,525*baris),(238,238,238))
    for i,im in enumerate(gambar):
        lembar.paste(im,((i%3)*290,(i//3)*525))
    lembar.save(OUT/"lembar-kontak.jpg",quality=82,optimize=True)
    for p in sorted(OUT.glob("*.jpg")):
        print("BUKTI_RENDER",p,p.stat().st_size,"bytes")

if __name__ == "__main__":
    main()
