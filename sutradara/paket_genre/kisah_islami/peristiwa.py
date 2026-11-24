"""Ekstraksi peristiwa narasi untuk keputusan visual yang dapat ditelusuri.

Parser ini sengaja konservatif: hanya mengenali pola bahasa yang eksplisit. Ia tidak
menyimpulkan fakta, sebab-akibat, atau perubahan benda yang tidak disebut naskah.
"""
from __future__ import annotations

import re
import unicodedata


def _normal(teks: str) -> str:
    teks = unicodedata.normalize("NFKD", str(teks).lower())
    return "".join(c for c in teks if not unicodedata.combining(c))


# Urutan terpanjang lebih dulu agar "melarikan diri" tidak dipotong menjadi "lari".
_AKSI = {
    "melarikan diri": "lari", "berjalan": "jalan", "berlari": "lari", "lari": "lari", "bangkit": "bangkit",
    "menjauh": "menjauh", "menjauhi": "menjauh", "mendekat": "mendekat",
    "mendekati": "mendekat", "menghampiri": "mendekat",
    "membangun": "membangun", "dibangun": "membangun", "membuat": "membangun",
    "menyelesaikan": "selesai", "selesai": "selesai", "rampung": "selesai",
    "menggali": "menggali", "digali": "menggali",
    "mengejek": "mengejek", "mengolok": "mengejek", "tertawa": "tertawa",
    "berdoa": "berdoa", "memohon": "berdoa", "menyerahkan": "menyerahkan",
    "memberikan": "menyerahkan", "mengulurkan": "menyerahkan", "menerima": "menerima",
    "berkumpul": "berkumpul", "berhimpun": "berkumpul", "terkumpul": "berkumpul", "berkeringat": "berkeringat", "tenggelam": "tenggelam", "seluruh manusia": "berkumpul",
    "terbelah": "terbelah", "membelah": "terbelah", "retak": "retak", "terpecah": "retak",
    "runtuh": "runtuh", "roboh": "runtuh", "hancur": "runtuh",
    "terbuka": "terbuka", "membuka": "terbuka", "terangkat": "terangkat",
    "mengangkat": "terangkat", "surut": "surut", "mengering": "surut",
    "didekatkan": "mendekat", "mendekatkan": "mendekat",
    "terbit": "muncul", "muncul": "muncul", "datang": "datang",
    "pergi": "pergi", "jatuh": "jatuh", "terjatuh": "jatuh",
    "berbicara": "berbicara", "menyeru": "berbicara", "berkata": "berbicara",
    "menjawab": "berbicara", "menunjuk": "menunjuk", "menuding": "menunjuk",
}
_OBJEK = {
    "bahtera": ("bahtera", "bahtera"), "kapal": ("bahtera", "bahtera"),
    "dinding": ("dinding", "dinding"), "kota": ("kota", "kota"),
    "permukiman": ("permukiman", "permukiman"), "bumi": ("bumi", "bumi"),
    "tanah": ("bumi", "bumi"), "matahari": ("matahari", "matahari"),
    "manusia": ("kerumunan", "kerumunan"), "kerumunan": ("kerumunan", "kerumunan"),
    "keringat": ("keringat", "keringat"), "keringatnya": ("keringat", "keringat"), "danau": ("danau", "danau"),
    "sungai": ("sungai", "sungai"), "pintu": ("pintu", "pintu"),
    "langit": ("langit", "langit"), "gunung": ("gunung", "gunung"),
    "air": ("air", "air"), "api": ("api", "api"),
}
_NEGASI = re.compile(r"\b(?:tidak|tak|belum|bukan|jangan)(?:\s+(?:akan|pernah|lagi|dapat|bisa|mau|berhasil|jadi|juga))?\s+$")


def analisis_peristiwa(narasi: str, peran: list[str] | None = None, indeks: int = 0) -> list[dict]:
    """Kembalikan peristiwa eksplisit dari satu beat, beserta bukti teks sumber."""
    teks = _normal(narasi)
    temuan: list[tuple[int, int, str, str]] = []
    for frasa, aksi in sorted(_AKSI.items(), key=lambda item: len(item[0]), reverse=True):
        pola = re.compile(r"(?<![a-z])" + re.escape(frasa) + r"(?![a-z])")
        for cocok in pola.finditer(teks):
            if _NEGASI.search(teks[max(0, cocok.start() - 18):cocok.start()]):
                continue
            if any(not (cocok.end() <= a or cocok.start() >= b) for a, b, _, _ in temuan):
                continue
            temuan.append((cocok.start(), cocok.end(), aksi, frasa))
    objek = []
    for nama, (jenis, id_objek) in sorted(_OBJEK.items(), key=lambda item: len(item[0]), reverse=True):
        m = re.search(r"(?<![a-z])" + re.escape(nama) + r"(?![a-z])", teks)
        if m:
            objek.append((m.start(), jenis, id_objek, nama))
    # Kehadiran peran dalam beat bukan bukti bahwa ia pelaku. Isi aktor hanya
    # bila nama/peran benar-benar disebut sebagai token dalam kalimat sumber.
    aktor_eksplisit = []
    for nama in peran or []:
        kunci = _normal(nama).strip()
        if kunci and re.search(r"(?<![a-z])" + re.escape(kunci) + r"(?![a-z])", teks):
            aktor_eksplisit.append(nama)

    hasil = []
    for urutan, (awal, akhir, aksi, frasa) in enumerate(sorted(temuan)):
        target = next((o for o in objek if o[0] >= akhir), None)
        if target is None and objek:
            target = min(objek, key=lambda o: abs(o[0] - awal))
        # Tujuan perpindahan bukan sasaran aksi/transitif. Pisahkan relasi
        # "berjalan menuju X" dari aksi yang mengubah X.
        tujuan = None
        if aksi in {"jalan", "lari", "mendekat", "menjauh"} and target:
            penghubung = teks[akhir:target[0]]
            if re.search(r"\b(?:menuju|ke arah|ke)\b", penghubung):
                tujuan = target[2]
                target = None
        perubahan = None
        if aksi in {"terbelah", "retak", "runtuh", "terbuka", "surut", "terangkat", "muncul", "jatuh"} and target:
            perubahan = {"objek": target[2], "keadaan": aksi}
        hasil.append({
            "id": f"beat-{indeks + 1}-peristiwa-{urutan + 1}",
            "aktor": list(aktor_eksplisit),
            "aksi": aksi,
            "sasaran": target[2] if target else None,
            "tujuan": tujuan,
            "perubahan_keadaan": perubahan,
            "bukti_narasi": narasi[awal:akhir],
            "keyakinan": "pola_eksplisit",
        })
    return hasil


def aksi_utama(peristiwa: list[dict]) -> str | None:
    """Pilih aksi pertama yang eksplisit; None berarti jangan mengarang gerakan."""
    return peristiwa[0]["aksi"] if peristiwa else None
