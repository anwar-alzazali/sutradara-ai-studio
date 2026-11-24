"""Renderer karakter generik dengan RANGKA BERSENDI.

Tubuh dihitung dari sudut sendi (sutradara/gerak.py): panggul, badan, kepala, lengan atas/bawah, paha/betis.
Gamis mengikuti bahu-pinggul-lutut sehingga ikut berayun saat berjalan/berlari dan menjuntai saat duduk.
Mode tampil: "pakaian" (bawaan) atau "siluet" (bentuk sama, gelap, tepi tersinari dari kiri, tanpa wajah).
Jenis: "pria" (janggut, imamah/kain/kopiah) atau "wanita" (kerudung, tanpa janggut).
Wajah: datar, senyum, tertawa, ejek, cemberut, sedih, marah, takut, kaget, pejam (+ kedip otomatis, mulut bicara).

Pilihan gaya wajah dan aksesori diberikan oleh pemanggil; aturan kategori dan adab tetap menjadi tanggung jawab paket genre.
"""
from __future__ import annotations

import math
from typing import Callable

from .. import gerak as G

KULIT = ["#c98b62", "#a86a45", "#d9a07a", "#8d5a3b", "#b97a52"]
BAJU = [("#7a3b2e", "#d9b26a"), ("#3f5a6b", "#c9b48a"), ("#6b5a2e", "#e0d2b0"),
        ("#4b3a5e", "#c99a5a"), ("#2f4a3a", "#d6c08e"), ("#8a5a2a", "#f0e2c0")]
KERUDUNG = ["#5a3a5e", "#2e4a5a", "#6a3a32", "#3a4a3a", "#7a6a4a"]
CELANA = "#d9ccb0"
GELAP = "#150f1d"
RAMBUT = "#2a1b14"

PAHA, BETIS, BADAN, LENGAN_A, LENGAN_B, R_KEPALA = 78, 74, 110, 64, 58, 34
WAJAH = ("datar", "senyum", "tertawa", "ejek", "cemberut", "sedih", "marah", "takut", "kaget", "pejam",
         "kepergok_panik", "jijik_ilfil", "sinis", "curiga", "heran")
WAJAH_DASAR = {
    "kepergok_panik": "takut",
    "jijik_ilfil": "cemberut",
    "sinis": "ejek",
    "curiga": "datar",
    "heran": "datar",
}
EKSPRESI_DETAIL = {
    "kepergok_panik": {"kelopak": -0.9, "lirikan": 0.0, "alis_dalam": -1.0, "alis_luar": 0.15, "alis_rapat": 0.15, "kerut_hidung": 0.65, "mulut_bulat": 0.9},
    "jijik_ilfil": {"kelopak": 0.35, "lirikan": -0.2, "alis_dalam": 0.65, "alis_luar": 0.35, "alis_rapat": 0.9, "kerut_hidung": 1.0, "mulut_bulat": 0.0},
    "sinis": {"kelopak": 0.4, "lirikan": 0.65, "alis_dalam": 0.15, "alis_luar": -0.7, "alis_rapat": 0.1, "kerut_hidung": 0.0, "mulut_bulat": 0.0},
    "curiga": {"kelopak": 0.55, "lirikan": 0.8, "alis_dalam": 0.25, "alis_luar": -0.35, "alis_rapat": 0.35, "kerut_hidung": 0.25, "mulut_bulat": 0.0},
    "heran": {"kelopak": -0.45, "lirikan": 0.0, "alis_dalam": -0.85, "alis_luar": -0.85, "alis_rapat": 0.0, "kerut_hidung": 0.0, "mulut_bulat": 0.45},
}
KEPALA = ("imamah", "kain", "kopiah", "kerudung", "tanpa")
POSE = G.SEMUA  # nama gerak yang sah (termasuk pose lama: tunjuk, tertawa, silang, angkat, kaget, mundur, tutup, berdiri)


def _balik_pada(balik, t: float) -> bool:
    """Nilai orientasi kiri/kanan dari bool tetap atau jadwal keyframe."""
    if isinstance(balik, bool):
        return balik
    jadwal = sorted((float(a), bool(v)) for a, v in balik)
    aktif = False
    for waktu, nilai in jadwal:
        if t < waktu:
            break
        aktif = nilai
    return aktif


