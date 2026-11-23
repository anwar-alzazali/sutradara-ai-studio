"""Render uji D2 memakai audio ElevenLabs produksi yang sudah tersimpan.

Audio dibuat sekali melalui workflow \`suara\` dan disimpan di cabang \`suara\`.
Uji ini memakai ulang MP3/alignment tersebut; tidak memanggil API berbayar.
Teks tiga beat harus identik dengan naskah sumber agar cache dan timing sah.
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
    # Teks harus sama persis dengan contoh/nuh_mengejek.json yang sudah
    # dibuat audionya pada workflow suara: sidik cache dan alignment per beat
    # bergantung pada teks, suara, model, setelan, serta kamus lafal.
    naskah = {
        "judul": "Nabi Nuh: kapal dan jawaban",
        "inti": "Nabi Nuh membuat kapal dan menjawab ejekan kaumnya.",
        "dalil": [],
        "beat": [
            {
                "narasi": "Nabi Nuh mulai membuat kapal di tengah daratan, jauh dari laut.",
                "kata_kunci": ["membuat"], "dalil": [], "suasana": "senja",
                "peran": ["Nabi Nuh", "pengikut beriman"],
            },
            {
                "narasi": "Setiap kali pemuka kaumnya lewat, mereka mengejeknya.",
                "kata_kunci": ["mengejek"], "dalil": [], "suasana": "senja",
                "peran": ["Nabi Nuh", "pemuka kaum Nuh"],
            },
            {
                "narasi": "Nuh menjawab: jika kalian mengejek kami, kami pun akan mengejek kalian.",
                "kata_kunci": ["menjawab"], "dalil": [], "suasana": "senja",
                "peran": ["Nabi Nuh", "pemuka kaum Nuh"],
                "dialog": [{
                    "pembicara": "Nabi Nuh",
                    "penjawab": "pemuka kaum Nuh",
                    "ucapan": "Jika kalian mengejek kami, kami pun akan mengejek kalian.",
                }],
            },
        ],
    }
    rencana, _ = rancang(naskah)

    mp3, js = narasi.jalur(rencana, CACHE)
    if not mp3.is_file() or not js.is_file():
        raise FileNotFoundError(
            f"Cache audio produksi tidak ditemukan: {mp3.name}. "
            "Pastikan cabang suara berisi MP3 dan JSON dari naskah yang sama."
        )
    teks = narasi.teks_narasi(rencana)
    if len(teks) != 191:
        raise AssertionError(f"teks uji berubah: diharapkan 191 huruf, ditemukan {len(teks)}")
    data = json.loads(js.read_text(encoding="utf-8"))
    if data.get("huruf") != len(teks):
        raise AssertionError("panjang teks cache tidak cocok dengan naskah D2")
    if len(data.get("beat", [])) != len(rencana["beat"]):
        raise AssertionError("jumlah kelompok alignment tidak sama dengan jumlah beat")
    for i, (beat, kata) in enumerate(zip(rencana["beat"], data["beat"]), 1):
        if len(kata) != len(narasi.kata_beat(beat["narasi"])):
            raise AssertionError(f"jumlah kata alignment beat {i} tidak cocok")
    setelan = narasi.setelan(rencana)
    if data.get("voice_id") != setelan["voice_id"] or data.get("model") != setelan["model"]:
        raise AssertionError("voice/model cache tidak cocok dengan setelan rencana")

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
        "penyedia": "ElevenLabs (cache produksi yang sudah ada)",
        "sidik_cache": narasi.sidik(rencana),
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
