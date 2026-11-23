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



def periksa_alignment_sumber(data: dict, dur_sumber: float, potongan: list[dict]) -> float:
    """Pastikan kata tidak melewati MP3; kembalikan ekor hening yang perlu ditambahkan.

    Alignment ElevenLabs dapat menyertakan ekor jeda setelah kata terakhir.
    Ekor itu bukan audio yang harus sudah ada di MP3: mux menambahkan hening,
    tetapi akhir kata tetap wajib berada dalam toleransi durasi sumber.
    """
    if dur_sumber <= 0:
        raise AssertionError(f"durasi sumber audio tidak valid: {dur_sumber}")
    akhir_kata = max(
        (float(k[1]) for beat in data.get("beat", []) for k in beat),
        default=0.0,
    )
    if akhir_kata > dur_sumber + 0.15:
        raise AssertionError(
            "alignment kata melewati durasi sumber audio: "
            f"{akhir_kata:.2f}s > {dur_sumber:.2f}s"
        )
    akhir_potongan = max((float(p["a1"]) for p in potongan), default=0.0)
    return max(0.0, akhir_potongan - dur_sumber)


def mux_narasi_cepat(video_bisu: Path, mp3: Path, garis, mp4: Path,
                     padding_ekor: float = 0.0) -> None:
    """Mux potongan narasi; ekor alignment yang melampaui MP3 diisi hening."""
    dur = float(garis.total)
    potongan = garis.potongan_audio
    if not potongan:
        raise AssertionError("garis waktu tidak memiliki potongan audio")
    filter_bagian = []
    label = []
    for i, p in enumerate(potongan):
        awal, akhir, tujuan = float(p["a0"]), float(p["a1"]), float(p["di"])
        if akhir <= awal:
            raise AssertionError(f"potongan audio {i + 1} berdurasi tidak valid")
        # apad hanya menambah hening di ujung sumber, bukan mengubah waktu kata.
        pad = f"apad=pad_dur={padding_ekor + 0.02:.3f}," if padding_ekor > 0 else ""
        filter_bagian.append(
            f"[1:a]{pad}atrim=start={awal:.3f}:end={akhir:.3f},"
            f"asetpts=PTS-STARTPTS,aresample=44100,"
            f"adelay={max(0, round(tujuan * 1000))}:all=1[n{i}]"
        )
        label.append(f"[n{i}]")
    filter_bagian.append(
        f"{''.join(label)}amix=inputs={len(label)}:normalize=0:duration=longest,"
        f"apad,atrim=duration={dur:.3f},"
        "loudnorm=I=-15:TP=-2:LRA=11:print_format=summary[a]"
    )
    mp4.unlink(missing_ok=True)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "warning", "-y",
        "-i", str(video_bisu), "-i", str(mp3),
        "-filter_complex_threads", "1", "-filter_complex", ";".join(filter_bagian),
        "-map", "0:v:0", "-map", "[a]", "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-t", f"{dur:.3f}",
        "-movflags", "+faststart", "-progress", "pipe:1", "-nostats", str(mp4),
    ]
    print(f"MUX_AUDIO_MULAI potongan={len(potongan)} durasi={dur:.2f}s", flush=True)
    proses = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, bufsize=1)
    try:
        assert proses.stdout is not None
        for baris in proses.stdout:
            baris = baris.strip()
            if baris.startswith(("out_time=", "speed=", "progress=")) or baris.startswith(("frame=", "size=")):
                print("FFMPEG " + baris, flush=True)
            elif baris:
                print("FFMPEG " + baris[:500], flush=True)
        kode = proses.wait(timeout=240)
    except subprocess.TimeoutExpired:
        proses.kill()
        proses.wait()
        raise TimeoutError("mux narasi melewati batas 240 detik")
    if kode != 0:
        raise RuntimeError(f"FFmpeg mux narasi gagal (kode {kode})")
    if not mp4.is_file() or mp4.stat().st_size < 100_000:
        raise AssertionError("MP4 hasil mux tidak terbentuk dengan ukuran wajar")
    print(f"MUX_AUDIO_SELESAI ukuran={mp4.stat().st_size} byte", flush=True)


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
    dur_sumber = durasi(mp3)
    padding_ekor = periksa_alignment_sumber(data, dur_sumber, garis.potongan_audio)
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
    video.buat(rencana, bisu, fps=8, garis=garis, kabar=lambda pesan: print(pesan, flush=True))
    mux_narasi_cepat(bisu, mp3, garis, mp4, padding_ekor)
    bisu.unlink(missing_ok=True)

    print("RENDER_SELESAI, MEMBUAT LEMBAR KONTAK", flush=True)
    lembar = video.lembar(mp4, OUT / "lembar-kontak-elevenlabs.jpg", n=12, kolom=4)
    print("MENGUKUR HASIL AUDIO-VIDEO", flush=True)
    dur_video = durasi(mp4, "video")
    dur_audio = durasi(mp4, "audio")
    ukur = campur.ukur(mp4)
    if abs(dur_video - dur_audio) > 0.15:
        raise AssertionError(
            f"durasi stream tidak sama: video {dur_video:.3f}s, audio {dur_audio:.3f}s"
        )
    # Durasi potongan boleh melewati MP3 hanya pada ekor jeda yang sudah
    # divalidasi terpisah; mux mengisinya dengan hening. Kata tetap dijaga
    # agar tidak melewati durasi sumber lebih dari toleransi 0,15 detik.
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
        "padding_ekor_hening": round(padding_ekor, 3),
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
