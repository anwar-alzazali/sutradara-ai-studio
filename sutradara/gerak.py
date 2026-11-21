"""Pustaka GERAK tokoh: tiap gerak = fungsi waktu -> sudut sendi rangka (lihat gaya/rangka.py).

Sudut dalam derajat. Ruas lengan/kaki: 0 = lurus ke bawah, 90 = mendatar ke LUAR badan, 180 = lurus ke atas,
negatif = menyilang ke dalam. Sisi kanan layar = akhiran `_ka`, kiri = `_ki`. Semua tokoh tampak depan (gaya 2D datar).

Kunci pose:
  tubuh   condong badan (+ ke kanan layar)       kepala  miring kepala
  naik    geser panggul ke atas (-) / bawah (+)  geser   geser panggul ke samping
  toleh   geser wajah kiri/kanan (-1..1)        angguk  geser wajah atas/bawah (-1..1)
  la/sa   lengan atas / lengan bawah            pa/ba   paha / betis       pf = pemendekan paha (1 = penuh)
  bangku  1 bila duduk (bangku digambar)

Jadwal di spesifikasi shot: "gerak": "jalan" atau [[0, "jalan"], [2.5, "berdiri"], [3, "tunjuk"]]
Perpindahan antar-gerak dicampur halus selama CAMPUR detik.
"""
from __future__ import annotations

import math

CAMPUR = 0.35
DASAR = dict(tubuh=0.0, kepala=0.0, naik=0.0, geser=0.0, toleh=0.0, angguk=0.0,
             la_ka=8.0, la_ki=8.0, sa_ka=4.0, sa_ki=4.0, pa_ka=4.0, pa_ki=4.0, ba_ka=2.0, ba_ki=2.0,
             pf_ka=1.0, pf_ki=1.0, bangku=0.0)


LENGAN_A, LENGAN_B = 64, 58  # sama dengan gaya/tokoh.py


def ik(tx: float, ty: float) -> tuple[float, float]:
    """Sudut (lengan atas, lengan bawah) agar tangan tiba di (tx keluar, ty ke bawah) relatif bahu; siku menekuk ke luar."""
    d = max(abs(LENGAN_A - LENGAN_B) + 1, min(LENGAN_A + LENGAN_B - 1, math.hypot(tx, ty)))
    arah = math.degrees(math.atan2(tx, ty))
    a = math.degrees(math.acos((LENGAN_A ** 2 + d ** 2 - LENGAN_B ** 2) / (2 * LENGAN_A * d)))
    calon = [arah - a, arah + a]
    a1 = max(calon, key=lambda c: math.sin(math.radians(c)))  # siku paling ke luar
    ex, ey = LENGAN_A * math.sin(math.radians(a1)), LENGAN_A * math.cos(math.radians(a1))
    a2 = math.degrees(math.atan2(tx - ex, ty - ey))
    return a1, a2


def _p(ka: tuple | None = None, ki: tuple | None = None, **k) -> dict:
    """Pose. `ka`/`ki` = titik tujuan tangan kanan/kiri (keluar, bawah) relatif bahu; sudut lengan dihitung otomatis."""
    d = dict(DASAR); d.update(k)
    if ka:
        d["la_ka"], d["sa_ka"] = ik(*ka)
    if ki:
        d["la_ki"], d["sa_ki"] = ik(*ki)
    return d


def _napas(t: float, d: dict, kuat: float = 1.0) -> dict:
    d = dict(d); d["naik"] += 1.5 * kuat * math.sin(t * 1.8); d["kepala"] += 1.2 * kuat * math.sin(t * 0.9)
    return d


