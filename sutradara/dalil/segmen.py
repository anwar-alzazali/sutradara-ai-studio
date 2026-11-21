"""Memotong dalil menjadi potongan pendek (Arab + terjemah, masing-masing <= 2 baris) untuk kartu dalil bertahap.

Prinsip:
- Teks yang dipotong HANYA teks terverifikasi (teks_ar/terjemah) atau kutipan yang terbukti potongan persis darinya.
  Tidak ada kata yang diubah, ditambah, atau dibuang; gabungan semua potongan = teks utuh.
- Arab dipotong di tanda waqaf mushaf (ۚ ۖ ۗ ۛ ۘ ۙ) atau tanda baca (، . ؛) bila ada; terjemah di tanda baca.
- Pasangan Arab-terjemah disejajarkan menurut proporsi panjang. Ini PERKIRAAN: tidak ada pemetaan kata-per-kata resmi
  antara Arab dan terjemah Kemenag, jadi satu potongan terjemah bisa sedikit mendahului/tertinggal dari Arabnya.
"""
from __future__ import annotations

import math
import re
import unicodedata

WAQAF = "ۖۗۘۙۚۛۜ"
_HARAKAT = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭ]")
# kapasitas kasar per baris (huruf tampak) pada ukuran kartu: Arab Amiri 58 px, Latin Nunito 44 px, lebar 940 px
ARAB_PER_BARIS, LATIN_PER_BARIS = 38, 40
MAKS_BARIS = 2


def panjang_arab(s: str) -> int:
    """Jumlah huruf tampak (harakat & tanda waqaf tidak memakan lebar)."""
    return len(_HARAKAT.sub("", s).replace(" ", "")) + s.count(" ") // 2


def rapikan(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s or "")).strip()


def kutipan_sah(kutipan: str, sumber: str) -> bool:
    """Kutipan harus potongan persis dari teks sumber (spasi dirapikan, tanpa mengabaikan harakat/huruf)."""
    k, s = rapikan(kutipan), rapikan(sumber)
    return bool(k) and k in s


def _token(teks: str, arab: bool) -> list[tuple[str, float]]:
    """Daftar (kata, bobot_akhir). bobot: 0 = tengah klausa, ~0,1 = koma/jeda ringan, ~0,3 = akhir kalimat/waqaf."""
    kata = rapikan(teks).split(" ")
    out: list[tuple[str, float]] = []
    for w in kata:
        if arab and w and all(c in WAQAF for c in w) and out:
            out[-1] = (out[-1][0] + " " + w, 0.3)
            continue
        e = w[-1:]
        if arab:
            bobot = 0.3 if e in WAQAF or e in ".؛" else 0.12 if e in "،:" else 0.0
        else:
            bobot = 0.3 if e in ".!?" or w[-2:] in ('."', '.”') else 0.12 if e in ",;:" else 0.0
        out.append((w, bobot))
    if not arab:  # kata sambung pembuka klausa: potong SEBELUMnya
        for i in range(len(out) - 1):
            if out[i + 1][0].lower().strip('"“(') in ("dan", "lalu", "kemudian", "maka", "tetapi", "namun", "sedangkan", "karena"):
                out[i] = (out[i][0], max(out[i][1], 0.15))
    if arab:  # kata berikut diawali huruf sambung و/ف biasanya membuka klausa baru -> tempat potong yang baik
        for i in range(len(out) - 1):
            awal = _HARAKAT.sub("", out[i + 1][0])[:1]
            if awal in ("و", "ف"):
                out[i] = (out[i][0], max(out[i][1], 0.18))
    return out


def _lebar(teks: str, arab: bool) -> int:
    return panjang_arab(teks) if arab else len(teks)


def _kum(token, arab: bool) -> list[float]:
    lebar = [_lebar(w, arab) + 1 for w, _ in token]
    total, kum, pos = sum(lebar), 0, []
    for l in lebar:
        kum += l; pos.append(kum / total)
    return pos


def _bagi(token, target: list[float], arab: bool) -> tuple[list[str], list[float]]:
    """Potong di dekat proporsi `target` (kumulatif, tanpa 1.0), utamakan akhir klausa. Kembalikan potongan & proporsi aktual."""
    pos = _kum(token, arab)
    potong, mulai = [], 0
    for j, tg in enumerate(target):
        sisa = len(target) - j
        calon = range(mulai, len(token) - sisa)
        if not calon:
            break
        i = min(calon, key=lambda i: abs(pos[i] - tg) - token[i][1])
        potong.append(i); mulai = i + 1
    hasil, a = [], 0
    for p in potong + [len(token) - 1]:
        hasil.append(" ".join(w for w, _ in token[a:p + 1])); a = p + 1
    return [h for h in hasil if h], [pos[p] for p in potong]


def baris(teks: str, arab: bool) -> list[str]:
    """Bungkus satu potongan menjadi baris sesuai kapasitas."""
    batas = ARAB_PER_BARIS if arab else LATIN_PER_BARIS
    hasil, kini = [], ""
    for w in rapikan(teks).split(" "):
        coba = (kini + " " + w).strip()
        if kini and _lebar(coba, arab) > batas:
            hasil.append(kini); kini = w
        else:
            kini = coba
    if kini:
        hasil.append(kini)
    return hasil


def potong(ar: str, terjemah: str) -> list[tuple[str, str]]:
    """Pasangan (potongan Arab, potongan terjemah), masing-masing muat <= 2 baris.
    Terjemah dipotong lebih dulu (kalimat diutamakan, karena itulah yang dibaca penonton), lalu Arab dipotong di
    proporsi yang sama dengan mengutamakan tanda waqaf."""
    ta, tt = _token(ar, True), _token(terjemah, False)
    mulai_k = max(1, math.ceil(sum(len(w) + 1 for w, _ in tt) / (LATIN_PER_BARIS * MAKS_BARIS)),
                  math.ceil(sum(_lebar(w, True) + 1 for w, _ in ta) / (ARAB_PER_BARIS * MAKS_BARIS)))
    terbaik = None
    for k in range(mulai_k, mulai_k + 12):
        pt, aktual = _bagi(tt, [j / k for j in range(1, k)], False)
        pa, _ = _bagi(ta, aktual, True)
        terbaik = list(zip(pa, pt))
        if len(pa) == len(pt) == k and all(len(baris(x, True)) <= MAKS_BARIS for x in pa) \
                and all(len(baris(x, False)) <= MAKS_BARIS for x in pt):
            return terbaik
    return terbaik


def durasi_baca(terjemah: str) -> float:
    """Detik tampil satu potongan: cukup untuk membaca terjemah (±13 huruf/dtk) + jeda, minimal 2,6 dtk."""
    return round(max(2.6, len(terjemah) / 13 + 1.0), 2)