def _arah_derajat(arah, t: float) -> float:
    """Sudut depan/samping/belakang dengan interpolasi smoothstep."""
    sudut = {"depan": 0.0, "tiga_perempat": 45.0, "samping": 90.0, "tiga_perempat_belakang": 135.0, "belakang": 180.0}
    if isinstance(arah, str):
        if arah not in sudut:
            raise ValueError("arah harus depan, samping, atau belakang")
        return sudut[arah]
    jadwal = sorted((float(a), sudut[b]) for a, b in arah)
    if not jadwal:
        return 0.0
    if t <= jadwal[0][0]:
        return jadwal[0][1]
    for (a, v), (b, w) in zip(jadwal, jadwal[1:]):
        if t <= b:
            u = max(0.0, min(1.0, (t-a)/max(b-a, 1e-9)))
            u = u*u*(3-2*u)
            return v + (w-v)*u
    return jadwal[-1][1]


def _ruas(x, y, sudut, panjang, sisi, pendek=1.0):
    r = math.radians(sudut)
    return x + sisi * math.sin(r) * panjang * pendek, y + math.cos(r) * panjang * pendek


def _alat(jenis: str, siku, tangan, warna=None) -> str:
    """Gagang searah lengan bawah (diteruskan dari tangan), kepala alat tegak lurus di ujung gagang."""
    (sx, sy), (tx, ty) = siku, tangan
    dx, dy = tx - sx, ty - sy; n = math.hypot(dx, dy) or 1; ux, uy = dx / n, dy / n
    gagang = 62 if jenis == "palu" else 92
    ex, ey = tx + ux * gagang, ty + uy * gagang
    px, py = -uy, ux  # tegak lurus
    kayu, besi = (warna, warna) if warna else ("#7a4f2a", "#5d6270")
    if jenis == "palu":
        kep = f'<path d="M{ex - px * 20:.1f} {ey - py * 20:.1f} L{ex + px * 14:.1f} {ey + py * 14:.1f}" stroke="{besi}" stroke-width="20" stroke-linecap="round"/>'
    else:  # beliung: mata melengkung runcing ke dua arah
        kep = (f'<path d="M{ex - px * 42 + ux * 10:.1f} {ey - py * 42 + uy * 10:.1f} Q {ex - ux * 6:.1f} {ey - uy * 6:.1f} '
               f'{ex + px * 42 + ux * 10:.1f} {ey + py * 42 + uy * 10:.1f}" fill="none" stroke="{besi}" stroke-width="11" stroke-linecap="round"/>')
    return (f'<path d="M{tx - ux * 10:.1f} {ty - uy * 10:.1f} L{ex:.1f} {ey:.1f}" stroke="{kayu}" stroke-width="9" stroke-linecap="round"/>' + kep)


def _putar(dx, dy, derajat):
    r = math.radians(derajat)
    return dx * math.cos(r) - dy * math.sin(r), dx * math.sin(r) + dy * math.cos(r)


