"""Penjaga teks Arab sebelum narasi dikirim ke text-to-speech.

Asal: mesin-video/papan/penjaga_arab.py (20 Nov 2026), disalin tanpa perubahan aturan.

Aturan wajib di CLAUDE.md: "Bacaan Arab tidak disuarakan AI (tulisan Arab +
latin + arti)." Teks Arab boleh ditampilkan sebagai tulisan di layar, tetapi
tidak boleh masuk ke payload suara ElevenLabs. Modul ini sengaja hanya
mendeteksi dan menolak: ia TIDAK menghapus, mengganti, mentransliterasi, atau
menebak teks. Kesalahan harus diperbaiki manusia pada naskah sumber --
KECUALI lambang honorifik tunggal (lih. _HONORIFIK_DIKECUALIKAN di bawah,
keputusan pemilik 20 Nov 2026), yang dianggap lambang tipografi, bukan
bacaan Arab.

Dipasang di `sutradara/suara/narasi.py` (titik kirim ke ElevenLabs).
"""
from __future__ import annotations

from typing import Optional


# Blok Unicode untuk huruf/mark Arab, termasuk harakat, bentuk presentasi,
# ekstensi Arab, dan simbol alfabet Arab matematis.
_RENTANG_ARAB = (
    (0x0600, 0x06FF),  # Arabic (termasuk harakat dan angka Arab-Indic)
    (0x0750, 0x077F),  # Arabic Supplement
    (0x0870, 0x089F),  # Arabic Extended-B
    (0x08A0, 0x08FF),  # Arabic Extended-A
    (0x10EC0, 0x10EFF),  # Arabic Extended-C
    (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
    (0x1EE00, 0x1EEFF),  # Arabic Mathematical Alphabetic Symbols
)

# Pengecualian SEMPIT (keputusan pemilik 20 Nov 2026): lambang tipografi
# honorifik tunggal yang lazim menempel di nama dalam teks Indonesia (mis.
# "Rasulullah ﷺ") -- ini simbol/ligatur, bukan kalimat Arab yang dimaksud
# untuk dibaca. HANYA ligatur honorifik satu-simbol dari sub-blok "Arabic
# Ligatures" (U+FDF0-FDF9, U+FDFB) yang dikecualikan.
#
# SENGAJA TIDAK termasuk (tetap ditolak -- ini kalimat/frasa Arab sungguhan,
# bukan sekadar lambang):
#   U+FDFA  ligatur PENUH "shallallahu 'alaihi wasallam" ditulis sbg satu
#           simbol -- tetap DIKECUALIKAN di bawah karena fungsinya sama
#           dengan honorifik U+FDF0-FDF9 (lazim ditulis "Nabi Muhammad ﷺ"
#           di naskah Indonesia), bukan ayat/hadis yang dibacakan.
#   U+FDFD  ligatur "Bismillahir Rahmanir Rahiim" -- ini SATU AYAT utuh
#           dalam satu karakter, bukan sekadar lambang honorifik -> TETAP
#           DITOLAK.
#   U+FDFC  bukan honorifik (lambang mata uang Rial) -- tidak relevan,
#           tidak dikecualikan.
_HONORIFIK_DIKECUALIKAN = frozenset(
    {
        0xFDF0,  # ligatur "صلى" (Koranic stop sign)
        0xFDF1,  # ligatur "قلى" (Koranic stop sign)
        0xFDF2,  # ligatur "الله" (Allah) bentuk terisolasi
        0xFDF3,  # ligatur "اكبر" (Akbar)
        0xFDF4,  # ligatur "محمد" (Muhammad)
        0xFDF5,  # ligatur "صلعم" (Salam)
        0xFDF6,  # ligatur "رسول" (Rasul)
        0xFDF7,  # ligatur "عليه" (Alayhe)
        0xFDF8,  # ligatur "وسلم" (Wasallam)
        0xFDF9,  # ligatur "صلى" (Salla)
        0xFDFA,  # ligatur penuh "shallallahu 'alaihi wasallam" (ﷺ)
        0xFDFB,  # ligatur "جل جلاله" (Jalla Jalaluhu)
    }
)


class TeksArabDilarangError(ValueError):
    """Dilempar jika teks narasi mengandung karakter dari blok Unicode Arab."""


def ada_huruf_arab(teks: str) -> bool:
    """Kembalikan True bila string mengandung karakter dalam blok Unicode Arab.

    Harakat termasuk dalam blok Arabic U+0600–U+06FF sehingga ikut terdeteksi.
    String kosong dan teks non-Arab menghasilkan False.
    """
    if not isinstance(teks, str):
        raise TypeError(f"teks harus berupa str, bukan {type(teks).__name__}")

    return any(
        ord(karakter) not in _HONORIFIK_DIKECUALIKAN
        and any(awal <= ord(karakter) <= akhir for awal, akhir in _RENTANG_ARAB)
        for karakter in teks
    )


def _potongan(teks: str, posisi: int, batas: int) -> str:
    """Ambil potongan teks di sekitar karakter terlarang tanpa mengubahnya."""
    setengah = max(1, batas // 2)
    awal = max(0, posisi - setengah)
    akhir = min(len(teks), awal + batas)
    awal = max(0, akhir - batas)
    hasil = teks[awal:akhir]
    if awal:
        hasil = "…" + hasil
    if akhir < len(teks):
        hasil += "…"
    return hasil


def periksa_teks_narasi(
    teks: str,
    konteks: str = "narasi",
    panjang_potongan: int = 100,
) -> None:
    """Tolak teks Arab sebelum teks boleh diteruskan ke penyedia TTS.

    Args:
        teks: Teks persis yang akan dikirim sebagai narasi.
        konteks: Identitas adegan/baris, misalnya "adegan 2, baris 4".
        panjang_potongan: Batas panjang cuplikan pada pesan error.

    Raises:
        TypeError: Jika teks bukan string atau panjang_potongan bukan bilangan
            positif.
        TeksArabDilarangError: Jika ditemukan karakter Unicode Arab.

    Tidak ada normalisasi atau pembersihan otomatis. Pemanggil harus
    menghentikan pengiriman ke TTS ketika exception ini muncul.
    """
    if not isinstance(teks, str):
        raise TypeError(f"teks harus berupa str, bukan {type(teks).__name__}")
    if not isinstance(panjang_potongan, int) or panjang_potongan < 1:
        raise TypeError("panjang_potongan harus berupa bilangan bulat positif")

    for posisi, karakter in enumerate(teks):
        kode = ord(karakter)
        if kode in _HONORIFIK_DIKECUALIKAN:
            continue
        if any(awal <= kode <= akhir for awal, akhir in _RENTANG_ARAB):
            cuplikan = _potongan(teks, posisi, panjang_potongan)
            lokasi = konteks.strip() if isinstance(konteks, str) and konteks.strip() else "narasi"
            raise TeksArabDilarangError(
                "Teks Arab dilarang dikirim ke ElevenLabs TTS "
                f"({lokasi}). Karakter U+{kode:04X} ditemukan. "
                f"Perbaiki naskah secara manual; teks tidak dihapus/diubah. "
                f"Potongan: {cuplikan!r}"
            )
