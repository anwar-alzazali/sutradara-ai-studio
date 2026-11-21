"""Bandingkan renderer serial pada main dengan renderer paralel pada branch ini."""
from __future__ import annotations
import importlib.util
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


def muat_baseline(folder: Path):
    subprocess.run(["git", "fetch", "--no-tags", "--depth=1", "origin", "main"], check=True)
    sumber = subprocess.check_output(
        ["git", "show", "FETCH_HEAD:sutradara/video.py"], text=True
    )
    path = folder / "video_baseline.py"
    path.write_text(sumber, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("sutradara.video_baseline", path)
    modul = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modul
    spec.loader.exec_module(modul)
    return modul


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
        baseline = muat_baseline(folder)
        hasil, paths = {}, {}
        for nama in ("main_serial", "branch_paralel"):
            paths[nama] = folder / (nama + ".mp4")
            mulai = time.perf_counter()
            if nama == "main_serial":
                baseline.buat(rencana, paths[nama], fps=30, kabar=lambda m: print("[main] " + m))
            else:
                video.buat(rencana, paths[nama], fps=30, workers=2,
                           kabar=lambda m: print("[branch] " + m))
            hasil[nama] = time.perf_counter() - mulai
        a = ambil_sampel(paths["main_serial"], folder, "main")
        b = ambil_sampel(paths["branch_paralel"], folder, "branch")
        identik = len(a) == len(b) and all(
            ImageChops.difference(x, y).getbbox() is None for x, y in zip(a, b)
        )
        if not identik:
            raise SystemExit("BINGKAI_MAIN_DAN_BRANCH_BERBEDA")
        speedup = hasil["main_serial"] / hasil["branch_paralel"] if hasil["branch_paralel"] else 0
        print("TAHAP_B_RENDER_BENCHMARK", json.dumps({
            "baseline": "origin/main:sutradara/video.py (serial, satu Chromium)",
            "candidate": "branch:sutradara/video.py (2 worker, Chromium per shot)",
            "runner": "same GitHub Actions job",
            "baseline_seconds": round(hasil["main_serial"], 2),
            "candidate_seconds": round(hasil["branch_paralel"], 2),
            "speedup": round(speedup, 3),
            "sampled_frames_pixel_identical": identik
        }, sort_keys=True))


if __name__ == "__main__":
    main()
