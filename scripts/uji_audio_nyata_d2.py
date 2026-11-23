"""Uji integrasi D2 memakai narasi dan alignment nyata dari mesin-video (Nabi Nuh)."""
from __future__ import annotations

import json
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from sutradara import video
from sutradara.garis_waktu import susun
from sutradara.paket_genre.kisah_islami.sutradara import rancang
from sutradara.suara import narasi

BASE = "https://raw.githubusercontent.com/anwar-alzazali/mesin-video/dfc5a00b1c465c366a397d7cf9a9417ffc5753de/audio_manual/nuh2"
BAGIAN = ("b06", "b07")
JEDA = 0.22
OUT = Path("keluaran-bukti/tahap-d2/audio-nyata")
OUT.mkdir(parents=True, exist_ok=True)


def unduh(nama: str, tujuan: Path) -> None:
    with urllib.request.urlopen(f"{BASE}/{nama}", timeout=45) as r:
        tujuan.write_bytes(r.read())


def durasi(berkas: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(berkas)
    ]).decode().strip())


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        audio, alignment = [], []
        for nama in BAGIAN:
            mp3, js = tmp / f"{nama}.mp3", tmp / f"{nama}.json"
            unduh(f"{nama}.mp3", mp3)
            unduh(f"{nama}.json", js)
            audio.append(mp3)
            alignment.append(json.loads(js.read_text(encoding="utf-8")))

        naskah = {
            "judul": "Nabi Nuh: kapal dan jawaban",
            "inti": "Nabi Nuh membuat kapal dan menjawab ejekan kaumnya.",
            "dalil": [],
            "suara": {"whoosh": "tidak", "vol_suasana": 0},
            "beat": [
                {"narasi": alignment[0]["teks"], "kata_kunci": ["membuat", "mengejek"],
                 "dalil": [], "suasana": None, "peran": ["Nabi Nuh", "pemuka kaum Nuh"]},
                {"narasi": alignment[1]["teks"], "kata_kunci": ["menjawab"],
                 "dalil": [], "suasana": None, "peran": ["Nabi Nuh", "pemuka kaum Nuh"],
                 "dialog": [{"pembicara": "Nabi Nuh", "penjawab": "pemuka kaum Nuh",
                             "ucapan": "Kalau kalian mengejek kami, kami pun akan mengejek kalian."}]},
            ],
        }
        rencana, _ = rancang(naskah)
        offset = durasi(audio[0]) + JEDA
        gabung = tmp / "narasi.mp3"
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-i", str(audio[0]),
            "-f", "lavfi", "-t", str(JEDA), "-i", "anullsrc=r=44100:cl=stereo",
            "-i", str(audio[1]), "-filter_complex",
            "[0:a][1:a][2:a]concat=n=3:v=0:a=1[out]", "-map", "[out]",
            "-c:a", "libmp3lame", "-b:a", "128k", str(gabung)
        ], check=True)

        kata = []
        for i, data in enumerate(alignment):
            geser = 0.0 if i == 0 else offset
            kata.append([[round(t0 + geser, 3), round(t1 + geser, 3), teks]
                         for t0, t1, teks in data["kata"]])
        data_narasi = {"beat": kata}
        g = susun(rencana, data_narasi)

        # Periksa setiap kata memakai waktu video hasil transformasi, bukan waktu sumber.
        jumlah = 0
        for k in g.kata:
            t = (k["t0"] + k["t1"]) / 2
            sub = g.subtitle_pada(t)
            if not sub or k["teks"] not in sub[0]:
                raise AssertionError(f"subtitle tidak sinkron: {k['teks']} @ video {t:.3f}")
            if sub[1] >= len(sub[0]) or sub[0][sub[1]] != k["teks"]:
                raise AssertionError(f"sorotan kata tidak sinkron: {k['teks']} @ video {t:.3f}")
            jumlah += 1
        if jumlah < 20 or len(g.potongan_audio) != 2:
            raise AssertionError(f"alignment tidak lengkap: {jumlah} kata, {len(g.potongan_audio)} potongan")

        folder = tmp / "cache-suara"
        folder.mkdir()
        mp3_cache, js_cache = narasi.jalur(rencana, folder)
        mp3_cache.write_bytes(gabung.read_bytes())
        js_cache.write_text(json.dumps(data_narasi, ensure_ascii=False), encoding="utf-8")

        mp4 = OUT / "nuh-dialog-audio-nyata.mp4"
        hasil, laporan = video.buat_bersuara(rencana, mp4, fps=8, folder_suara=folder)
        lembar = video.lembar(hasil, OUT / "lembar-kontak-audio-nyata.jpg", n=12, kolom=4)
        dur_video = durasi(hasil)
        if dur_video < 8 or laporan.get("kata") != jumlah:
            raise AssertionError(f"hasil audio/video tidak lengkap: {dur_video:.2f}s, {laporan}")
        ringkas = {
            "sumber": "mesin-video/audio_manual/nuh2",
            "commit_sumber": "dfc5a00b1c465c366a397d7cf9a9417ffc5753de",
            "bagian": list(BAGIAN), "kata_terjajar": jumlah,
            "potongan_audio": g.potongan_audio, "durasi_video": round(dur_video, 2),
            "laporan_audio": laporan, "mp4": str(hasil), "lembar_kontak": str(lembar),
        }
        (OUT / "laporan-audio-nyata.json").write_text(
            json.dumps(ringkas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("D2_AUDIO_NYATA_LULUS", json.dumps(ringkas, ensure_ascii=False))


if __name__ == "__main__":
    main()
