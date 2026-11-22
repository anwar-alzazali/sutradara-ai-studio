"""Unduh dan susun dataset hadis lokal.

Sumber: github.com/fawazahmed0/hadith-api (lisensi Unlicense / domain publik), yang teksnya berasal dari sunnah.com.
Diambil edisi LENGKAP (bukan .min) karena hanya edisi lengkap yang memuat `arabicnumber`, yaitu nomor yang dipakai
sunnah.com dan dikutip di layar (mis. Muslim memakai penomoran Fuad Abdul Baqi: "HR. MUSLIM 2934").

Keluaran: data/hadis/<kitab>.json.gz (tidak masuk git; dibangun ulang dengan perintah ini atau dipulihkan dari cache CI):
{"kitab": "muslim", "nama": "Sahih Muslim", "sumber": ..., "hadis": {"2934": [{"n": 7367, "sub": "b", "ar": ..., "id": ..., "en": ..., "derajat": [...]}]}}
Satu nomor sunnah.com bisa berisi beberapa riwayat (2934a, 2934b, ...), maka nilainya daftar.

Pakai: python -m sutradara.paket_genre.kisah_islami.dalil.unduh_hadis [--kitab bukhari,muslim] [--keluar data/hadis]
"""
from __future__ import annotations

import argparse
import gzip
import json
import urllib.request
from pathlib import Path

DASAR = "https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/editions/{bahasa}-{kitab}.json"
KITAB = {"bukhari": "Sahih al-Bukhari", "muslim": "Sahih Muslim", "abudawud": "Sunan Abi Dawud",
         "tirmidhi": "Jami` at-Tirmidhi", "nasai": "Sunan an-Nasa'i", "ibnmajah": "Sunan Ibn Majah"}
BAHASA = ("ara", "ind", "eng")
SUMBER = "fawazahmed0/hadith-api (Unlicense), teks dari sunnah.com"
AKAR = Path(__file__).resolve().parents[4]


def _ambil(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "sutradara-ai-studio/0.1"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read())


def _kunci(arabicnumber, hadithnumber) -> tuple[str | None, str]:
    """('2934', 'b') dari '2934.02'; None bila tidak ada nomor Arab."""
    if arabicnumber in (None, "", 0):
        return None, ""
    s = str(arabicnumber)
    pokok, _, pecahan = s.partition(".")
    sub = ""
    if pecahan and int(pecahan or 0) > 0:
        sub = "abcdefghijklmnopqrstuvwxyz"[min(int(pecahan) - 1, 25)]
    return str(int(float(pokok))), sub


def susun(kitab: str, edisi: dict[str, dict]) -> dict:
    """Gabungkan edisi per bahasa (sejajar menurut `hadithnumber`) menjadi indeks bernomor sunnah.com."""
    per_bahasa = {b: {h["hadithnumber"]: h for h in e["hadiths"]} for b, e in edisi.items()}
    ara = edisi["ara"]["hadiths"]
    hasil: dict[str, list] = {}
    kunci_sebelum = None
    for i, h in enumerate(ara):
        n = h["hadithnumber"]
        pokok, sub = _kunci(h.get("arabicnumber"), n)
        entri = {"n": n, "sub": sub, "ar": h.get("text", "").strip(),
                 "id": (per_bahasa.get("ind", {}).get(n) or {}).get("text", "").strip(),
                 "en": (per_bahasa.get("eng", {}).get(n) or {}).get("text", "").strip(),
                 "derajat": (per_bahasa.get("eng", {}).get(n) or h).get("grades") or h.get("grades") or []}
        if pokok is None:
            # tanpa nomor Arab (sunnah.com menulisnya "2934/2935"): pasang ke nomor sebelum DAN sesudahnya
            berikut = next((_kunci(x.get("arabicnumber"), x["hadithnumber"])[0] for x in ara[i + 1:i + 6] if x.get("arabicnumber")), None)
            kunci = [k for k in {kunci_sebelum, berikut} if k]
        else:
            kunci, kunci_sebelum = [pokok], pokok
        for k in kunci:
            hasil.setdefault(k, []).append(entri)
    return {"kitab": kitab, "nama": KITAB[kitab], "sumber": SUMBER, "hadis": hasil}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kitab", default=",".join(KITAB))
    ap.add_argument("--keluar", default=str(AKAR / "data/hadis"))
    a = ap.parse_args(argv)
    keluar = Path(a.keluar); keluar.mkdir(parents=True, exist_ok=True)
    for k in a.kitab.split(","):
        edisi = {b: _ambil(DASAR.format(bahasa=b, kitab=k)) for b in BAHASA}
        data = susun(k, edisi)
        f = keluar / f"{k}.json.gz"
        with gzip.open(f, "wt", encoding="utf-8") as g:
            json.dump(data, g, ensure_ascii=False, separators=(",", ":"))
        print(f"{k}: {len(data['hadis'])} nomor -> {f} ({f.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
