"""Benchmark render serial versus paralel pada runner yang sama."""
from __future__ import annotations
import json
import tempfile
import time
from pathlib import Path
from sutradara import video

def main():
    rencana=json.loads(Path("contoh/nuh_mengejek.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as d:
        hasil={}
        for nama,workers in (("serial",1),("paralel",2)):
            mulai=time.perf_counter()
            video.buat(rencana,Path(d)/f"{nama}.mp4",fps=30,workers=workers,
                       kabar=lambda pesan: print(f"[{nama}] {pesan}"))
            hasil[nama]=time.perf_counter()-mulai
        speedup=hasil["serial"]/hasil["paralel"] if hasil["paralel"] else 0
        print("TAHAP_B_RENDER_BENCHMARK",json.dumps({
            "runner":"same GitHub Actions job",
            "serial_workers":1,"parallel_workers":2,
            "serial_seconds":round(hasil["serial"],2),
            "parallel_seconds":round(hasil["paralel"],2),
            "speedup":round(speedup,3)
        },sort_keys=True))

if __name__=="__main__":
    main()
