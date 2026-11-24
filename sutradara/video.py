"""Rencana -> MP4 + lembar kontak. Tanpa `garis`: durasi rancangan, tanpa suara (fase 1).
Dengan `garis` (garis_waktu.susun dari narasi): durasi & subtitle mengikuti waktu kata, lalu suara dicampur (fase 2).

Setiap bingkai: adegan.susun(shot, t, tg) -> SVG dimasukkan ke halaman Chromium yang sudah terbuka (tanpa memuat
ulang halaman, jadi cepat) -> tangkapan JPEG -> dialirkan ke ffmpeg (H.264, -preset veryfast, yuv420p).
Antar-shot = potongan keras (resep B1: potongan jatuh di kata kunci; waktu kata datang di fase 2).
"""
from __future__ import annotations

import copy
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from . import adegan, render
from .gaya import dasar
from .genre import dari_rencana, nama_dari_rencana


def daftar_shot(rencana):
    paket=dari_rencana(rencana);hasil=[]
    for beat in rencana["beat"]:
        for asli in beat["shot"]:
            shot=copy.deepcopy(asli)
            # Simpan narasi beat sebagai konteks visual agar adapter genre dapat
            # menurunkan peristiwa yang eksplisit ke komponen renderer.
            shot["_narasi_visual"]=beat.get("narasi","")
            shot["_peran_visual"]=[p.get("nama",p.get("id","")) for p in rencana.get("peran",[])]
            if paket.adaptasi_shot:shot=paket.adaptasi_shot(rencana,shot)
            hasil.append(shot)
    return hasil

def data_render(rencana):
    paket=dari_rencana(rencana)
    return paket.data_render(rencana) if paket.data_render else {}

def total_durasi(rencana):
    data=data_render(rencana);genre=nama_dari_rencana(rencana)
    return sum(adegan.durasi(s,data,genre=genre) for s in daftar_shot(rencana))


def _ffmpeg() -> str:
    f = shutil.which("ffmpeg")
    if not f:
        raise RuntimeError("ffmpeg tidak ditemukan; pasang ffmpeg")
    return f



def _render_shot_berkas(args):
    """Render satu shot di Chromium milik worker sendiri; hasil disimpan per-shot."""
    from pathlib import Path
    shot, indeks, tg, fps, data, garis, folder, genre = args
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    n = max(1, round((tg + adegan.durasi(shot, data, genre=genre)) * fps) - round(tg * fps))
    with render.peramban() as pg:
        kerangka = folder / "kerangka.html"
        kerangka.write_text(dasar.html('<div id="k"></div>'), encoding="utf-8")
        pg.goto(kerangka.as_uri())
        for k in range(n):
            t = k / fps
            sub = garis.subtitle_pada(tg + t) if garis else None
            pg.evaluate("s => { document.getElementById('k').innerHTML = s; }",
                        adegan.susun(shot, t, tg + t, data_render=data, sub=sub, genre=genre))
            if k == 0:
                pg.evaluate("document.fonts.ready")
            (folder / f"frame_{k:08d}.jpg").write_bytes(pg.screenshot(type="jpeg", quality=92))
        kerangka.unlink(missing_ok=True)
    return indeks, n, folder


def buat(rencana: dict, keluar: Path, *, fps: int = 30, crf: int = 20, kabar=print, garis=None, workers: int = 2) -> Path:
    """Render MP4; tiap shot dirender di Chromium terpisah lalu dirangkai berurutan.

    workers=1 menjadi jalur pembanding serial. Setiap worker memiliki browser sendiri,
    sehingga halaman Chromium tidak dipakai bersamaan oleh thread lain.
    """
    from concurrent.futures import ThreadPoolExecutor
    keluar = Path(keluar); keluar.parent.mkdir(parents=True, exist_ok=True)
    ff = [_ffmpeg(), "-v", "error", "-y", "-f", "image2pipe", "-framerate", str(fps), "-i", "-",
          "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p",
          "-movflags", "+faststart", str(keluar)]
    awal = time.time()
    data = data_render(rencana)
    from .genre import nama_dari_rencana
    genre = nama_dari_rencana(rencana)
    shots = list(garis.shot if garis else daftar_shot(rencana))
    tugas, tg = [], 0.0
    with tempfile.TemporaryDirectory() as d:
        for i, shot in enumerate(shots):
            folder = Path(d) / f"shot_{i:05d}"
            tugas.append((shot, i, tg, fps, data, garis, folder, genre))
            tg = round((tg + adegan.durasi(shot, data, genre=genre)) * fps) / fps
        jumlah_worker = max(1, min(int(workers), len(tugas) or 1))
        with ThreadPoolExecutor(max_workers=jumlah_worker) as pool:
            hasil = list(pool.map(_render_shot_berkas, tugas))
        hasil.sort(key=lambda item: item[0])
        proses = subprocess.Popen(ff, stdin=subprocess.PIPE)
        n_total = 0
        try:
            for indeks, n, folder in hasil:
                for frame in sorted(folder.glob("frame_*.jpg")):
                    proses.stdin.write(frame.read_bytes())
                n_total += n
                kabar(f"shot {indeks + 1}: {n} bingkai dirender ({time.time() - awal:.0f} dtk berjalan)")
        finally:
            proses.stdin.close()
            kode = proses.wait()
        if kode != 0:
            raise RuntimeError(f"ffmpeg gagal (kode {kode})")
    kabar(f"selesai: {keluar} · {n_total} bingkai · {n_total / fps:.1f} dtk video · {time.time() - awal:.0f} dtk render · {jumlah_worker} worker")
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


def __getattr__(nama):
    """Shim atribut lama; data domain tetap disediakan oleh paket genre aktif."""
    if nama == "peta_dalil":
        return data_render
    raise AttributeError(f"module {__name__!r} has no attribute {nama!r}")