# ---------- gerak berulang ----------
def jalan(t: float) -> dict:
    f = 2 * math.pi * 1.0 * t
    ka, ki = max(0.0, math.sin(f)), max(0.0, -math.sin(f))
    return _p(naik=-4 * abs(math.cos(f)), tubuh=1.5 * math.sin(f), kepala=-1.5 * math.sin(f),
              pf_ka=1 - .3 * ka, pf_ki=1 - .3 * ki, ba_ka=-18 * ka + 2, ba_ki=-18 * ki + 2, pa_ka=4 + 3 * ka, pa_ki=4 + 3 * ki,
              la_ka=10 + 8 * ki, la_ki=10 + 8 * ka, sa_ka=6 + 30 * ki, sa_ki=6 + 30 * ka)


def lari(t: float) -> dict:
    f = 2 * math.pi * 1.7 * t
    ka, ki = max(0.0, math.sin(f)), max(0.0, -math.sin(f))
    return _p(naik=-10 * abs(math.cos(f)) - 4, tubuh=3 * math.sin(f), kepala=-2 * math.sin(f),
              pf_ka=1 - .5 * ka, pf_ki=1 - .5 * ki, ba_ka=-40 * ka + 4, ba_ki=-40 * ki + 4, pa_ka=6 + 6 * ka, pa_ki=6 + 6 * ki,
              la_ka=22 + 20 * ki, la_ki=22 + 20 * ka, sa_ka=70 + 40 * ki, sa_ki=70 + 40 * ka)


def joget(t: float) -> dict:
    f = 2 * math.pi * 1.2 * t
    return _p(geser=12 * math.sin(f), tubuh=-6 * math.sin(f), kepala=6 * math.sin(f + 0.6), naik=-6 * abs(math.sin(f)),
              la_ka=140 + 25 * math.sin(f), sa_ka=165 + 20 * math.sin(f + 1), la_ki=140 - 25 * math.sin(f), sa_ki=165 - 20 * math.sin(f + 1),
              pa_ka=8 + 4 * math.sin(f), pa_ki=8 - 4 * math.sin(f), ba_ka=-6 * max(0, math.sin(f)), ba_ki=-6 * max(0, -math.sin(f)))


def lompat(t: float) -> dict:
    u = (t % 1.2) / 1.2
    if u < 0.2:  # jongkok ancang-ancang
        k = math.sin(math.pi * u / 0.2 / 2)
        return _p(naik=22 * k, pf_ka=1 - .25 * k, pf_ki=1 - .25 * k, ba_ka=-10 * k, ba_ki=-10 * k, la_ka=20 - 10 * k, la_ki=20 - 10 * k)
    if u < 0.75:  # melayang
        k = (u - 0.2) / 0.55
        return _p(naik=-120 * math.sin(math.pi * k), pf_ka=.75, pf_ki=.75, ba_ka=-25, ba_ki=-25, pa_ka=10, pa_ki=10,
                  la_ka=150, la_ki=150, sa_ka=170, sa_ki=170)
    k = 1 - (u - 0.75) / 0.25  # mendarat
    return _p(naik=18 * k, pf_ka=1 - .2 * k, pf_ki=1 - .2 * k, ba_ka=-8 * k, ba_ki=-8 * k, la_ka=40 * k + 8, la_ki=40 * k + 8)


def duduk(t: float) -> dict:
    return _napas(t, _p(naik=55, pf_ka=.3, pf_ki=.3, pa_ka=14, pa_ki=14, ba_ka=3, ba_ki=3,
                        ka=(4, 108), ki=(4, 108), bangku=1.0), .6)


def melambai(t: float) -> dict:
    return _napas(t, _p(la_ka=150, sa_ka=160 + 25 * math.sin(t * 2 * math.pi * 1.6), kepala=4))


def palu(t: float) -> dict:
    u = (math.sin(t * 2 * math.pi * 1.4) + 1) / 2  # 1 = terangkat, 0 = memukul
    return _p(la_ka=40 + 85 * u, sa_ka=60 + 115 * u, tubuh=-3 + 4 * u, naik=2 * (1 - u), la_ki=20, sa_ki=-30)