def _wajah(jenis: str, bicara: float, kedip: bool, wanita: bool, ox: float, oy: float,
           profil: bool = False, janggut: str = "pendek", warna_janggut: str | None = None,
           detail_wajah: dict | None = None) -> list[str]:
    # Peta lokal menjaga renderer tetap mandiri saat dipanggil dari jalur impor alternatif.
    preset_detail = {
        "kepergok_panik": {"kelopak": -0.9, "lirikan": 0.0, "alis_dalam": -1.0, "alis_luar": 0.15, "alis_rapat": 0.15, "kerut_hidung": 0.65, "mulut_bulat": 0.9},
        "jijik_ilfil": {"kelopak": 0.35, "lirikan": -0.2, "alis_dalam": 0.65, "alis_luar": 0.35, "alis_rapat": 0.9, "kerut_hidung": 1.0, "mulut_bulat": 0.0},
        "sinis": {"kelopak": 0.4, "lirikan": 0.65, "alis_dalam": 0.15, "alis_luar": -0.7, "alis_rapat": 0.1, "kerut_hidung": 0.0, "mulut_bulat": 0.0},
        "curiga": {"kelopak": 0.55, "lirikan": 0.8, "alis_dalam": 0.25, "alis_luar": -0.35, "alis_rapat": 0.35, "kerut_hidung": 0.25, "mulut_bulat": 0.0},
        "heran": {"kelopak": -0.45, "lirikan": 0.0, "alis_dalam": -0.85, "alis_luar": -0.85, "alis_rapat": 0.0, "kerut_hidung": 0.0, "mulut_bulat": 0.45},
    }
    detail = dict(preset_detail.get(jenis, {}))
    detail.update(detail_wajah or {})
    jenis = {"kepergok_panik": "takut", "jijik_ilfil": "cemberut", "sinis": "ejek",
             "curiga": "datar", "heran": "datar"}.get(jenis, jenis)
    W, M = RAMBUT, "#5a1e1e"
    warna_janggut = warna_janggut or W
    bentuk_janggut = {
        "tanpa": "",
        "tipis": f'<path d="M-24 16 Q 0 45 24 16 Q 18 31 0 33 Q -18 31 -24 16Z" fill="{warna_janggut}" opacity=".72"/>',
        "pendek": f'<path d="M-30 14 Q 0 60 30 14 Q 26 36 0 42 Q -26 36 -30 14Z" fill="{warna_janggut}"/>',
        "panjang": f'<path d="M-30 14 Q 0 60 30 14 L24 48 Q 0 72 -24 48Z" fill="{warna_janggut}"/>',
    }
    if janggut not in bentuk_janggut:
        raise ValueError("janggut harus tanpa, tipis, pendek, atau panjang")
    g = [] if wanita else ([bentuk_janggut[janggut]] if bentuk_janggut[janggut] else [])
    if wanita:
        g.append('<ellipse cx="-17" cy="10" rx="6" ry="3.5" fill="#e07a6a" opacity=".35"/><ellipse cx="17" cy="10" rx="6" ry="3.5" fill="#e07a6a" opacity=".35"/>')
    e = lambda s: f'<g transform="translate({ox:.1f},{oy:.1f})">{s}</g>'
    mata_tutup = '<path d="M-17 -6 q 6 4 12 0 M5 -6 q 6 4 12 0" stroke="{W}" stroke-width="3.5" fill="none" stroke-linecap="round"/>'.replace("{W}", W)
    mata_titik = f'<circle cx="-11" cy="-6" r="4.5" fill="{W}"/><circle cx="11" cy="-6" r="4.5" fill="{W}"/>'
    mata_besar = (f'<circle cx="-12" cy="-6" r="7" fill="#fff"/><circle cx="12" cy="-6" r="7" fill="#fff"/>'
                  f'<circle cx="-12" cy="-5" r="3.5" fill="{W}"/><circle cx="12" cy="-5" r="3.5" fill="{W}"/>')
    alis = {
        "datar": "M-18 -17 h12 M18 -17 h-12", "senyum": "M-18 -17 q 6 -3 12 0 M18 -17 q -6 -3 -12 0",
        "tertawa": "M-18 -18 q 6 -4 12 0 M18 -18 q -6 -4 -12 0", "ejek": "M-18 -15 l 12 3 M18 -21 l -12 3",
        "cemberut": "M-18 -19 l 12 4 M18 -19 l -12 4", "sedih": "M-18 -14 l 12 -5 M18 -14 l -12 -5",
        "marah": "M-19 -22 l 13 8 M19 -22 l -13 8", "takut": "M-18 -18 l 12 -4 M18 -18 l -12 -4",
        "kaget": "M-18 -24 q 6 -4 12 0 M18 -24 q -6 -4 -12 0", "pejam": "M-18 -16 h12 M18 -16 h-12",
    }[jenis]
    if jenis in ("tertawa", "pejam"):
        mata = mata_tutup if jenis == "pejam" else f'<path d="M-17 -5 q 6 -7 12 0 M5 -5 q 6 -7 12 0" stroke="{W}" stroke-width="4" fill="none" stroke-linecap="round"/>'
    elif jenis in ("takut", "kaget"):
        mata = mata_besar if not kedip else mata_tutup
    elif jenis == "marah":
        mata = mata_tutup.replace("q 6 4 12 0", "h12") if kedip else f'<path d="M-17 -6 h11 M6 -6 h11" stroke="{W}" stroke-width="5" stroke-linecap="round"/>'
    else:
        mata = mata_tutup if kedip else mata_titik
    if profil:
        mata = f'<path d="M-17 -7 Q -9 -14 -2 -7 Q -9 0 -17 -7Z" fill="#fff"/><circle cx="-9" cy="-7" r="3" fill="{W}"/>'
        alis = "M-19 -18 Q -10 -23 -2 -17"
    buka = max(0.0, min(1.0, bicara))
    mulut = {
        "datar": f'<path d="M-9 16 h18" stroke="{M}" stroke-width="3.5" stroke-linecap="round"/>',
        "senyum": f'<path d="M-12 13 Q 0 24 12 13" stroke="{M}" stroke-width="3.5" fill="none" stroke-linecap="round"/>',
        "tertawa": f'<path d="M-14 12 Q 0 32 14 12Z" fill="{M}"/><path d="M-10 13 h20" stroke="#fff" stroke-width="3"/>',
        "ejek": f'<path d="M-11 17 Q 2 22 14 11" stroke="{M}" stroke-width="3.5" fill="none" stroke-linecap="round"/>',
        "cemberut": f'<path d="M-10 20 Q 0 13 10 20" stroke="{M}" stroke-width="3.5" fill="none" stroke-linecap="round"/>',
        "sedih": f'<path d="M-11 21 Q 0 12 11 21" stroke="{M}" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
                 '<path d="M-14 0 q -2 8 0 10" stroke="#8fc0f0" stroke-width="3" fill="none"/>',
        "marah": f'<path d="M-13 18 h26 v4 h-26Z" fill="{M}"/><path d="M-12 19.5 h24" stroke="#fff" stroke-width="2"/>',
        "takut": f'<ellipse cx="0" cy="18" rx="7" ry="9" fill="{M}"/>',
        "kaget": f'<ellipse cx="0" cy="19" rx="9" ry="11" fill="{M}"/>',
        "pejam": f'<path d="M-8 16 h16" stroke="{M}" stroke-width="3.5" stroke-linecap="round"/>',
    }[jenis]
    if buka > 0.05 and jenis not in ("tertawa", "takut", "kaget"):
        mulut = f'<ellipse cx="0" cy="17" rx="{8 + 2 * buka:.1f}" ry="{1.5 + 7 * buka:.1f}" fill="{M}"/>'
    hidung = '<path d="M1 -5 L10 4 L2 7" stroke="#704631" stroke-width="2.5" fill="none" stroke-linecap="round"/>' if profil else ""
    g.append(e(mata + f'<path d="{alis}" stroke="{W}" stroke-width="3.5" fill="none" stroke-linecap="round"/>' + hidung + mulut))
    if detail:
        # Lapisan mikro menambah kendali mata dan alis tanpa mengubah ekspresi lama.
        kelopak = max(-1.0, min(1.0, float(detail.get("kelopak", 0.0))))
        lirikan = max(-1.0, min(1.0, float(detail.get("lirikan", 0.0))))
        dalam = max(-1.0, min(1.0, float(detail.get("alis_dalam", 0.0))))
        luar = max(-1.0, min(1.0, float(detail.get("alis_luar", 0.0))))
        rapat = max(0.0, min(1.0, float(detail.get("alis_rapat", 0.0))))
        kerut = max(0.0, min(1.0, float(detail.get("kerut_hidung", 0.0))))
        bulat = max(0.0, min(1.0, float(detail.get("mulut_bulat", 0.0))))
        tinggi_mata = 5.0 + (1.0 - kelopak) * 3.0
        pupil_x = 3.5 * lirikan
        mata_halus = (f'<ellipse cx="-11" cy="-6" rx="7.5" ry="{tinggi_mata:.1f}" fill="#fff"/>'
                      f'<ellipse cx="11" cy="-6" rx="7.5" ry="{tinggi_mata:.1f}" fill="#fff"/>'
                      f'<circle cx="{-11 + pupil_x:.1f}" cy="-6" r="3.4" fill="{W}"/>'
                      f'<circle cx="{11 + pupil_x:.1f}" cy="-6" r="3.4" fill="{W}"/>')
        rapat_y = rapat * 3.5
        alis_halus = (f'<path d="M-19 {-17 + luar * 5 + rapat_y:.1f} L-6 {-17 + dalam * 5 + rapat_y:.1f} '
                      f'M6 {-17 + dalam * 5 + rapat_y:.1f} L19 {-17 + luar * 5 + rapat_y:.1f}" '
                      f'stroke="{W}" stroke-width="3.8" fill="none" stroke-linecap="round"/>')
        kerut_svg = (f'<path d="M-7 2 l-4 5 M0 1 l0 6 M7 2 l4 5" stroke="#704631" '
                     f'stroke-width="{1.2 + 1.8 * kerut:.1f}" opacity="{kerut:.2f}" stroke-linecap="round"/>')
        mulut_svg = (f'<ellipse cx="0" cy="17" rx="{3 + 6 * bulat:.1f}" ry="{2 + 7 * bulat:.1f}" '
                     f'fill="{M}" opacity="{max(bulat, buka):.2f}"/>') if bulat > 0 else ""
        g.append(e(mata_halus + alis_halus + kerut_svg + mulut_svg))
    return g


