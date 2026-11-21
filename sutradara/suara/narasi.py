"""Narasi ElevenLabs dengan waktu per kata.

Asal: mesin-video/narasi_api.py + papan/kisah/dlib.py (Nov 2026). Disempurnakan:
- SATU permintaan untuk seluruh narasi video (semua beat digabung) -> intonasi menyambung, kredit hemat.
- Cache per sidik isi (teks + suara + model + setelan + kamus lafal): narasi yang sama tidak pernah dibayar dua kali.
- Kata hasil penjajaran ElevenLabs dibagi kembali per beat (dihitung dari jumlah kata tiap beat).
- Kamus lafal (lafal.json): kata asing dikirim dengan ejaan bunyi, subtitle tetap memakai tulisan asli.
- Penjaga Arab: teks berhuruf Arab ditolak sebelum dikirim (bacaan Arab tidak disuarakan AI).

Kunci: env ELEVENLABS_API_KEY (GitHub Secrets). Di sesi pengembangan tanpa kunci, jalankan workflow `suara`.
Keluaran (data/suara/<sidik>.mp3 + .json) disimpan workflow di cabang `suara`; ambil dengan `python -m sutradara ambil-suara`.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

from .penjaga_arab import periksa_teks_narasi

AKAR = Path(__file__).resolve().parents[2]
FOLDER = AKAR / "data/suara"
LAFAL = Path(__file__).with_name("lafal.json")
# suara tetap yang terbukti di mesin-video
SUARA = {"ozhy": "UdQDnhmw5mrED2XYPXhu", "mahaputra": "v70fYBHUOrHA3AKIBjPq", "meraki": "OKanSStS6li6xyU1WdXa",
         "mazlan": "GcHP6UfXX0zaHYu0b0ut", "jack": "7EzWGsX10sAS4c9m9cPf"}
BAWAAN = {"narator": "ozhy", "model": "eleven_v4", "stabil": 0.5, "mirip": 0.75, "kecepatan": 1.0}
_ADA_HURUF = re.compile(r"\w")


def setelan(rencana: dict) -> dict:
    s = dict(BAWAAN); s.update(rencana.get("suara") or {})
    s["voice_id"] = SUARA.get(s["narator"], s["narator"])
    return s


def kamus_lafal() -> dict:
    if not LAFAL.exists():
        return {}
    return {k: v for k, v in json.loads(LAFAL.read_text(encoding="utf-8")).items() if not k.startswith("_")}


def kata_beat(teks: str) -> list[str]:
    return [w for w in teks.split() if _ADA_HURUF.search(w)]


def teks_narasi(rencana: dict) -> str:
    """Seluruh narasi video: beat dipisah baris kosong (ElevenLabs memberi jeda alami)."""
    return "\n\n".join(b["narasi"].strip() for b in rencana["beat"] if b.get("narasi", "").strip())


def sidik(rencana: dict) -> str:
    s = setelan(rencana)
    isi = json.dumps([teks_narasi(rencana), s["voice_id"], s["model"], s["stabil"], s["mirip"], s["kecepatan"], kamus_lafal()],
                     ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(isi.encode()).hexdigest()[:16]


def jalur(rencana: dict, folder: Path = FOLDER) -> tuple[Path, Path]:
    k = sidik(rencana)
    return folder / f"{k}.mp3", folder / f"{k}.json"


def terapkan_lafal(teks: str, lafal: dict) -> tuple[str, dict]:
    balik = {}
    for asli, bunyi in lafal.items():
        teks, n = re.subn(r"(?<![\w-])" + re.escape(asli) + r"(?![\w-])", bunyi, teks)
        if n:
            balik[bunyi] = asli
    return teks, balik


def kata_dari_huruf(al: dict) -> list[dict]:
    """Penjajaran huruf ElevenLabs -> kata {teks, t0, t1}. Tag [emosi] dilewati."""
    kata, buf, t0, t1, tag = [], "", None, None, False
    for c, s, e in zip(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]):
        if c in "<[":
            tag = True
        if tag:
            if c in ">]":
                tag = False
            continue
        if c.isspace():
            if buf:
                kata.append({"teks": buf, "t0": t0, "t1": t1}); buf = ""
            continue
        if not buf:
            t0 = s
        buf += c; t1 = e
    if buf:
        kata.append({"teks": buf, "t0": t0, "t1": t1})
    return kata


def _kembalikan_tulisan(kata: list[dict], balik: dict) -> None:
    polos = lambda x: "".join(c for c in unicodedata.normalize("NFKD", x) if not unicodedata.combining(c)).lower()
    for k in kata:
        m = re.match(r"^(\W*)(.*?)(\W*)$", k["teks"])
        for bunyi, asli in balik.items():
            if polos(m.group(2)) == polos(bunyi):
                k["teks"] = m.group(1) + asli + m.group(3); break


def bagi_per_beat(rencana: dict, kata: list[dict]) -> list[list[dict]]:
    """Kata penjajaran dibagi ke beat menurut jumlah kata tiap narasi beat."""
    kk = [k for k in kata if _ADA_HURUF.search(k["teks"])]
    hasil, pos = [], 0
    for b in rencana["beat"]:
        n = len(kata_beat(b.get("narasi", "")))
        hasil.append(kk[pos:pos + n]); pos += n
    if pos != len(kk):
        raise ValueError(f"jumlah kata audio ({len(kk)}) tidak sama dengan naskah ({pos}); periksa lafal/tanda baca")
    return hasil


def buat(rencana: dict, *, folder: Path = FOLDER, kirim=None) -> Path:
    """Pastikan narasi rencana ada (cache). `kirim(teks, setelan) -> (mp3_bytes, alignment)` dapat diganti untuk tes."""
    mp3, js = jalur(rencana, folder)
    if mp3.exists() and js.exists():
        return js
    s = setelan(rencana)
    teks_asli = teks_narasi(rencana)
    teks, balik = terapkan_lafal(teks_asli, kamus_lafal())
    periksa_teks_narasi(teks, "narasi rencana")
    data, al = (kirim or _kirim_elevenlabs)(teks, s)
    kata = kata_dari_huruf(al) if al else []
    _kembalikan_tulisan(kata, balik)
    per_beat = bagi_per_beat(rencana, kata)
    folder.mkdir(parents=True, exist_ok=True)
    mp3.write_bytes(data)
    js.write_text(json.dumps({"suara": s["narator"], "voice_id": s["voice_id"], "model": s["model"], "huruf": len(teks),
                              "beat": [[[round(k["t0"], 3), round(k["t1"], 3), k["teks"]] for k in b] for b in per_beat]},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    return js


def _kirim_elevenlabs(teks: str, s: dict) -> tuple[bytes, dict]:
    kunci = os.environ.get("ELEVENLABS_API_KEY")
    if not kunci:
        raise RuntimeError("ELEVENLABS_API_KEY kosong: jalankan workflow 'suara' (kunci ada di GitHub Secrets)")
    badan = {"text": teks, "model_id": s["model"],
             "voice_settings": {"stability": s["stabil"], "similarity_boost": s["mirip"], "speed": s["kecepatan"]}}
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{s['voice_id']}/with-timestamps?output_format=mp3_44100_128"
    req = urllib.request.Request(url, data=json.dumps(badan).encode(), method="POST",
                                 headers={"xi-api-key": kunci, "Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ElevenLabs galat {e.code}: {e.read().decode(errors='replace')[:400]}") from None
    return base64.b64decode(r["audio_base64"]), (r.get("normalized_alignment") or r.get("alignment"))
