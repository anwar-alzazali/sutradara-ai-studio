"""Pemeriksaan kontinuitas yang netral terhadap genre.

Modul ini hanya membandingkan identitas stabil pada kartu pemeran dengan atribut
yang dipakai per shot. Aturan cara tokoh ditampilkan tetap menjadi tanggung jawab
paket genre.
"""
from __future__ import annotations

from typing import Any

from .penjaga import Temuan


_KUNCI_IDENTITAS = {
    "jenis": "jenis",
    "usia": "usia",
    "zaman": "zaman",
    "indeks": "indeks",
    "warna_kulit": "warna_kulit",
    "warna_baju": "warna_baju",
    "warna_aksen": "warna_aksen",
    "rambut": "rambut",
    "janggut": "janggut",
    "warna_janggut": "warna_janggut",
    "aksesori": "aksesori",
    "suara": "suara",
    "ciri_wajah": "ciri_wajah",
    "kepala": "penutup_kepala",
}



def periksa_kedekatan_pelaku(
    *,
    visual_x: float,
    visual_y: float,
    setengah_lebar: float,
    pelaku: list[tuple[str, str, float, float]],
    tokoh_lain: list[tuple[str, float, float]],
    jarak_maks: float,
    pita_kedalaman: float,
    label_visual: str,
    lokasi: str,
) -> list[Temuan]:
    """Periksa kedekatan pelaku terhadap objek dengan geometri netral-genre.

    Koordinat dan ukuran visual diberikan oleh pemanggil; inti tidak mengetahui
    nama benda, kategori tokoh, atau cara representasi karakter.
    """
    def jarak_tepi(x: float) -> float:
        return max(0.0, abs(x - visual_x) - setengah_lebar)

    hasil: list[Temuan] = []
    jarak_pelaku = {pid: jarak_tepi(x) for pid, _nama, x, _y in pelaku}
    jauh = [(pid, nama) for pid, nama, x, _y in pelaku
            if jarak_tepi(x) > jarak_maks]
    if jauh:
        nama = ", ".join(n for _pid, n in jauh)
        hasil.append(Temuan(
            "PERIKSA", "PELAKU_JAUH",
            f"{lokasi}: {nama} berbuat pada {label_visual} tetapi terlalu jauh dari tepinya",
        ))

    if jarak_pelaku:
        terdekat = min(jarak_pelaku.values())
        lebih_dekat = [
            pid for pid, x, y in tokoh_lain
            if jarak_tepi(x) + 1 < terdekat
            and abs(y - visual_y) < pita_kedalaman
        ]
        if lebih_dekat:
            hasil.append(Temuan(
                "PERIKSA", "BUKAN_PELAKU_DEKAT",
                f"{lokasi}: {len(lebih_dekat)} tokoh non-pelaku lebih dekat ke "
                f"{label_visual} daripada pelaku terdekat",
            ))
    return hasil

def periksa_kontinuitas_identitas(rencana: dict[str, Any]) -> list[Temuan]:
    """Tandai pemeran yang tidak terdaftar dan perubahan ciri stabil antar-shot.

    Peran kolektif tidak dibandingkan dengan satu identitas contoh. Individu
    dalam kelompok tetap diaudit melalui pemeran_id yang stabil.
    """
    hasil: list[Temuan] = []
    peta_peran = {p["id"]: p for p in rencana.get("peran", [])}
    kartu_pemeran = {p["id"]: p for p in rencana.get("pemeran", [])}
    kartu = {pid: p.get("identitas", {}) for pid, p in peta_peran.items()}
    kartu.update({pid: p.get("identitas", {}) for pid, p in kartu_pemeran.items()})

    for bi, beat in enumerate(rencana.get("beat", [])):
        for si, shot in enumerate(beat.get("shot", [])):
            for tokoh in shot.get("tokoh", []):
                pid = tokoh.get("pemeran_id") or tokoh.get("peran")
                if tokoh.get("pemeran_id") and pid not in kartu_pemeran:
                    hasil.append(Temuan(
                        "GAGAL",
                        "PEMERAN_TAK_TERDAFTAR",
                        f"beat {bi} shot {si}: pemeran_id {pid!r} tidak memiliki kartu identitas",
                    ))
                    continue

                id_peran = tokoh.get("peran")
                definisi_peran = peta_peran.get(id_peran, {})
                if not tokoh.get("pemeran_id") and definisi_peran.get("kolektif", False):
                    identitas = {}
                else:
                    identitas = kartu.get(pid) or {}
                if not identitas:
                    continue

                beda = [
                    (field, identitas[acuan], tokoh[field])
                    for field, acuan in _KUNCI_IDENTITAS.items()
                    if field in tokoh and acuan in identitas and tokoh[field] != identitas[acuan]
                ]
                if beda:
                    rincian = ", ".join(f"{field}: {lama!r} -> {baru!r}" for field, lama, baru in beda)
                    hasil.append(Temuan(
                        "PERIKSA",
                        "IDENTITAS_BERUBAH",
                        f"beat {bi} shot {si} {pid}: ciri kartu pemeran berubah ({rincian}); "
                        "perbarui kartu hanya bila perubahan memang menjadi desain baru",
                    ))
    return hasil