def _lapisan_rambut(model: str, warna: str, *, profil: bool, membelakangi: bool) -> str:
    """Rambut kepala prosedural; geometri mengikuti sudut kamera, bukan warna saja."""
    if model == "botak":
        return ""
    if membelakangi:
        bentuk = {
            "pendek": "M-34 -5 Q-43 -48 0 -50 Q43 -48 34 -5 Q22 9 0 8 Q-22 9 -34 -5Z",
            "ikal": "M-37 -8 Q-48 -50 -27 -43 Q-20 -58 -7 -48 Q8 -59 17 -47 Q38 -55 43 -31 Q47 -5 34 3 Q0 17 -34 3Z",
            "panjang": "M-35 -8 Q-44 -50 0 -51 Q44 -50 35 -8 L42 55 Q20 68 14 48 L0 58 L-14 48 Q-20 68 -42 55Z",
        }[model]
    elif profil:
        bentuk = {
            "pendek": "M-31 -10 Q-38 -45 0 -49 Q25 -47 32 -20 L22 -17 Q8 -30 -8 -26 L-20 -7Z",
            "ikal": "M-34 -10 Q-43 -38 -27 -43 Q-22 -56 -8 -46 Q5 -58 15 -45 Q35 -46 34 -20 L22 -15 Q8 -31 -8 -25 L-21 -5Z",
            "panjang": "M-32 -9 Q-42 -45 0 -50 Q30 -46 33 -16 L25 45 Q14 52 12 28 L-18 34 L-25 6Z",
        }[model]
    else:
        bentuk = {
            "pendek": "M-34 -8 Q-42 -48 0 -51 Q42 -48 34 -8 L23 -16 Q0 -27 -23 -16Z",
            "ikal": "M-36 -7 Q-47 -38 -31 -43 Q-25 -59 -10 -47 Q2 -61 15 -47 Q36 -55 40 -31 L34 -6 L23 -17 Q0 -28 -23 -17Z",
            "panjang": "M-35 -8 Q-44 -48 0 -51 Q44 -48 35 -8 L39 50 Q24 59 20 38 L-20 38 Q-24 59 -39 50Z",
        }[model]
    return f'<path d="{bentuk}" fill="{warna}"/>'



