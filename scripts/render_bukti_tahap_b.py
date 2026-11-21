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
    shots = [
        ("Nuh", nuh["beat"][0]["shot"][0], 1.0),
        ("Dabbah", dabbah["beat"][1]["shot"][0], 1.0),
        ("Buraq + nur", {"preset":"dhuha","belakang":[],"tanah_y":1300,
         "buraq":[{"x":540,"y":1450,"s":1.0}],
         "nur":[{"x":540,"y":1180,"nama":"Nabi Muhammad ﷺ","tinggi":280}],"depan":False}, 0.8),
        ("Dinding Ya'juj", {"preset":"malam","belakang":[],"tanah_y":1300,
         "akhir_zaman":[{"jenis":"dinding_yajuj","x":540,"y":1400,"s":0.8,"lubang":0.7}],"depan":False}, 0.8),
        ("Danau surut", {"preset":"dhuha","belakang":[],"tanah_y":1300,
         "akhir_zaman":[{"jenis":"danau_surut","x":540,"y":1450,"s":1.0,"surut":0.85}],"depan":False}, 0.8),
        ("Massa Ya'juj", {"preset":"senja","belakang":["gunung"],"tanah_y":1300,"tokoh":[
            {"x":90,"y":1430,"s":0.62,"gerak":"lari","kepala":"kain"},
            {"x":220,"y":1480,"s":0.68,"gerak":"lari","kepala":"imamah"},
            {"x":350,"y":1390,"s":0.58,"gerak":"lari","kepala":"kopiah"},
            {"x":500,"y":1500,"s":0.72,"gerak":"lari","kepala":"kain"},
            {"x":650,"y":1410,"s":0.61,"gerak":"lari","kepala":"imamah"},
            {"x":800,"y":1480,"s":0.69,"gerak":"lari","kepala":"kain"},
            {"x":960,"y":1370,"s":0.57,"gerak":"lari","kepala":"kopiah"}],"depan":False}, 0.8),
        ("Dajjal belakang", {"preset":"malam_merah","belakang":[],"tanah_y":1300,
         "dajjal":[{"x":540,"y":1450,"s":1.0,"arah":"belakang","jalan":True,"jubah_berkibar":0.8,"buka":0.8}],"depan":False}, 0.8),
        ("Dajjal depan", {"preset":"malam_merah","belakang":[],"tanah_y":1300,
         "dajjal":[{"x":540,"y":1450,"s":1.0,"lengan":"terbuka"}],"depan":False}, 0.8),
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
    baris=(len(gambar)+2)//3
    lembar=Image.new("RGB",(290*3,525*baris),(238,238,238))
    for i,im in enumerate(gambar):
        lembar.paste(im,((i%3)*290,(i//3)*525))
    lembar.save(OUT/"lembar-kontak.jpg",quality=82,optimize=True)
    for p in sorted(OUT.glob("*.jpg")):
        print("BUKTI_RENDER",p,p.stat().st_size,"bytes")

if __name__ == "__main__":
    main()
