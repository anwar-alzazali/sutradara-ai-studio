"""Bandingkan renderer serial dan paralel pada kode/tekstur branch yang sama."""
from __future__ import annotations
import json
import subprocess
import tempfile
import time
from pathlib import Path
import sys

AKAR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AKAR))
from PIL import Image, ImageChops
from sutradara import video


def ambil_sampel(video_path: Path, folder: Path, nama: str):
    pola = folder / (nama + "_%02d.jpg")
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", str(video_path), "-vf",
        "select='eq(n,0)+eq(n,100)+eq(n,200)'", "-vsync", "0", "-q:v", "2", str(pola)
    ], check=True)
    return [
        Image.open(folder / (nama + "_" + str(i).zfill(2) + ".jpg")).convert("RGB")
        for i in range(1, 4)
    ]


def main():
    rencana = json.loads(Path("contoh/nuh_mengejek.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as d:
        folder = Path(d)
        hasil, paths = {}, {}
        for nama in ("branch_serial", "branch_paralel"):
            paths[nama] = folder / (nama + ".mp4")
            mulai = time.perf_counter()
            workers = 1 if nama == "branch_serial" else 2
            video.buat(rencana, paths[nama], fps=30, workers=workers,
                       kabar=lambda m: print(f"[{nama}] " + m))
            hasil[nama] = time.perf_counter() - mulai
        a = ambil_sampel(paths["branch_serial"], folder, "main")
        b = ambil_sampel(paths["branch_paralel"], folder, "branch")
        identik = len(a) == len(b) and all(
            ImageChops.difference(x, y).getbbox() is None for x, y in zip(a, b)
        )
        if not identik:
            raise SystemExit("BINGKAI_MAIN_DAN_BRANCH_BERBEDA")
        speedup = hasil["branch_serial"] / hasil["branch_paralel"] if hasil["branch_paralel"] else 0
        print("TAHAP_B_RENDER_BENCHMARK", json.dumps({
            "baseline": "branch:sutradara/video.py (serial, 1 worker)",
            "candidate": "branch:sutradara/video.py (paralel, 2 worker)",
            "runner": "same GitHub Actions job",
            "baseline_seconds": round(hasil["main_serial"], 2),
            "candidate_seconds": round(hasil["branch_paralel"], 2),
            "speedup": round(speedup, 3),
            "sampled_frames_pixel_identical": identik
        }, sort_keys=True))


if __name__ == "__main__":
    main()