def orang(x: float, y: float, s: float = 1.0, *, gerak=None, pose: str | None = None, t: float = 0.0, indeks: int = 0,
          mode: str = "pakaian", kepala: str | None = None, jenis: str = "pria", wajah="datar", bicara=None,
          rinci: bool = True, balik: bool = False, alat: str | None = None, arah='depan', usia='dewasa', zaman='arab_kuno',
          wajah_cahaya: bool = False, barang: list[dict] | None = None,
          target_tangan: dict | None = None, detail_wajah: dict | None = None, warna_kulit: str | None = None,
          warna_baju: str | None = None, warna_aksen: str | None = None,
          rambut: str | None = None, model_rambut: str = "pendek", janggut: str = "pendek",
          warna_janggut: str | None = None, gambar_item: Callable[..., str] | None = None) -> str:
    """Satu tokoh, kaki di (x, y), tinggi ±360 px pada s=1. `gerak`/`wajah` boleh jadwal [[detik, nama], ...];
    `bicara` = daftar [mulai, akhir] (detik) saat mulut bergerak. `pose` = nama lama untuk `gerak`.
    `alat` = "palu" | "beliung" di tangan kanan; bawaan otomatis bila jadwal gerak memuat palu/gali."""
    if mode not in ("pakaian", "siluet"):
        raise ValueError("mode harus 'pakaian' atau 'siluet'")
    sp = gerak if gerak is not None else (pose or "berdiri")
    if isinstance(sp, str) and sp not in G.SEMUA:
        raise ValueError(f"gerak/pose tak dikenal: {sp} (pilihan: {', '.join(G.SEMUA)})")
    J = G.pada(sp, t)
    if usia == "lansia":
        J = dict(J)
        J["tubuh"] += 5.0
        J["kepala"] += 2.0
    if alat is None:
        nama_gerak = [sp] if isinstance(sp, str) else [b for _, b in sp]
        alat = "beliung" if "gali" in nama_gerak else ("palu" if "palu" in nama_gerak else None)
    wanita = jenis == "wanita"
    kepala = kepala or ("kerudung" if wanita else "imamah")
    sudut = _arah_derajat(arah, t)
    balik_aktif = _balik_pada(balik, t)
    proyeksi = 0.55 + 0.45 * abs(math.cos(math.radians(sudut)))
    tampak_wajah = max(0.0, min(1.0, (105.0 - abs(sudut)) / 40.0))
    membelakangi = abs(sudut) > 135.0
    profil = 60.0 < abs(sudut) <= 135.0
    if usia not in ("anak", "dewasa", "lansia"):
        raise ValueError("usia harus anak, dewasa, atau lansia")
    if zaman not in ("arab_kuno", "mesir_kuno", "umum"):
        raise ValueError("zaman harus arab_kuno, mesir_kuno, atau umum")
    skala_usia = 0.72 if usia == "anak" else (1.04 if usia == "lansia" else 1.0)
    palet_zaman = {"arab_kuno": None, "mesir_kuno": (("#8a6a32", "#e2c36e"), ("#3f6470", "#d7b86a")),
                   "umum": (("#52634a", "#c8b995"), ("#6b526b", "#d7b995"))}
    siluet = mode == "siluet"
    kulit = GELAP if siluet else (warna_kulit or KULIT[indeks % len(KULIT)])
    baju, aksen = (GELAP, GELAP) if siluet else (warna_baju or BAJU[indeks % len(BAJU)][0],
                                                  warna_aksen or BAJU[indeks % len(BAJU)][1])
    if not siluet and palet_zaman[zaman]:
        baju, aksen = palet_zaman[zaman][indeks % 2]
    celana = GELAP if siluet else CELANA

    # --- rangka ---
    py = -(PAHA + BETIS) - 6 + J["naik"]
    px = J["geser"]
    pinggul = {+1: (px + 20, py), -1: (px - 20, py)}
    lutut, mata_kaki = {}, {}
    for sisi, k in ((+1, "ka"), (-1, "ki")):
        hx, hy = pinggul[sisi]
        lutut[sisi] = _ruas(hx, hy, J[f"pa_{k}"], PAHA, sisi, J[f"pf_{k}"])
        mata_kaki[sisi] = _ruas(*lutut[sisi], J[f"ba_{k}"], BETIS, sisi)
    dx, dy = _putar(0, -BADAN, J["tubuh"]); leher = (px + dx, py + dy)
    bahu = {}
    for sisi in (+1, -1):
        bx, by = _putar(sisi * 40, 12, J["tubuh"]); bahu[sisi] = (leher[0] + bx, leher[1] + by)
    # Target serah-terima memakai koordinat dunia; sudut sendi dihitung ulang dengan IK yang sama.
    if target_tangan:
        skala_x = (-1 if balik_aktif else 1) * s * proyeksi * skala_usia
        skala_y = s * skala_usia
        for sisi, k in ((+1, "ka"), (-1, "ki")):
            if k in target_tangan:
                gx, gy = target_tangan[k]
                lx, ly = (gx - x) / skala_x, (gy - y) / skala_y
                dx = (lx - bahu[sisi][0]) * sisi
                dy = ly - bahu[sisi][1]
                J[f"la_{k}"], J[f"sa_{k}"] = G.ik(dx, dy)
    siku, tangan = {}, {}
    for sisi, k in ((+1, "ka"), (-1, "ki")):
        siku[sisi] = _ruas(*bahu[sisi], J[f"la_{k}"] + sisi * 0 - J["tubuh"] * sisi, LENGAN_A, sisi)
        tangan[sisi] = _ruas(*siku[sisi], J[f"sa_{k}"] - J["tubuh"] * sisi, LENGAN_B, sisi)
    kx, ky = _putar(0, -38, J["tubuh"] + J["kepala"]); pk = (leher[0] + kx, leher[1] + ky)

    g = [f'<g transform="translate({x:.1f},{y:.1f}) scale({(-1 if balik_aktif else 1) * s * proyeksi * skala_usia:.4f},{s * skala_usia:.4f})">',
         f'<ellipse cx="{px:.1f}" cy="4" rx="{70 * (1 - min(.5, max(0, -J["naik"]) / 240)):.1f}" ry="12" fill="#000" opacity=".35"/>']
    if J["bangku"] > 0.5:
        g.append(f'<rect x="{px - 72:.1f}" y="{py + 8:.1f}" width="144" height="{-py - 8:.1f}" rx="8" fill="#6b4630"/>'
                 f'<rect x="{px - 80:.1f}" y="{py + 2:.1f}" width="160" height="16" rx="6" fill="#8a5a3a"/>')
    # betis & kaki (celana di bawah gamis)
    for sisi in (+1, -1):
        lx, ly = lutut[sisi]; ax, ay = mata_kaki[sisi]
        g.append(f'<path d="M{lx:.1f} {ly:.1f} L{ax:.1f} {ay:.1f}" stroke="{celana}" stroke-width="22" stroke-linecap="round"/>'
                 f'<ellipse cx="{ax + sisi * 6:.1f}" cy="{ay + 4:.1f}" rx="19" ry="9" fill="#2a1a14"/>')
    # gamis: bahu -> pinggul -> lutut, ujung menjuntai
    hem = max(max(lutut[1][1], lutut[-1][1]) + 30, py + 70)
    kl, kr = lutut[-1][0] - 26, lutut[1][0] + 26
    jubah = (f"M{bahu[-1][0] - 6:.1f} {bahu[-1][1] - 4:.1f} Q {leher[0]:.1f} {leher[1] - 10:.1f} {bahu[1][0] + 6:.1f} {bahu[1][1] - 4:.1f} "
             f"L {pinggul[1][0] + 30:.1f} {py + 6:.1f} L {kr:.1f} {hem:.1f} Q {(kl + kr) / 2:.1f} {hem + 10:.1f} {kl:.1f} {hem:.1f} "
             f"L {pinggul[-1][0] - 30:.1f} {py + 6:.1f} Z")
    g.append(f'<path d="{jubah}" fill="{baju}"/>')
    if not siluet:
        g.append(f'<path d="M{leher[0] - 6:.1f} {leher[1] + 4:.1f} L{leher[0] + 6:.1f} {leher[1] + 4:.1f} L{px + 6:.1f} {hem - 6:.1f} L{px - 6:.1f} {hem - 6:.1f}Z" fill="{aksen}" opacity=".5"/>')
        g.append(f'<path d="M{pinggul[-1][0] - 30:.1f} {py:.1f} Q {px:.1f} {py + 12:.1f} {pinggul[1][0] + 30:.1f} {py:.1f}" stroke="{aksen}" stroke-width="13" fill="none"/>')
        g.append(f'<path d="M{kl + 4:.1f} {hem - 10:.1f} Q {(kl + kr) / 2:.1f} {hem} {kr - 4:.1f} {hem - 10:.1f}" stroke="{aksen}" stroke-width="5" fill="none" opacity=".7"/>')
    # leher & kepala
    sudut_k = J["tubuh"] + J["kepala"]
    g.append(f'<g transform="translate({pk[0]:.1f},{pk[1]:.1f}) rotate({sudut_k:.2f}) scale({1.18 if usia == "anak" else 1.0:.2f})">')
    g.append(f'<rect x="-11" y="20" width="22" height="22" fill="{kulit}"/><circle r="{R_KEPALA}" fill="{kulit}"/>')
    # Rambut menjadi lapisan dasar kepala: terlihat pada kepala terbuka, dan
    # tidak menembus penutup kepala. Fitur wajah tetap dirender paling akhir.
    if not siluet and kepala == "tanpa":
        g.append(_lapisan_rambut(model_rambut, rambut or RAMBUT,
                                 profil=profil, membelakangi=membelakangi))
    if kepala == "kerudung" and not siluet:
        warna_k = KERUDUNG[indeks % len(KERUDUNG)]
        g.append(f'<path d="M-40 6 Q -46 -44 0 -46 Q 46 -44 40 6 L 50 62 Q 0 74 -50 62Z" fill="{warna_k}"/>')
        if not membelakangi:
            g.append(f'<ellipse cx="0" cy="2" rx="28" ry="31" fill="{kulit}"/>')
    tutup = GELAP if siluet else aksen
    if kepala == "imamah":
        g += [f'<path d="M-37 -8 Q -40 -48 0 -52 Q 40 -48 37 -8 Q 0 -20 -37 -8Z" fill="{tutup}"/>',
              f'<path d="M30 -14 Q 46 18 40 52" stroke="{tutup}" stroke-width="12" fill="none" stroke-linecap="round"/>']
    elif kepala == "kain":
        g += [f'<path d="M-40 2 Q -44 -52 0 -54 Q 44 -52 40 2 L 48 60 L 30 48 L 34 -2 Q 0 -22 -34 -2 L -30 48 L -48 60Z" fill="{tutup}"/>',
              f'<path d="M-38 -24 Q 0 -38 38 -24" stroke="{rambut or RAMBUT}" stroke-width="6" fill="none"/>']
    elif kepala == "kopiah":
        g.append(f'<path d="M-30 -20 Q -30 -44 0 -44 Q 30 -44 30 -20Z" fill="{tutup}"/>')
    elif kepala == "kerudung" and siluet:
        g.append(f'<path d="M-40 6 Q -46 -44 0 -46 Q 46 -44 40 6 L 50 62 Q 0 74 -50 62Z" fill="{GELAP}"/>')
    if not siluet and rinci and tampak_wajah > 0.02 and not membelakangi:
        if wajah_cahaya:
            # Mode bercahaya menutup bidang wajah dari depan maupun profil tanpa mengubah rig tubuh.
            lebar_wajah = 22 if profil else 32
            g.append(f'<ellipse cx="{J["toleh"] * 4:.1f}" cy="2" rx="{lebar_wajah}" ry="34" fill="#fff8df" opacity=".96"/>'
                     f'<ellipse cx="{J["toleh"] * 4:.1f}" cy="2" rx="{lebar_wajah + 7}" ry="39" fill="#fff0bd" opacity=".36" filter="url(#b10)"/>')
        else:
            jw = G.nilai_jadwal(wajah, t, "datar")
            if jw not in WAJAH:
                raise ValueError(f"wajah tak dikenal: {jw} (pilihan: {', '.join(WAJAH)})")
            bc = 0.0
            for a, b in (bicara or []):
                if a <= t <= b:
                    bc = 0.5 + 0.5 * math.sin(t * 15)
            kedip = (t + indeks * 0.9) % 3.7 < 0.12
            g += _wajah(jw, bc, kedip, wanita, J["toleh"] * 8, J["angguk"] * 7,
                        profil=profil, janggut=janggut, warna_janggut=warna_janggut, detail_wajah=detail_wajah)
    if not siluet and rinci and tampak_wajah > 0.02 and not membelakangi:
        if wajah_cahaya:
            # Mode bercahaya menutup bidang wajah dari depan maupun profil tanpa mengubah rig tubuh.
            lebar_wajah = 22 if profil else 32
            g.append(f'<ellipse cx="{J["toleh"] * 4:.1f}" cy="2" rx="{lebar_wajah}" ry="34" fill="#fff8df" opacity=".96"/>'
                     f'<ellipse cx="{J["toleh"] * 4:.1f}" cy="2" rx="{lebar_wajah + 7}" ry="39" fill="#fff0bd" opacity=".36" filter="url(#b10)"/>')
        else:
            jw = G.nilai_jadwal(wajah, t, "datar")
            if jw not in WAJAH:
                raise ValueError(f"wajah tak dikenal: {jw} (pilihan: {', '.join(WAJAH)})")
            bc = 0.0
            for a, b in (bicara or []):
                if a <= t <= b:
                    bc = 0.5 + 0.5 * math.sin(t * 15)
            kedip = (t + indeks * 0.9) % 3.7 < 0.12
            g += _wajah(jw, bc, kedip, wanita, J["toleh"] * 8, J["angguk"] * 7,
                        profil=profil, janggut=janggut, warna_janggut=warna_janggut, detail_wajah=detail_wajah)
    g.append("</g>")
    # lengan (digambar SETELAH kepala supaya tangan bisa menutup wajah/mulut/telinga)
    if barang and (siluet or alat):
        raise ValueError("barang genggam tidak boleh digabung dengan siluet atau alat kerja lama")
    for sisi in (+1, -1):
        bx, by = bahu[sisi]; sx, sy = siku[sisi]; tx, ty = tangan[sisi]
        g.append(f'<path d="M{bx:.1f} {by:.1f} L{sx:.1f} {sy:.1f}" stroke="{baju}" stroke-width="26" stroke-linecap="round"/>'
                 f'<path d="M{sx:.1f} {sy:.1f} L{tx:.1f} {ty:.1f}" stroke="{baju}" stroke-width="22" stroke-linecap="round"/>'
                 f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="13" fill="{kulit}"/>')
        if alat and sisi == +1:
            g.insert(len(g) - 1, _alat(alat, (sx, sy), (tx, ty), GELAP if siluet else None))
    if barang and gambar_item is None:
        raise ValueError("renderer item genggam harus disediakan melalui kontrak paket aktif")
    for item in (barang or []):
        sisi = +1 if item.get("tangan", "ka") == "ka" else -1
        if item.get("tangan", "ka") not in ("ka", "ki"):
            raise ValueError("tangan barang harus 'ka' atau 'ki'")
        sx, sy = siku[sisi]; tx, ty = tangan[sisi]
        sudut_barang = math.degrees(math.atan2(ty - sy, tx - sx))
        g.append(gambar_item(tx, ty, item["jenis"], angle=sudut_barang,
                             s=item.get("skala", .72), warna=item.get("warna")))
    if siluet:  # tepi tersinari hanya di sisi kiri (arah cahaya)
        mid = f"m{indeks}_{int(x)}_{int(y)}"
        g.insert(1, f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="-300" y="-560" width="600" height="600">'
                    f'<rect x="-120" y="-560" width="150" height="600" fill="url(#sisiKiri)"/></mask>')
        rim = f'<path d="{jubah}" fill="none" stroke="#fff1cc" stroke-width="7"/><circle cx="{pk[0]:.1f}" cy="{pk[1]:.1f}" r="{R_KEPALA}" fill="none" stroke="#fff1cc" stroke-width="6"/>'
        g.append(f'<g mask="url(#{mid})" filter="url(#b4)">{rim}</g>')
    else:
        g.append(f'<path d="{jubah}" fill="#ffe9c0" opacity=".14"/>')
    g.append("</g>")
    return "\n".join(g)
