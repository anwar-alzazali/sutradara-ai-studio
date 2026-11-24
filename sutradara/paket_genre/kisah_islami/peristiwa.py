"""Ekstraksi peristiwa narasi untuk keputusan visual yang dapat ditelusuri.

Parser ini konservatif: hanya mengikat pelaku, pasien, tujuan, dan perubahan keadaan
ketika relasi bahasanya eksplisit. Peran yang sekadar hadir tidak otomatis menjadi pelaku.
"""
from __future__ import annotations

import re
import unicodedata


def _normal(teks: str) -> str:
    teks = unicodedata.normalize("NFKD", str(teks).lower())
    return "".join(c for c in teks if not unicodedata.combining(c))


_AKSI = {
    "melarikan diri": "lari", "berjalan": "jalan", "berlari": "lari", "lari": "lari",
    "bangkit": "bangkit", "menjauh": "menjauh", "menjauhi": "menjauh",
    "mendekat": "mendekat", "mendekati": "mendekat", "menghampiri": "mendekat",
    "membangun": "membangun", "dibangun": "membangun", "membuat": "membangun",
    "menggali": "menggali", "digali": "menggali", "mengejek": "mengejek",
    "mengolok": "mengejek", "tertawa": "tertawa", "berdoa": "berdoa",
    "memohon": "berdoa", "menyerahkan": "menyerahkan", "memberikan": "menyerahkan",
    "mengulurkan": "menyerahkan", "menerima": "menerima", "berkumpul": "berkumpul",
    "berhimpun": "berkumpul", "terkumpul": "berkumpul", "berkeringat": "berkeringat",
    "tenggelam": "tenggelam", "terbelah": "terbelah", "membelah": "terbelah",
    "retak": "retak", "terpecah": "retak", "runtuh": "runtuh", "roboh": "runtuh",
    "hancur": "runtuh", "terbuka": "terbuka", "membuka": "terbuka",
    "terangkat": "terangkat", "mengangkat": "terangkat", "surut": "surut",
    "mengering": "surut", "didekatkan": "mendekat", "mendekatkan": "mendekat",
    "terbit": "muncul", "muncul": "muncul", "datang": "datang", "pergi": "pergi",
    "jatuh": "jatuh", "terjatuh": "jatuh", "berbicara": "berbicara",
    "menyeru": "berbicara", "berkata": "berbicara", "menjawab": "berbicara",
    "menunjuk": "menunjuk", "menuding": "menunjuk",
}
_OBJEK = {
    "bahtera": "bahtera", "kapal": "bahtera", "dinding": "dinding",
    "bumi": "bumi", "tanah": "bumi", "matahari": "matahari",
    "manusia": "kerumunan", "kerumunan": "kerumunan", "keringat": "keringat",
    "keringatnya": "keringat", "danau": "danau", "sungai": "sungai",
    "pintu": "pintu", "langit": "langit", "gunung": "gunung", "air": "air", "api": "api",
}
_NEGASI = re.compile(r"\b(?:tidak|tak|belum|bukan|jangan)\\b")
_TUJUAN = re.compile(r"\b(?:menuju|ke arah|menghampiri|mendekati)\\s+(?:ke\\s+)?([a-z ]+?)(?=[,.!?;]|$)")
_PERUBAHAN = {"terbelah", "retak", "runtuh", "terbuka", "surut", "terangkat", "muncul", "jatuh"}


def _batas_klausa(teks: str, posisi: int) -> tuple[int, int]:
    kiri = max(teks.rfind(x, 0, posisi) for x in (".", ",", ";", ":", " lalu "))
    kanan = min((p for x in (".", ",", ";", ":") if (p := teks.find(x, posisi)) >= 0), default=len(teks))
    return kiri + 1, kanan


def _cocok_objek(teks: str, awal: int, akhir: int):
    kandidat = []
    for nama, jenis in _OBJEK.items():
        for m in re.finditer(r"(?<![a-z])" + re.escape(nama) + r"(?![a-z])", teks):
            if awal <= m.start() < akhir:
                kandidat.append((m.start(), m.end(), jenis, nama))
    return sorted(kandidat)


def analisis_peristiwa(narasi: str, peran: list[str] | None = None, indeks: int = 0) -> list[dict]:
    """Ekstrak relasi eksplisit; nama peran yang tidak disebut bukan pelaku."""
    teks = _normal(narasi)
    temuan = []
    for frasa, aksi in sorted(_AKSI.items(), key=lambda item: len(item[0]), reverse=True):
        for m in re.finditer(r"(?<![a-z])" + re.escape(frasa) + r"(?![a-z])", teks):
            if any(not (m.end() <= a or m.start() >= b) for item in temuan for a, b in [(item[0], item[1])]):
                continue
            kiri, kanan = _batas_klausa(teks, m.start())
            if _NEGASI.search(teks[kiri:m.start()]):
                continue
            temuan.append((m.start(), m.end(), aksi, frasa, kiri, kanan))
    hasil = []
    for urutan, (awal, akhir, aksi, frasa, kiri, kanan) in enumerate(sorted(temuan)):
        lokal = _cocok_objek(teks, kiri, kanan)
        tujuan = None
        mt = _TUJUAN.search(teks, akhir, kanan)
        if mt:
            nama_tujuan = mt.group(1).strip()
            tujuan = _OBJEK.get(nama_tujuan)
            if tujuan is None:
                tujuan = nama_tujuan.replace(" ", "_") or None
        # Pasien eksplisit: objek sebelum verba pasif/perubahan, atau setelah
        # verba aktif yang memang memiliki objek. Tujuan perjalanan bukan pasien.
        pasien = next((o for o in reversed(lokal) if o[1] <= awal), None)
        if pasien is None and tujuan is None:
            pasien = next((o for o in lokal if o[0] >= akhir), None)
        pelaku = []
        if peran:
            sebelum = teks[kiri:awal]
            for nama in peran:
                kunci = _normal(nama).strip()
                if kunci and re.search(r"(?<![a-z])" + re.escape(kunci) + r"(?![a-z])", sebelum):
                    pelaku.append(nama)
        perubahan = None
        if aksi in _PERUBAHAN and pasien:
            perubahan = {"objek": pasien[2], "keadaan": aksi}
        hasil.append({
            "id": f"beat-{indeks + 1}-peristiwa-{urutan + 1}",
            "aktor": pelaku,
            "aksi": aksi,
            "sasaran": pasien[2] if pasien else None,
            "tujuan": tujuan,
            "perubahan_keadaan": perubahan,
            "bukti_narasi": narasi[awal:akhir],
            "keyakinan": "pola_eksplisit",
        })
    return hasil


def aksi_utama(peristiwa: list[dict]) -> str | None:
    """Pilih aksi pertama yang eksplisit; None berarti jangan mengarang gerakan."""
    return peristiwa[0]["aksi"] if peristiwa else None