def menggeleng(t: float) -> dict:
    return _napas(t, _p(toleh=0.8 * math.sin(t * 2 * math.pi * 1.6)))


def mengangguk(t: float) -> dict:
    return _napas(t, _p(angguk=0.8 * max(0, math.sin(t * 2 * math.pi * 1.2))))


def tertawa(t: float) -> dict:
    return _p(ka=(-26, 78), ki=(-26, 78), kepala=-8, naik=-3 * abs(math.sin(t * 7)), tubuh=2 * math.sin(t * 7))


# ---------- pose diam (diberi napas) ----------
POSE = {
    "berdiri": _p(),
    "tunjuk": _p(la_ka=95, sa_ka=95, kepala=3),
    "angkat": _p(la_ka=165, sa_ka=178),
    "silang": _p(ka=(-62, 46), ki=(-58, 40)),
    "kaget": _p(ka=(14, -72), ki=(14, -72), naik=-4),
    "mundur": _p(ki=(70, -40), tubuh=6, kepala=-6, pf_ki=.85, ba_ki=-10),
    "tutup": _p(ka=(-36, -32), kepala=-4),                       # menutup mulut
    "tutup_telinga": _p(ka=(-4, -50), ki=(-4, -50)),
    "tutup_wajah": _p(ka=(-30, -48), ki=(-30, -48), kepala=-5, naik=3),
    "berdoa": _p(ka=(-14, 40), ki=(-14, 40), kepala=-6, angguk=.4),  # tangan menengadah di depan dada
    "menengadah": _p(ka=(26, -46), ki=(26, -46), kepala=-10, angguk=-.6),
    "lemas": _p(la_ka=4, la_ki=4, sa_ka=0, sa_ki=0, kepala=10, angguk=.7, naik=4, tubuh=-2),
    "pinggang": _p(ka=(-6, 96), ki=(-6, 96)),                    # tangan di pinggang (angkuh)
    "dagu": _p(ka=(-30, -18), ki=(-50, 52), kepala=6),          # berpikir: tangan di dagu
    "kepala": _p(ka=(-10, -78), kepala=-6),                      # menggaruk/memegang kepala (bingung, pusing)
}
BERULANG = {"jalan": jalan, "lari": lari, "joget": joget, "lompat": lompat, "duduk": duduk, "melambai": melambai,
            "palu": palu, "menggeleng": menggeleng, "mengangguk": mengangguk, "tertawa": tertawa}
SEMUA = sorted(set(POSE) | set(BERULANG))


def satu(nama: str, t: float) -> dict:
    if nama in BERULANG:
        return BERULANG[nama](t)
    if nama in POSE:
        return _napas(t, POSE[nama])
    raise ValueError(f"gerak tak dikenal: {nama} (pilihan: {', '.join(SEMUA)})")


def _jadwal(spec) -> list[tuple[float, str]]:
    if isinstance(spec, str):
        return [(0.0, spec)]
    return sorted(((float(a), b) for a, b in spec), key=lambda x: x[0])


def pada(spec, t: float) -> dict:
    """Sudut sendi pada detik t dari jadwal gerak (string atau [[detik, nama], ...]), dengan campuran halus."""
    j = _jadwal(spec or "berdiri")
    i = max([k for k, (a, _) in enumerate(j) if a <= t] or [0])
    kini = satu(j[i][1], t)
    if i == 0 or t - j[i][0] >= CAMPUR:
        return kini
    w = (t - j[i][0]) / CAMPUR; w = w * w * (3 - 2 * w)
    lalu = satu(j[i - 1][1], t)
    return {k: lalu[k] + (kini[k] - lalu[k]) * w for k in kini}


def nilai_jadwal(spec, t: float, bawaan: str) -> str:
    """Untuk jadwal berupa teks (mis. wajah): nilai yang berlaku pada detik t."""
    if not spec:
        return bawaan
    j = _jadwal(spec)
    return next((b for a, b in reversed(j) if a <= t), j[0][1])
