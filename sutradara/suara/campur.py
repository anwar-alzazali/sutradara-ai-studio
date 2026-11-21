"""Pencampuran suara: narasi + suasana per preset + efek + ducking + kenyaringan akhir.

Asal: mesin-video/papan_buat.campur_rekaman (sidechain, loudnorm, limiter) dan aset/suara (47 efek ElevenLabs).
Disempurnakan: rencana suara dibuat OTOMATIS dari garis waktu dan rencana sutradara, lalu bisa diatur per beat:
- suasana (ambience) mengikuti preset waktu beat: senja/dhuha/malam/... (bisa diganti `beat.suasana` atau dimatikan: null);
- `kamera.hentak` -> hentakan, `kamera.guncang` -> dentuman: efek muncul hanya di peristiwa yang memang dirancang;
- kartu dalil muncul -> kilau lembut;
- whoosh di pergantian beat (bukan di tiap potongan; `suara.whoosh`: "beat" | "semua" | "tidak");
- efek bebas per beat: `beat.efek: [{"berkas": "palu_kayu", "kata": "kapal", "vol": 0.6, "loop": true, "sampai": 2.0}]`
  (`kata` = saat kata itu diucapkan; atau `at` = detik sejak awal beat);
- musik latar opsional: `suara.musik: {"berkas": "senandung_haru", "vol": 0.25}`.
Ducking: efek & musik ditekan sidechain oleh narasi, jadi kata tetap jelas tanpa angka volume tetap di tiap efek.
Target akhir sekitar -15 LUFS, puncak -1,5 dBTP (titik awal teknis, bukan alasan merusak dinamika).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..garis_waktu import Garis, _cocok

AKAR = Path(__file__).resolve().parents[2]
ASET = AKAR / "aset/suara"
SUASANA = {"senja": "angin_sejuk", "dhuha": "angin_gurun", "malam": "jangkrik", "malam_merah": "drone_gelap",
           "fajar": "malam_hening"}
VOL_SUASANA = 0.32


def berkas(nama: str) -> Path:
    p = ASET / (nama if nama.endswith(".mp3") else nama + ".mp3")
    if not p.exists():
        raise FileNotFoundError(f"efek suara '{nama}' tidak ada di aset/suara")
    return p


def rancang(rencana: dict, g: Garis) -> list[dict]:
    """Daftar rekaman {berkas, at, vol, ulang?, sampai?, masuk, keluar, loop?} pada waktu video."""
    cfg = rencana.get("suara") or {}
    rek = []
    # suasana: gabungkan beat berurutan yang suasananya sama jadi satu hamparan
    hamparan = []
    for i, b in enumerate(rencana["beat"]):
        preset = b.get("preset") or b["shot"][0].get("preset")
        nama = b["suasana"] if "suasana" in b else SUASANA.get(preset)
        t0 = g.awal_beat[i]; t1 = g.awal_beat[i + 1] if i + 1 < len(g.awal_beat) else g.total
        if hamparan and hamparan[-1]["nama"] == nama:
            hamparan[-1]["t1"] = t1
        else:
            hamparan.append({"nama": nama, "t0": t0, "t1": t1})
    for h in hamparan:
        if h["nama"]:
            rek.append({"berkas": h["nama"], "at": h["t0"], "sampai": h["t1"] - h["t0"], "vol": cfg.get("vol_suasana", VOL_SUASANA),
                        "loop": True, "masuk": 0.6 if h["t0"] > 0 else 0.2, "keluar": 0.8})
    if cfg.get("musik"):
        m = cfg["musik"]
        rek.append({"berkas": m["berkas"], "at": m.get("at", 0.0), "sampai": m.get("sampai", g.total - m.get("at", 0.0)),
                    "vol": m.get("vol", 0.25), "loop": True, "masuk": 1.0, "keluar": 1.5})
    # peristiwa kamera & kartu (waktu shot -> waktu video)
    t = 0.0
    for s in g.shot:
        km = s.get("kamera") or {}
        for at, kuat in km.get("hentak", []):
            rek.append({"berkas": "hentak_serius", "at": t + at, "vol": min(1.0, 0.45 + kuat * 3)})
        for at, kuat in km.get("guncang", []):
            rek.append({"berkas": "dentum_jauh", "at": t + at, "vol": min(1.0, 0.35 + kuat / 60)})
        if s.get("kartu_dalil"):
            rek.append({"berkas": "kilau_cahaya", "at": t + s["kartu_dalil"].get("mulai", 0.0), "vol": 0.35})
        t += s["durasi"]
    # whoosh
    mode = cfg.get("whoosh", "beat")
    titik = g.awal_beat[1:] if mode == "beat" else (g.potong[1:] if mode == "semua" else [])
    for p in titik:
        rek.append({"berkas": "whoosh", "at": max(0.0, p - 0.18), "vol": 0.3})
    # efek bebas per beat
    for i, b in enumerate(rencana["beat"]):
        for e in b.get("efek", []):
            if "kata" in e:
                k = next((k for k in g.kata if k["beat"] == i and _cocok(k["teks"], e["kata"])), None)
                if k is None:
                    raise ValueError(f"beat {i + 1}: efek '{e['berkas']}' menunggu kata '{e['kata']}' yang tidak ada di narasi")
                at = k["t0"] + e.get("geser", 0.0)
            else:
                at = g.awal_beat[i] + e.get("at", 0.0)
            r = {"berkas": e["berkas"], "at": at, "vol": e.get("vol", 0.6)}
            for kunci in ("sampai", "masuk", "keluar", "loop"):
                if kunci in e:
                    r[kunci] = e[kunci]
            rek.append(r)
    for r in rek:
        berkas(r["berkas"])  # gagal cepat bila nama salah
    return rek


def campur(video: Path, narasi_mp3: Path, g: Garis, rekaman: list[dict], keluar: Path, *, lufs: float = -15.0) -> Path:
    """MP4 tanpa suara + narasi + rekaman -> MP4 bersuara (AAC 192k)."""
    ff = shutil.which("ffmpeg") or "ffmpeg"
    dur = g.total
    arg = [ff, "-v", "error", "-y", "-i", str(video), "-i", str(narasi_mp3)]
    fil, narr = [], []
    for k, p in enumerate(g.potongan_audio):
        d = p["a1"] - p["a0"]
        fil.append(f"[1:a]atrim={p['a0']:.3f}:{p['a1']:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,"
                   f"afade=t=out:st={max(0, d - 0.06):.3f}:d=0.06,adelay={int(p['di'] * 1000)}:all=1[n{k}]")
        narr.append(f"[n{k}]")
    fil.append(f"{''.join(narr)}amix=inputs={len(narr)}:normalize=0:duration=longest,apad,atrim=0:{dur:.3f},"
               f"asplit=2[narasi][kendali]" if narr else f"anullsrc=r=44100:cl=stereo,atrim=0:{dur:.3f},asplit=2[narasi][kendali]")
    efek = []
    for k, r in enumerate(rekaman):
        if r.get("loop"):
            arg += ["-stream_loop", "-1"]
        arg += ["-i", str(berkas(r["berkas"]))]
        idx = 2 + k
        rantai = [f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo"]
        if r.get("sampai"):
            rantai.append(f"atrim=0:{r['sampai']:.3f},asetpts=PTS-STARTPTS")
        masuk, kel = r.get("masuk", 0.0), r.get("keluar", 0.0)
        if masuk:
            rantai.append(f"afade=t=in:d={masuk}")
        if kel and r.get("sampai"):
            rantai.append(f"afade=t=out:st={max(0, r['sampai'] - kel):.3f}:d={kel}")
        rantai.append(f"volume={r.get('vol', 0.6)}")
        rantai.append(f"adelay={int(max(0, r['at']) * 1000)}:all=1")
        fil.append(",".join(rantai) + f"[e{k}]")
        efek.append(f"[e{k}]")
    if efek:
        fil.append(f"{''.join(efek)}amix=inputs={len(efek)}:normalize=0:duration=longest,apad,atrim=0:{dur:.3f}[efek]")
        # ducking: efek ditekan saat narasi berbicara (dari mesin-video: threshold .015, attack 8, release 450)
        fil.append("[efek][kendali]sidechaincompress=threshold=0.015:ratio=6:attack=8:release=450:makeup=1[efekd]")
        fil.append("[narasi][efekd]amix=inputs=2:normalize=0:duration=first[campur]")
    else:
        fil.append("[kendali]anullsink"); fil.append("[narasi]anull[campur]")
    fil.append(f"[campur]loudnorm=I={lufs}:TP=-1.5:LRA=11,alimiter=limit=0.89:level=false,aresample=44100[akhir]")
    arg += ["-filter_complex", ";".join(fil), "-map", "0:v", "-map", "[akhir]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{dur:.3f}", "-movflags", "+faststart", str(keluar)]
    subprocess.run(arg, check=True)
    return Path(keluar)


def ukur(video: Path) -> dict:
    """Kenyaringan terpadu (LUFS) dan puncak sejati (dBTP) hasil akhir."""
    import json
    import re
    ff = shutil.which("ffmpeg") or "ffmpeg"
    r = subprocess.run([ff, "-hide_banner", "-i", str(video), "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr)
    d = json.loads(m.group(0)) if m else {}
    return {"lufs": float(d.get("input_i", "nan")), "puncak_dbtp": float(d.get("input_tp", "nan"))}
