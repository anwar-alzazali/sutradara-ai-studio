"""Pencampuran suara: narasi + suasana per preset + efek + ducking + kenyaringan akhir.

Asal: mesin-video/papan_buat.campur_rekaman (sidechain, loudnorm, limiter) dan aset/suara (47 efek ElevenLabs).
Disempurnakan: rencana suara dibuat OTOMATIS dari garis waktu dan rencana sutradara, lalu bisa diatur per beat:
- suasana (ambience) mengikuti preset waktu beat: senja/dhuha/malam/... (bisa diganti `beat.suasana` atau dimatikan: null);
- `kamera.hentak` -> hentakan, `kamera.guncang` -> dentuman: efek muncul hanya di peristiwa yang memang dirancang;
- elemen khusus genre dapat mendaftarkan efek kemunculannya melalui hook paket;
- whoosh di pergantian beat (bukan di tiap potongan; `suara.whoosh`: "beat" | "semua" | "tidak");
- efek bebas per beat: `beat.efek: [{"berkas": "palu_kayu", "kata": "kapal", "vol": 0.6, "loop": true, "sampai": 2.0}]`
  (`kata` = saat kata itu diucapkan; atau `at` = detik sejak awal beat);
- musik latar opsional: `suara.musik: {"berkas": "senandung_haru", "vol": 0.25}`.
ATURAN EFEK TERIKAT AKSI (permintaan pemilik 21 Nov 2026): bunyi mengikuti apa yang SEDANG DILAKUKAN di layar.
- Tokoh dengan gerak palu/gali/jalan/lari/lompat -> satu ketukan/langkah (aset/suara/satu) di setiap titik kena
  gerak itu, hanya selama gerak itu berlangsung; keras-pelan mengikuti ukuran tokoh, kiri-kanan mengikuti posisi x.
- Benda yang sedang berubah: bahtera `jadi` bertambah -> ketukan palu selama papan bertambah (bila tak ada tokoh memalu).
- Efek satu-kali BERHENTI di akhir shot tempat ia mulai (fade 0,3 dtk), kecuali ditandai `"lewat": true`.
  Suasana dan musik diatur terpisah, tidak terkena aturan ini.
Ducking: efek & musik ditekan sidechain oleh narasi, jadi kata tetap jelas tanpa angka volume tetap di tiap efek.
Target akhir sekitar -15 LUFS; true-peak target -2 dBTP memberi ruang untuk AAC agar hasil akhir tetap di bawah -1 dBTP.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from . import aksi as AK
from ..garis_waktu import Garis, _cocok
from ..waktu import adalah_kf

AKAR = Path(__file__).resolve().parents[2]
ASET = AKAR / "aset/suara"
SUASANA = {"senja": "angin_sejuk", "dhuha": "angin_gurun", "malam": "jangkrik", "malam_merah": "drone_gelap",
           "fajar": "malam_hening"}
VOL_SUASANA = 0.32
# gerak -> (sampel satu-ketukan, volume dasar pada tokoh s=1)
def _pan(x: float) -> float:
    return max(-0.7, min(0.7, (x - 540) / 540 * 0.7))


def _sisa(shot: dict, at_lokal: float) -> dict:
    """Efek peristiwa berhenti di akhir shotnya (fade 0,3 dtk)."""
    d = max(0.2, shot["durasi"] - at_lokal)
    return {"sampai": round(d, 3), "keluar": min(0.3, d / 2)}


def efek_aksi(shot: dict, mulai: float) -> list[dict]:
    """Ketukan diegetik dari aksi yang terlihat, termasuk perspektif kamera."""
    return AK.efek_aksi(shot, mulai)


def berkas(nama: str) -> Path:
    p = ASET / (nama if nama.endswith(".mp3") else nama + ".mp3")
    if not p.exists():
        raise FileNotFoundError(f"efek suara '{nama}' tidak ada di aset/suara")
    return p


def rancang(rencana: dict, g: Garis) -> list[dict]:
    """Daftar rekaman {berkas, at, vol, ulang?, sampai?, masuk, keluar, loop?} pada waktu video."""
    from ..genre import dari_rencana
    paket = dari_rencana(rencana)
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
        rek += efek_aksi(s, t)
        km = s.get("kamera") or {}
        for at, kuat in km.get("hentak", []):
            rek.append({"berkas": "hentak_serius", "at": t + at, "vol": min(1.0, 0.45 + kuat * 3), **_sisa(s, at)})
        for at, kuat in km.get("guncang", []):
            rek.append({"berkas": "dentum_jauh", "at": t + at, "vol": min(1.0, 0.35 + kuat / 60), **_sisa(s, at)})
        if paket.efek_kemunculan:
            for evento in paket.efek_kemunculan(s):
                at_lokal = float(evento.get("offset", 0.0))
                rek.append({"berkas": evento["berkas"], "at": t + at_lokal,
                            "vol": evento.get("vol", 0.35), **_sisa(s, at_lokal)})
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
            for kunci in ("sampai", "masuk", "keluar", "loop", "pan"):
                if kunci in e:
                    r[kunci] = e[kunci]
            if not e.get("lewat") and "sampai" not in r:  # berhenti di akhir shot tempat ia mulai
                if at >= g.total:
                    continue
                akhir = next((p for p in g.potong[1:] + [g.total] if p > at + 1e-6), g.total)
                # Ekor minimum mencegah satu-kali dekat potongan menjadi klik; fade pendek menyamarkan sambungan.
                r["sampai"] = round(max(0.18, akhir - at), 3)
                r.setdefault("keluar", min(0.12, r["sampai"] / 2))
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
    efek, kelompok = [], {}
    for r in rekaman:  # satu input per berkas (dibagi asplit) -> kerumunan ketukan tidak membuat ratusan input
        kelompok.setdefault((r["berkas"], bool(r.get("loop"))), []).append(r)
    idx = 2
    for (nama, ulang), daftar in kelompok.items():
        if ulang:
            arg += ["-stream_loop", "-1"]
        arg += ["-i", str(berkas(nama))]
        lab = [f"[g{idx}_{j}]" for j in range(len(daftar))]
        fil.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo" +
                   (f",asplit={len(daftar)}" + "".join(lab) if len(daftar) > 1 else lab[0]))
        for j, r in enumerate(daftar):
            rantai = []
            if r.get("sampai"):
                rantai.append(f"atrim=0:{r['sampai']:.3f},asetpts=PTS-STARTPTS")
            masuk, kel = r.get("masuk", 0.0), r.get("keluar", 0.0)
            if masuk:
                rantai.append(f"afade=t=in:d={masuk}")
            if kel and r.get("sampai"):
                rantai.append(f"afade=t=out:st={max(0, r['sampai'] - kel):.3f}:d={kel}")
            if r.get("kecepatan", 1.0) != 1.0:
                rantai.append(AK.filter_kecepatan(r))
            if r.get("pan"):
                p = r["pan"]
                rantai.append(f"pan=stereo|c0={min(1, 1 - p):.3f}*c0|c1={min(1, 1 + p):.3f}*c1")
            rantai.append(f"volume={r.get('vol', 0.6)}")
            rantai.append(f"adelay={int(max(0, r['at']) * 1000)}:all=1")
            fil.append(lab[j] + ",".join(rantai) + f"[e{len(efek)}]")
            efek.append(f"[e{len(efek)}]")
        idx += 1
    if efek:
        fil.append(f"{''.join(efek)}amix=inputs={len(efek)}:normalize=0:duration=longest,apad,atrim=0:{dur:.3f}[efek]")
        # ducking: efek ditekan saat narasi berbicara (dari mesin-video: threshold .015, attack 8, release 450)
        fil.append("[efek][kendali]sidechaincompress=threshold=0.015:ratio=6:attack=8:release=450:makeup=1[efekd]")
        fil.append("[narasi][efekd]amix=inputs=2:normalize=0:duration=first[campur]")
    else:
        fil.append("[kendali]anullsink"); fil.append("[narasi]anull[campur]")
    fil.append(f"[campur]loudnorm=I={lufs}:TP=-2.0:LRA=11,alimiter=limit=0.84:level=false,aresample=44100[akhir]")
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
