"""Render uji D2 dengan narasi ElevenLabs dan alignment kata produksi.

Pemanggilan API berbayar hanya dilakukan oleh workflow manual suara-d2.yml.
Teks contoh memakai dua beat Nuh yang sudah dipakai pada uji audio sebelumnya.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sutradara import video
from sutradara.garis_waktu import susun
from sutradara.paket_genre.kisah_islami.sutradara import rancang
from sutradara.suara import narasi

OUT = ROOT / "keluaran-bukti/tahap-d2/audio-elevenlabs"
CACHE = ROOT / "keluaran-bukti/tahap-d2/cache-suara-elevenlabs"


def durasi(berkas: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(berkas)
    ]).decode().strip())


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    naskah = {
        "judul": "Nabi Nuh: kapal dan jawaban",
        "inti": "Nabi Nuh membuat kapal dan menjawab ejekan kaumnya.",
        "dalil": [],
        "suara": {"whoosh": "tidak", "vol_suasana": 0},
        "beat": [
            {"narasi": "Lalu beliau mulai membuat kapal. Setiap kali pemuka kaumnya lewat, mereka mengejek.",
             "kata_kunci": ["membuat", "mengejek"], "dalil": [], "suasana": None,
             "peran": ["Nabi Nuh", "pemuka kaum Nuh"]},
            {"narasi": "Nabi Nuh menjawab: kalau kalian mengejek kami, kami pun akan mengejek kalian, seperti kalian mengejek.",
             "kata_kunci": ["menjawab"], "dalil": [], "suasana": None,
             "peran": ["Nabi Nuh", "pemuka kaum Nuh"],
             "dialog": [{"pembicara": "Nabi Nuh", "penjawab": "pemuka kaum Nuh",
                         "ucapan": "Kalau kalian mengejek kami, kami pun akan mengejek kalian."}]},
        ],
    }
    rencana, _ = rancang(naskah)

    # Modul produksi mengurus penjaga Arab, cache, ElevenLabs timestamps, dan pembagian beat.
    js = narasi.buat(rencana, folder=CACHE)
    mp3, _ = narasi.jalur(rencana, CACHE)
    data = json.loads(js.read_text(encoding="utf-8"))
    if not mp3.is_file() or mp3.stat().st_size < 1024:
        raise AssertionError("MP3 ElevenLabs tidak terbentuk atau terlalu kecil")
    if len(data.get("beat", [])) != len(rencana["beat"]):
        raise AssertionError("jumlah kelompok alignment tidak sama dengan jumlah beat")

    garis = susun(rencana, data)
    jumlah = 0
    for kata in garis.kata:
        t = (kata["t0"] + kata["t1"]) / 2
        sub = garis.subtitle_pada(t)
        if not sub or kata["teks"] not in sub[0]:
            raise AssertionError(f"subtitle tidak sinkron: {kata['teks']} @ {t:.3f}s")
        if sub[1] >= len(sub[0]) or sub[0][sub[1]] != kata["teks"]:
            raise AssertionError(f"sorotan kata tidak sinkron: {kata['teks']} @ {t:.3f}s")
        jumlah += 1
    if jumlah < 20 or len(garis.potongan_audio) != len(rencana["beat"]):
        raise AssertionError(f"alignment tidak lengkap: {jumlah} kata, {len(garis.potongan_audio)} potongan")

    mp4 = OUT / "nuh-dialog-elevenlabs.mp4"
    hasil, laporan = video.buat_bersuara(rencana, mp4, fps=8, folder_suara=CACHE)
    lembar = video.lembar(hasil, OUT / "lembar-kontak-elevenlabs.jpg", n=12, kolom=4)
    dur_video = durasi(hasil)
    dur_audio = durasi(mp3)
    if dur_video < 8 or laporan.get("kata") != jumlah:
        raise AssertionError(f"hasil audio/video tidak lengkap: {dur_video:.2f}s, {laporan}")
    ringkas = {
        "penyedia": "ElevenLabs",
        "model": data.get("model"),
        "suara": data.get("suara"),
        "voice_id": data.get("voice_id"),
        "kata_terjajar": jumlah,
        "potongan_audio": garis.potongan_audio,
        "durasi_audio_sumber": round(dur_audio, 2),
        "durasi_video": round(dur_video, 2),
        "laporan_audio": laporan,
        "mp4": str(hasil),
        "lembar_kontak": str(lembar),
    }
    (OUT / "laporan-audio-elevenlabs.json").write_text(
        json.dumps(ringkas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("D2_AUDIO_ELEVENLABS_LULUS", json.dumps(ringkas, ensure_ascii=False))


if __name__ == "__main__":
    main()
