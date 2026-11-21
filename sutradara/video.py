"""Rencana -> MP4 + lembar kontak. Tanpa `garis`: durasi rancangan, tanpa suara (fase 1).
Dengan `garis` (garis_waktu.susun dari narasi): durasi & subtitle mengikuti waktu kata, lalu suara dicampur (fase 2).

Setiap bingkai: adegan.susun(shot, t, tg) -> SVG dimasukkan ke halaman Chromium yang sudah terbuka (tanpa memuat
ulang halaman, jadi cepat) -> tangkapan JPEG -> dialirkan ke ffmpeg (H.264, -preset veryfast, yuv420p).
Antar-shot = potongan keras (resep B1: potongan jatuh di kata kunci; waktu kata datang di fase 2).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from . import adegan, render
from .gaya import dasar


def daftar_shot(rencana: dict) -> list[dict]:
    return [s for b in rencana["beat"] for s in b["shot"]]


def peta_dalil(rencana: dict) -> dict:
    return {d["id"]: d for d in rencana.get("dalil", [])}


def total_durasi(rencana: dict) -> float:
    dl = peta_dalil(rencana)
    return sum(adegan.durasi(s, dl) for s in daftar_shot(rencana))


def _ffmpeg() -> str:
    f = shutil.which("ffmpeg")
    if not f:
        raise RuntimeError("ffmpeg tidak ditemukan; pasang ffmpeg")
    return f


def buat(rencana: dict, keluar: Path, *, fps: int = 30, crf: int = 20, kabar=print, garis=None) -> Path:
    """Render seluruh rencana ke MP4 (tanpa suara). Kembalikan path berkas."""
    keluar = Path(keluar); keluar.parent.mkdir(parents=True, exist_ok=True)
    proses = subprocess.Popen([_ffmpeg(), "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(fps), "-i", "-",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p",
                               "-movflags", "+faststart", str(keluar)], stdin=subprocess.PIPE)
    awal = time.time(); n_total = 0
    try:
        with render.peramban() as pg, tempfile.TemporaryDirectory() as d:
            kerangka = Path(d) / "kerangka.html"
            kerangka.write_text(dasar.html('<div id="k"></div>'), encoding="utf-8")
            pg.goto(kerangka.as_uri())
            tg = 0.0
            dl = peta_dalil(rencana)
            for i, shot in enumerate(garis.shot if garis else daftar_shot(rencana)):
                # titik potong dibulatkan ke bingkai dari waktu global, supaya galat pembulatan tidak menumpuk
                n = max(1, round((tg + adegan.durasi(shot, dl)) * fps) - round(tg * fps))
                for k in range(n):
                    t = k / fps
                    sub = garis.subtitle_pada(tg + t) if garis else None
                    pg.evaluate("s => { document.getElementById('k').innerHTML = s; }", adegan.susun(shot, t, tg + t, dl, sub=sub))
                    if n_total == 0:
                        pg.evaluate("document.fonts.ready")  # font harus siap sebelum bingkai pertama
                    proses.stdin.write(pg.screenshot(type="jpeg", quality=92))
                    n_total += 1
                tg = round((tg + adegan.durasi(shot, dl)) * fps) / fps
                kabar(f"shot {i + 1}: {n} bingkai ({time.time() - awal:.0f} dtk berjalan)")
    finally:
        proses.stdin.close()
        kode = proses.wait()
    if kode != 0:
        raise RuntimeError(f"ffmpeg gagal (kode {kode})")
    kabar(f"selesai: {keluar} · {n_total} bingkai · {n_total / fps:.1f} dtk video · {time.time() - awal:.0f} dtk render")
    return keluar


def buat_bersuara(rencana: dict, keluar: Path, *, fps: int = 30, kabar=print, folder_suara=None) -> tuple[Path, dict]:
    """Narasi (cache) -> garis waktu -> render -> campur suara. Kembalikan (mp4, laporan)."""
    from . import garis_waktu
    from .suara import campur, narasi
    folder = Path(folder_suara) if folder_suara else narasi.FOLDER
    mp3, js = narasi.jalur(rencana, folder)
    if not (mp3.exists() and js.exists()):
        raise FileNotFoundError(f"narasi {mp3.name} belum ada: jalankan workflow 'suara' lalu `python -m sutradara ambil-suara`")
    g = garis_waktu.susun(rencana, json.loads(js.read_text(encoding="utf-8")))
    keluar = Path(keluar)
    bisu = keluar.with_name(keluar.stem + ".bisu.mp4")
    buat(rencana, bisu, fps=fps, kabar=kabar, garis=g)
    rek = campur.rancang(rencana, g)
    campur.campur(bisu, mp3, g, rek, keluar)
    bisu.unlink(missing_ok=True)
    lap = {"durasi": round(g.total, 2), "shot": len(g.shot), "kata": len(g.kata), "efek": [r["berkas"] for r in rek], **campur.ukur(keluar)}
    kabar(f"suara: {lap}")
    return keluar, lap


def lembar(video: Path, keluar: Path, *, n: int = 16, kolom: int = 8) -> Path:
    """Lembar kontak: n bingkai merata dari video, disusun kolom x baris (untuk tinjauan & kritikus)."""
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)]).strip())
    baris = -(-n // kolom)
    subprocess.run([_ffmpeg(), "-v", "error", "-y", "-i", str(video), "-vf",
                    f"fps={n}/{dur:.3f},scale=270:-1,tile={kolom}x{baris}", "-frames:v", "1", str(keluar)], check=True)
    return Path(keluar)


if __name__ == "__main__":  # python -m sutradara.video rencana.json keluaran.mp4
    import sys
    buat(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), Path(sys.argv[2]))
