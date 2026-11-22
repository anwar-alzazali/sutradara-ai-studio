#!/usr/bin/env python3
"""Bandingkan frame PNG dari main (sebelum ekstraksi) dan PR (sesudah ekstraksi)."""
from __future__ import annotations
import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

WORKER = r'''
import inspect, json, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(root))
from sutradara import adegan, render, video
ambil_data = video.data_render if hasattr(video, "data_render") else video.peta_dalil
try:
    from sutradara.genre import nama_dari_rencana
    ambil_genre = nama_dari_rencana
except ImportError:
    ambil_genre = lambda rencana: None
susun_params = inspect.signature(adegan.susun).parameters
durasi_params = inspect.signature(adegan.durasi).parameters
def shots(rencana):
    if hasattr(video, "daftar_shot"):
        return video.daftar_shot(rencana)
    return [s for b in rencana.get("beat", []) for s in b.get("shot", [])]
def buat_svg(shot, t, tg, data, genre):
    if "data_render" in susun_params:
        return adegan.susun(shot, t, tg, data_render=data, genre=genre)
    return adegan.susun(shot, t, tg, dalil=data)
def durasi_shot(shot, data, genre):
    if "genre" in durasi_params:
        return float(adegan.durasi(shot, data, genre=genre))
    return float(adegan.durasi(shot, data))
out.mkdir(parents=True, exist_ok=True)
jumlah = 0
with render.peramban() as halaman:
    for file in sorted((root / "contoh").glob("*.json")):
        rencana = json.loads(file.read_text(encoding="utf-8"))
        data, genre = ambil_data(rencana), ambil_genre(rencana)
        waktu_global = 0.0
        for indeks, shot in enumerate(shots(rencana)):
            durasi = max(0.2, durasi_shot(shot, data, genre))
            for nomor, t in enumerate((0.0, durasi * 0.5, max(0.0, durasi - 0.1))):
                svg = buat_svg(shot, t, waktu_global + t, data, genre)
                render.png(svg, out / f"{file.stem}__shot-{indeks:03d}__frame-{nomor}.png", halaman=halaman)
                jumlah += 1
            waktu_global += durasi
if jumlah == 0:
    raise SystemExit("Tidak ada frame contoh yang dirender")
print(jumlah)
'''

def jalankan(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)

def hash_frame(folder: Path) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.glob("*.png"))}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="SHA commit dasar PR")
    base_sha = parser.parse_args().base
    repo = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="banding-render-d0-") as tmp:
        tmp = Path(tmp)
        baseline, worker = tmp / "baseline", tmp / "worker.py"
        worker.write_text(WORKER, encoding="utf-8")
        jalankan(["git", "fetch", "--no-tags", "origin", base_sha], repo)
        jalankan(["git", "worktree", "add", "--detach", str(baseline), base_sha], repo)
        try:
            sebelum, sesudah = tmp / "sebelum", tmp / "sesudah"
            n_sebelum = subprocess.run([sys.executable, str(worker), str(baseline), str(sebelum)], cwd=baseline, check=True, capture_output=True, text=True).stdout.strip()
            n_sesudah = subprocess.run([sys.executable, str(worker), str(repo), str(sesudah)], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
            a, b = hash_frame(sebelum), hash_frame(sesudah)
            if a.keys() != b.keys():
                print(f"Daftar frame berbeda: sebelum={len(a)}, sesudah={len(b)}")
                print("Hanya sebelum:", sorted(a.keys() - b.keys())[:10])
                print("Hanya sesudah:", sorted(b.keys() - a.keys())[:10])
                return 1
            berbeda = [nama for nama in a if a[nama] != b[nama]]
            if berbeda:
                print(f"{len(berbeda)} dari {len(a)} frame PNG berubah:")
                for nama in berbeda[:20]: print(" -", nama)
                return 1
            print(f"LULUS: {len(a)} frame PNG identik; {n_sebelum} frame sebelum, {n_sesudah} frame sesudah.")
            return 0
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(baseline)], cwd=repo, check=False)

if __name__ == "__main__":
    raise SystemExit(main())
