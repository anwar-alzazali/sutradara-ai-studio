"""Render uji D2 dengan audio ElevenLabs produksi yang sudah tersimpan.

Audio dibuat sekali melalui workflow suara dan disimpan di cabang suara.
Uji ini memakai ulang MP3/alignment tersebut; tidak memanggil API berbayar.
Efek otomatis sengaja dikecualikan agar pengujian terfokus pada sinkronisasi
narasi, subtitle, dan mux audio-video; efek aksi diuji terpisah.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sutradara import video
from sutradara.garis_waktu import susun
from sutradara.paket_genre.kisah_islami.sutradara import rancang
from sutradara.suara import campur, narasi

OUT = ROOT / "keluaran-bukti/tahap-d2/audio-elevenlabs"
CACHE = ROOT / "keluaran-bukti/tahap-d2/cache-suara-elevenlabs"


def metadados(berkas: Path) -> dict:
    hasil = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,duration",
        "-of", "json", str(berkas),
    ])
    return json.loads(hasil)


def durasi(berkas: Path, jenis: str | None = None) -> float:
    data = metadados(berkas)
    if jenis:
        for stream in data.get("streams", []):
            if stream.get("codec_type") == jenis and stream.get("duration"):
                return float(stream["duration"])
        raise AssertionError(f"stream {jenis} tidak ditemukan pada {berkas.name}")
    return float(data["format"]["duration"])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    # Narasi dan beat identik dengan contoh/nuh_mengejek.json yang telah
    # dibuat audionya pada workflow suara: sidik cache bergantung pada teks,
    # suara, model, setelan, serta kamus lafal.
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
        raise AssertionError(
            f"teks uji berubah: diharapkan 191 huruf, ditemukan {len(teks)}"
        )
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
        raise AssertionError(
            f"alignment tidak lengkap: {jumlah} kata, "
            f"{len(garis.potongan_audio)} potongan"
        )

    # Render subtitle dari alignment nyata. Campur hanya narasi agar uji ini
    # tidak membebani FFmpeg dengan ratusan lapisan efek aksi yang bukan target D2.
    bisu = OUT / "nuh-dialog-elevenlabs.bisu.mp4"
    mp4 = OUT / "nuh-dialog-elevenlabs.mp4"
    video.buat(rencana, bisu, fps=8, garis=garis)
    campur.campur(bisu, mp3, garis, [], mp4)
    bisu.unlink(missing_ok=True)

    lembar = video.lembar(mp4, OUT / "lembar-kontak-elevenlabs.jpg", n=12, kolom=4)
    dur_video = durasi(mp4, "video")
    dur_audio = durasi(mp4, "audio")
    dur_sumber = durasi(mp3)
    ukur = campur.ukur(mp4)
    if abs(dur_video - dur_audio) > 0.15:
        raise AssertionError(
            f"durasi stream tidak sama: video {dur_video:.3f}s, audio {dur_audio:.3f}s"
        )
    if abs(dur_video - dur_sumber) > 1.0:
        raise AssertionError(
            f"durasi hasil dan narasi sumber berbeda: {dur_video:.2f}s vs {dur_sumber:.2f}s"
        )
    if not math.isfinite(ukur.get("lufs", float("nan"))) or not -17.0 <= ukur["lufs"] <= -13.0:
        raise AssertionError(f"kenyaringan di luar target sekitar -15 LUFS: {ukur}")
    if not math.isfinite(ukur.get("puncak_dbtp", float("nan"))) or ukur["puncak_dbtp"] > -1.0:
        raise AssertionError(f"true peak melebihi -1 dBTP: {ukur}")

    ringkas = {
        "penyedia": "ElevenLabs (cache produksi yang sudah ada)",
        "sidik_cache": narasi.sidik(rencana),
        "model": data.get("model"),
        "suara": data.get("suara"),
        "voice_id": data.get("voice_id"),
        "kata_terjajar": jumlah,
        "potongan_audio": garis.potongan_audio,
        "durasi_audio_sumber": round(dur_sumber, 2),
        "durasi_video": round(dur_video, 2),
        "durasi_audio_video": round(dur_audio, 2),
        "pengukuran_audio": ukur,
        "efek_otomatis": "dikecualikan; fokus uji sinkronisasi narasi dan subtitle",
        "mp4": str(mp4),
        "lembar_kontak": str(lembar),
    }
    (OUT / "laporan-audio-elevenlabs.json").write_text(
        json.dumps(ringkas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("D2_AUDIO_ELEVENLABS_LULUS", json.dumps(ringkas, ensure_ascii=False))


if __name__ == "__main__":
    main()