def periksa_kontinuitas_barang(rencana: dict[str, Any]) -> list[Temuan]:
    """Periksa invarians barang lintas-shot tanpa asumsi kategori atau genre.

    Kepemilikan hanya berubah melalui pasangan aksi ulurkan/terima. Pemeriksaan
    ini tidak menentukan bagaimana pemilik divisualkan atau apakah ia hadir
    sebagai tubuh, cahaya, maupun representasi lain.
    """
    hasil: list[Temuan] = []
    sebelumnya: dict[str, dict[str, Any]] = {}
    peran = {p["id"]: p for p in rencana.get("peran", [])}
    for bi, beat in enumerate(rencana.get("beat", [])):
        for si, shot in enumerate(beat.get("shot", [])):
            lokasi = f"beat {bi} shot {si}"
            sekarang: dict[str, dict[str, Any]] = {}
            for item in shot.get("barang", []):
                iid, pemilik = item.get("id"), item.get("pemilik")
                if not iid or iid in sekarang:
                    hasil.append(Temuan("GAGAL", "ID_BARANG",
                                        f"{lokasi}: id barang kosong atau duplikat ({iid})"))
                    continue
                sekarang[iid] = item
                if pemilik not in peran:
                    hasil.append(Temuan("GAGAL", "PEMILIK_BARANG",
                                        f"{lokasi}: pemilik {pemilik!r} tidak terdaftar"))
                    continue
                if item.get("tangan", "ka") not in {"ka", "ki"}:
                    hasil.append(Temuan("GAGAL", "TANGAN_BARANG",
                                        f"{lokasi} {iid}: tangan harus ka/ki"))
                aksi = item.get("aksi", "pegang")
                if aksi in {"ulurkan", "terima"}:
                    titik = item.get("titik_serah")
                    if not titik or len(titik) != 2:
                        hasil.append(Temuan("GAGAL", "TITIK_SERAH_BARANG",
                                            f"{lokasi} {iid}: aksi {aksi} perlu titik_serah [x,y]"))
                    pasangan = item.get("penerima") if aksi == "ulurkan" else item.get("pemberi")
                    if pasangan not in peran:
                        hasil.append(Temuan("GAGAL", "PASANGAN_SERAH_TERIMA",
                                            f"{lokasi} {iid}: pasangan serah-terima tidak terdaftar"))
                if iid in sebelumnya:
                    lama = sebelumnya[iid]
                    pemilik_lama = lama.get("pemilik")
                    if pemilik_lama != pemilik:
                        sah = (lama.get("aksi") == "ulurkan" and lama.get("penerima") == pemilik
                               and aksi == "terima" and item.get("pemberi") == pemilik_lama)
                        if not sah:
                            hasil.append(Temuan("GAGAL", "PEMILIK_BARANG_BERUBAH",
                                                f"{lokasi} {iid}: pemilik berubah {pemilik_lama} -> {pemilik} tanpa pasangan ulurkan/terima"))
                elif aksi == "terima":
                    hasil.append(Temuan("PERIKSA", "BARANG_TANPA_ADEGAN_ULUR",
                                        f"{lokasi} {iid}: adegan terima tidak punya shot ulurkan sebelumnya"))
            for iid in sebelumnya:
                if iid not in sekarang:
                    hasil.append(Temuan("PERIKSA", "BARANG_TIDAK_DIBAWA",
                                        f"{lokasi}: barang {iid} dari shot sebelumnya tidak dicantumkan; periksa kesinambungan"))
            sebelumnya = sekarang
    return hasil
