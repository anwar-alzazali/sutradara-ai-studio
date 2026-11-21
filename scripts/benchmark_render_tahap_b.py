"""Benchmark render serial dan paralel pada runner yang sama."""
from __future__ import annotations
import json
import tempfile
import time
import subprocess
from pathlib import Path
from PIL import Image, ImageChops
from sutradara import video

def main():
    rencana=json.loads(Path("contoh/nuh_mengejek.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as d:
        hasil={}
        paths={}
        for nama,workers in (("serial",1),("paralel",2)):
            paths[nama]=Path(d)/(nama+".mp4")
            mulai=time.perf_counter()
            video.buat(rencana,paths[nama],fps=30,workers=workers,
                       kabar=lambda pesan: print("["+nama+"] "+pesan))
            hasil[nama]=time.perf_counter()-mulai
        bingkai={}
        for nama,path in paths.items():
            pola=Path(d)/(nama+"_%02d.jpg")
            subprocess.run(["ffmpeg","-v","error","-y","-i",str(path),"-vf",
                            "select='eq(n,0)+eq(n,100)+eq(n,200)'","-vsync","0","-q:v","2",str(pola)],check=True)
            bingkai[nama]=[Image.open(Path(d)/(nama+"_"+str(i).zfill(2)+".jpg")).convert("RGB") for i in range(1,4)]
        identik=all(ImageChops.difference(a,b).getbbox() is None for a,b in zip(bingkai["serial"],bingkai["paralel"]))
        if not identik:
            raise SystemExit("BINGKAI_SERIAL_PARAREL_BERBEDA")
        speedup=hasil["serial"]/hasil["paralel"] if hasil["paralel"] else 0
        print("TAHAP_B_RENDER_BENCHMARK",json.dumps({
            "runner":"same GitHub Actions job","serial_workers":1,"parallel_workers":2,
            "serial_seconds":round(hasil["serial"],2),"parallel_seconds":round(hasil["paralel"],2),
            "speedup":round(speedup,3),"sampled_frames_pixel_identical":identik
        },sort_keys=True))

if __name__=="__main__":
    main()
