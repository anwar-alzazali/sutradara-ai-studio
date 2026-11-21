"""Garis waktu video dari waktu kata narasi (fase 2).

Masukan: rencana + hasil `suara.narasi` (kata per beat, detik di berkas audio narasi). Keluaran `Garis`:
- `shot`: salinan shot dengan `durasi` baru; semua waktu di dalam shot (keyframe, jadwal gerak/wajah, guncang/hentak,
  judul_mulai/subtitle_mulai) DISKALA ke durasi baru, jadi koreografi sutradara tetap utuh walau narasi lebih panjang/pendek.
- `potongan_audio`: potongan narasi per beat + posisinya di video (narasi dipotong per beat, bukan diputar lurus,
  supaya kartu dalil bisa mendapat waktu baca sendiri tanpa ditimpa suara).
- `kata`: semua kata pada waktu VIDEO -> subtitle per frasa dengan kata aktif disorot, dan titik efek `@kata`.

Aturan potong (resep B1): shot dipotong 0,1 dtk sebelum kata di `potong_di` diucapkan. Tanpa `potong_di`, waktu
narasi beat dibagi menurut perbandingan durasi rancangan shot. Shot kartu dalil tanpa `durasi` = sisipan SESUDAH
narasi beat, selama waktu baca kartu (narasi diam; mata penonton membaca). Beat yang isinya hanya kartu: narasi
diputar di atas kartu, durasi = yang terpanjang.
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field

from . import adegan
from .suara.narasi import kata_beat

POTONG_SEBELUM = 0.10   # potongan jatuh sesaat sebelum kata kunci
AWAL = 0.35             # jeda sebelum kata pertama video
JEDA = 0.30             # jeda antar beat (bisa diganti rencana.suara.jeda / beat.jeda)
EKOR = 1.0              # sisa sesudah kata terakhir
MIN_SHOT = 0.6
MAKS_KATA_FRASA = 5
KUNCI_MULAI = ("judul_mulai", "judul_sampai", "subtitle_mulai")


@dataclass
class Garis:
    shot: list = field(default_factory=list)            # shot siap render (durasi pasti)
    potongan_audio: list = field(default_factory=list)  # {"a0","a1","di"}: audio [a0,a1] diletakkan di detik video `di`
    kata: list = field(default_factory=list)            # {"t0","t1","teks","beat"} waktu video
    awal_beat: list = field(default_factory=list)
    potong: list = field(default_factory=list)          # detik video tiap potongan shot (untuk whoosh)
    total: float = 0.0

    def frasa(self) -> list[dict]:
        return frasa(self.kata)

    def subtitle_pada(self, t: float):
        """(daftar kata frasa, indeks kata yang sedang diucapkan) pada detik video t, atau None."""
        for f in self._frasa_cache():
            if f["t0"] <= t < f["t1"]:
                aktif = max([j for j, k in enumerate(f["kata"]) if k["t0"] <= t + 0.02] or [0])
                return [k["teks"] for k in f["kata"]], aktif
        return None

    def _frasa_cache(self):
        if not hasattr(self, "_fc"):
            self._fc = frasa(self.kata)
        return self._fc


def _bersih(w: str) -> str:
    return re.sub(r"[^\w]", "", w.lower())


def _cocok(kata: str, kunci: str) -> bool:
    """'mengejeknya' cocok dengan kunci 'mengejek' (imbuhan akhir -nya/-lah/-kah/-mu/-ku dibolehkan)."""
    a, b = _bersih(kata), _bersih(kunci)
    return a == b or (a.startswith(b) and a[len(b):] in ("nya", "lah", "kah", "mu", "ku", "pun"))


def frasa(kata: list[dict], maks: int = MAKS_KATA_FRASA) -> list[dict]:
    """Kata -> frasa subtitle: putus di tanda baca, di pergantian beat, di jeda > 0,35 dtk, atau setelah `maks` kata."""
    hasil, buf = [], []

    def tutup():
        if buf:
            hasil.append({"t0": buf[0]["t0"], "t1": buf[-1]["t1"], "kata": list(buf), "teks": " ".join(k["teks"] for k in buf)})
            buf.clear()
    for k in kata:
        if buf and (k["beat"] != buf[-1]["beat"] or k["t0"] - buf[-1]["t1"] > 0.35 or len(buf) >= maks):
            tutup()
        buf.append(k)
        if re.search(r"[.,;:!?…]$", k["teks"]):
            tutup()
    tutup()
    for a, b in zip(hasil, hasil[1:]):  # subtitle bertahan sampai frasa berikut (maks 0,6 dtk), tidak berkedip
        a["t1"] = min(b["t0"], a["t1"] + 0.6)
    if hasil:
        hasil[-1]["t1"] += 0.6
    return hasil


def skala_waktu(spec, f: float):
    """Kalikan semua waktu di dalam spesifikasi shot dengan f (keyframe [[t,v]], jadwal [[t,nama]], peristiwa)."""
    if isinstance(spec, dict):
        out = {}
        for k, v in spec.items():
            if k in KUNCI_MULAI and isinstance(v, (int, float)):
                out[k] = v * f
            elif k == "kartu_dalil":
                out[k] = v  # waktu kartu dihitung dari waktu baca, tidak diskala
            else:
                out[k] = skala_waktu(v, f)
        return out
    if isinstance(spec, list):
        if spec and all(isinstance(p, (list, tuple)) and len(p) == 2 and isinstance(p[0], (int, float))
                        and not isinstance(p[0], bool) for p in spec):
            return [[p[0] * f, skala_waktu(p[1], f) if isinstance(p[1], (dict, list)) else p[1]] for p in spec]
        return [skala_waktu(v, f) for v in spec]
    return spec


def _sisipan_kartu(shot: dict) -> bool:
    return bool(shot.get("kartu_dalil")) and "durasi" not in shot


def _durasi_rancangan(shot: dict, dl: dict) -> float:
    return adegan.durasi(shot, dl)


def _shot_baru(shot: dict, durasi_baru: float, dl: dict) -> dict:
    lama = _durasi_rancangan(shot, dl)
    s = skala_waktu(copy.deepcopy(shot), durasi_baru / lama) if lama > 0 and not _sisipan_kartu(shot) else copy.deepcopy(shot)
    s["durasi"] = round(durasi_baru, 3)
    tx = s.get("teks")
    if tx:  # subtitle kini dari waktu kata (global); subtitle tulisan tangan dibuang
        for k in ("subtitle", "sorot", "subtitle_mulai"):
            tx.pop(k, None)
    return s


def susun(rencana: dict, narasi: dict) -> Garis:
    """`narasi` = isi JSON dari suara.narasi.buat: {"beat": [[[t0, t1, teks], ...], ...]}."""
    dl = {d["id"]: d for d in rencana.get("dalil", [])}
    cfg = rencana.get("suara") or {}
    jeda_umum, awal = cfg.get("jeda", JEDA), cfg.get("awal", AWAL)
    kata_semua = narasi["beat"]
    if len(kata_semua) != len(rencana["beat"]):
        raise ValueError("jumlah beat narasi tidak sama dengan rencana; buat ulang narasi")
    g = Garis()
    v = 0.0  # kursor video
    n_beat = len(rencana["beat"])
    for i, (beat, kk) in enumerate(zip(rencana["beat"], kata_semua)):
        g.awal_beat.append(v)
        shots = beat["shot"]
        kartu = [s for s in shots if _sisipan_kartu(s)]
        bicara = [s for s in shots if not _sisipan_kartu(s)]
        if not kk:  # beat tanpa narasi: durasi rancangan apa adanya
            for s in shots:
                d = _durasi_rancangan(s, dl)
                g.shot.append(_shot_baru(s, d, dl)); g.potong.append(v); v += d
            continue
        # potongan audio beat ini: sedikit napas sebelum kata pertama dan ekor sesudah kata terakhir
        sblm = kata_semua[i - 1][-1][1] if i > 0 and kata_semua[i - 1] else 0.0
        ssdh = kata_semua[i + 1][0][0] if i + 1 < n_beat and kata_semua[i + 1] else kk[-1][1] + 0.5
        a0 = max(sblm, kk[0][0] - 0.12) if i > 0 else 0.0
        a1 = min(ssdh, kk[-1][1] + 0.35)
        lead = awal if i == 0 else 0.12
        di = v + lead - (kk[0][0] - a0) if i > 0 else v + awal
        di = max(v, di)
        g.potongan_audio.append({"a0": round(a0, 3), "a1": round(a1, 3), "di": round(di, 3)})
        geser = di - a0
        kata_v = [{"t0": t0 + geser, "t1": t1 + geser, "teks": w, "beat": i} for t0, t1, w in kk]
        g.kata += kata_v
        jeda = beat.get("jeda", jeda_umum)
        akhir_bicara = kata_v[-1]["t1"] + (EKOR if i == n_beat - 1 and not kartu else jeda)
        if not bicara:  # hanya kartu: narasi di atas kartu
            d = max(akhir_bicara - v, sum(_durasi_rancangan(s, dl) for s in kartu))
            ds = [_durasi_rancangan(s, dl) for s in kartu]; ds[-1] += d - sum(ds)
            for s, dd in zip(kartu, ds):
                g.shot.append(_shot_baru(s, dd, dl)); g.potong.append(v); v += dd
            continue
        # titik potong di antara shot berbicara
        span = akhir_bicara - v
        titik = []
        pd = beat.get("potong_di") or []
        cari = 0
        for w in pd:
            idx = next((j for j in range(cari, len(kata_v)) if _cocok(kata_v[j]["teks"], w)), None)
            if idx is None:
                raise ValueError(f"beat {i + 1}: kata potong '{w}' tidak ada di narasi")
            titik.append(kata_v[idx]["t0"] - POTONG_SEBELUM); cari = idx + 1
        if len(titik) != len(bicara) - 1:  # tanpa potong_di (atau jumlah tak cocok): bagi proporsional
            bobot = [_durasi_rancangan(s, dl) for s in bicara]
            tot, acc, titik = sum(bobot), 0.0, []
            for b_ in bobot[:-1]:
                acc += b_; titik.append(v + span * acc / tot)
        batas = [v] + titik + [akhir_bicara]
        for s, t0, t1 in zip(bicara, batas, batas[1:]):
            d = max(MIN_SHOT, t1 - t0)
            g.shot.append(_shot_baru(s, d, dl)); g.potong.append(v); v += d
        for s in kartu:
            d = _durasi_rancangan(s, dl) + (EKOR * 0.5 if i == n_beat - 1 else 0)
            g.shot.append(_shot_baru(s, d, dl)); g.potong.append(v); v += d
    g.total = v
    return g


def periksa_naskah(rencana: dict) -> list[str]:
    """Galat sebelum membayar narasi: kata potong_di harus ada di narasi beat, berurutan."""
    galat = []
    for i, b in enumerate(rencana["beat"], 1):
        kata = kata_beat(b.get("narasi", ""))
        pos = 0
        for w in b.get("potong_di") or []:
            try:
                pos = next(j for j in range(pos, len(kata)) if _cocok(kata[j], w)) + 1
            except StopIteration:
                galat.append(f"beat {i}: kata potong '{w}' tidak ada (atau tidak berurutan) di narasi")
        n_bicara = len([s for s in b["shot"] if not _sisipan_kartu(s)])
        if b.get("potong_di") and len(b["potong_di"]) != n_bicara - 1:
            galat.append(f"beat {i}: potong_di berisi {len(b['potong_di'])} kata untuk {n_bicara} shot berbicara (harus {n_bicara - 1})")
    return galat
