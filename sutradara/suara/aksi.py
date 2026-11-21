"""Pemetaan aksi visual ke bunyi diegetik; posisi dihitung pada saat kejadian."""
from __future__ import annotations

import math
import random
from pathlib import Path

from .. import kamera as KM, waktu
from ..gerak import titik_kena

AKAR = Path(__file__).resolve().parents[2]
ASET = AKAR / "aset/suara"
AKSI = {
    "palu": .70, "gali": .78, "jalan": .34, "lari": .43, "lompat": .52,
}
MAKS_KETUK_PER_SHOT = 40
LEBAR, TINGGI = 1080.0, 1920.0


def nilai(v, t, default):
    if v is None:
        return float(default)
    if waktu.adalah_kf(v):
        return float(waktu.pada(v, t))
    return float(v)


def _kamera(k, t):
    k = k or {}
    z = nilai(k.get("zoom"), t, 1.0) * KM._zoom_hentak(k.get("hentak"), t)
    x, y = nilai(k.get("x"), t, 540.0), nilai(k.get("y"), t, 960.0)
    dx, dy = KM._geser_guncang(k.get("guncang"), t)
    return z, x, y, dx, dy


def _layar(shot, x, y, t):
    z, cx, cy, dx, dy = _kamera(shot.get("kamera"), t)
    return 540 + dx + (x - cx) * z, 960 + dy + (y - cy) * z, z


def _kotak(shot, i, t):
    tk = shot["tokoh"][i]
    x, y = nilai(tk.get("x"), t, 540), nilai(tk.get("y"), t, 960)
    s = nilai(tk.get("s"), t, 1.0)
    sx, sy, z = _layar(shot, x, y, t)
    # Tinggi mengikuti rangka Tokoh.orang (±360 px pada s=1); lebar dibuat
    # konservatif agar tepi jubah dan alat tidak dianggap pasti terlihat.
    w, h = 150 * s * z, 360 * s * z
    return (sx - w / 2, sy - h, sx + w / 2, sy), sx, s * z, sy


def _fraksi_bingkai(b):
    x0, y0, x1, y1 = b
    penuh = max(1.0, (x1 - x0) * (y1 - y0))
    dalam = max(0.0, min(LEBAR, x1) - max(0.0, x0)) * max(0.0, min(TINGGI, y1) - max(0.0, y0))
    return min(1.0, dalam / penuh)


def _titik_dalam(x, y, poligon):
    inside = False
    j = len(poligon) - 1
    for i, (xi, yi) in enumerate(poligon):
        xj, yj = poligon[j]
        if ((yi > y) != (yj > y)) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
            inside = not inside
        j = i
    return inside


def _fraksi_tertutup_depan(shot, b, t):
    if not shot.get("depan", True):
        return 0.0
    _, cx, _, _, _ = _kamera(shot.get("kamera"), t)
    geser = -(cx - 540) * .35
    kiri = [(-60 + geser, 1700), (40 + geser, 1610), (170 + geser, 1680),
            (290 + geser, 1920), (-60 + geser, 1920)]
    kanan = [(1140 + geser, 1660), (1020 + geser, 1600), (900 + geser, 1700),
             (850 + geser, 1760), (860 + geser, 1920), (1140 + geser, 1920)]
    x0, y0, x1, y1 = b
    total = tertutup = 0
    # Sampel area kotak secara merata; batu depan digambar setelah tokoh.
    for iy in range(7):
        for ix in range(7):
            x = x0 + (ix + .5) / 7 * (x1 - x0)
            y = y0 + (iy + .5) / 7 * (y1 - y0)
            total += 1
            if _titik_dalam(x, y, kiri) or _titik_dalam(x, y, kanan):
                tertutup += 1
    return tertutup / total if total else 0.0


def keterlihatan(shot, i, t):
    b, sx, ukuran, sy = _kotak(shot, i, t)
    fraksi = _fraksi_bingkai(b)
    if fraksi < .22:
        return 0.0, sx, ukuran, sy
    x0, y0, x1, y1 = b
    area = max(1.0, (x1 - x0) * (y1 - y0))
    for j, lain in enumerate(shot.get("tokoh", [])):
        if j == i:
            continue
        # Adegan mengurutkan tokoh dari y kecil ke besar; y lebih besar digambar di depan.
        if nilai(lain.get("y"), t, 960) <= nilai(shot["tokoh"][i].get("y"), t, 960):
            continue
        q, _, _, _ = _kotak(shot, j, t)
        irisan = max(0.0, min(x1, q[2]) - max(x0, q[0])) * max(0.0, min(y1, q[3]) - max(y0, q[1]))
        fraksi *= max(0.0, 1.0 - irisan / area)
    fraksi *= 1.0 - _fraksi_tertutup_depan(shot, b, t)
    return max(0.0, min(1.0, fraksi)), sx, ukuran, sy


def pan(x):
    return max(-.7, min(.7, (x - 540) / 540 * .7))


def _acak(tokoh, nomor, salt=0):
    # Variasi kecil, deterministik: ritme tetap tersinkron, timbre tidak identik.
    r = random.Random((tokoh + 1) * 1009 + (nomor + 1) * 7919 + salt * 104729)
    return r.uniform(.94, 1.06), r.uniform(.91, 1.08), r.uniform(-.018, .018)


def _ada(nama):
    return (ASET / (nama if nama.endswith(".mp3") else nama + ".mp3")).is_file()


def _permukaan(shot, tk, t):
    p = (tk.get("permukaan") or tk.get("material") or shot.get("permukaan") or "tanah").lower()
    aliases = {"pasir": "tanah", "bumi": "tanah", "darat": "tanah", "dek": "kayu",
               "dek_kapal": "kayu", "air": "air", "sungai": "air", "besi": "batu_besi",
               "batu": "batu_besi", "tembok": "batu_besi", "dinding": "batu_besi"}
    p = aliases.get(p, p)
    if p in {"tanah", "kayu", "air", "batu_besi"}:
        if p != "tanah" or tk.get("permukaan") or tk.get("material") or shot.get("permukaan"):
            return p
    # Infer dek kapal bila kaki tokoh berada dekat geladak bahtera yang terlihat.
    x, y = nilai(tk.get("x"), t, 540), nilai(tk.get("y"), t, 960)
    for b in shot.get("benda", []):
        if b.get("jenis") == "bahtera":
            bx, by, bs = nilai(b.get("x"), t, 540), nilai(b.get("y"), t, 1235), nilai(b.get("s"), t, 1)
            if abs(x - bx) <= 420 * bs and abs(y - (by - 250 * bs)) <= 70 * bs:
                return "kayu"
        if b.get("jenis") == "sungai" and b.get("isi") == "air" and y >= 1350:
            sisi = b.get("sisi")
            if (sisi == "kiri" and x < 560) or (sisi == "kanan" and x > 520):
                return "air"
    return "tanah"


def _sampel(aksi, permukaan):
    # Rekaman khusus dipakai bila tersedia; fallback selalu berasal dari aset repo.
    if aksi == "palu":
        return ("aksi/palu_batu_besi" if permukaan == "batu_besi" else "aksi/palu_kayu",
                "pintu_besi" if permukaan == "batu_besi" else "satu/palu")
    if aksi == "gali":
        return ("aksi/palu_batu_besi" if permukaan == "batu_besi" else "aksi/tanah_retak",
                "pintu_besi" if permukaan == "batu_besi" else "satu/gali")
    if aksi in {"jalan", "lari", "lompat"}:
        khusus = {"tanah": "aksi/langkah_pasir", "kayu": "aksi/langkah_kayu",
                  "air": "aksi/langkah_air", "batu_besi": "aksi/langkah_batu_besi"}[permukaan]
        fallback = "satu/langkah_lari" if aksi == "lari" else "satu/langkah"
        return khusus, fallback
    return "", ""


def _efek(berkas, fallback, *, at, vol, x, speed=1.0, sebab="", sampai=None, loop=False):
    nama = berkas if _ada(berkas) else fallback
    r = {"berkas": nama, "at": at, "vol": round(vol, 3), "pan": pan(x), "sebab": sebab}
    if speed != 1.0:
        r["kecepatan"] = speed
    if sampai is not None:
        r["sampai"] = round(max(.08, sampai), 3)
        r["keluar"] = min(.25, r["sampai"] / 2)
    if loop:
        r["loop"] = True
    return r


def _jadwal(spec):
    if isinstance(spec, str):
        return [(0.0, spec)]
    return sorted((float(a), b) for a, b in (spec or []))


def _aktif(jadwal, t):
    return next((nama for awal, nama in reversed(jadwal) if awal <= t), jadwal[0][1] if jadwal else "")


def _hit_tokoh(shot, mulai):
    dur = float(shot["durasi"])
    calon = []
    tawa = []
    for i, tk in enumerate(shot.get("tokoh", [])):
        off = i * .37  # renderer memberi offset ini pada animasi dan ekspresi tokoh.
        gerak = _jadwal(tk.get("gerak", tk.get("pose", "berdiri")))
        wajah = _jadwal(tk.get("wajah", "datar"))
        wajah_tercatat = set()
        for nomor, (awal, nama) in enumerate(gerak):
            akhir = gerak[nomor + 1][0] if nomor + 1 < len(gerak) else dur + off
            lo, hi = max(awal, off), min(akhir, dur + off)
            if hi <= lo:
                continue
            if nama == "tertawa":
                lokal = max(0.0, lo - off)
                if lokal < dur:
                    tampak, x, ukuran, y = keterlihatan(shot, i, lokal)
                    if tampak >= .22:
                        tawa.append((mulai + lokal, x, ukuran, tampak, i))
            if nama in AKSI:
                for urut, tc in enumerate(titik_kena(nama, lo, hi)):
                    lokal = tc - off
                    if not 0 <= lokal < dur:
                        continue
                    tampak, x, ukuran, y = keterlihatan(shot, i, lokal)
                    if tampak < .22:
                        continue
                    permukaan = _permukaan(shot, tk, lokal)
                    sampel, cadangan = _sampel(nama, permukaan)
                    speed, gain, geser = _acak(i, urut)
                    vol = AKSI[nama] * min(1.3, max(.2, ukuran)) * tampak * gain
                    at = min(dur - .001, max(0.0, lokal + geser))
                    calon.append({"rek": _efek(sampel, cadangan, at=mulai + at, vol=vol, x=x,
                                               speed=speed, sebab=f"tokoh {i + 1} {nama}"),
                                  "i": i, "score": tampak * ukuran * (.8 + .2 * y / TINGGI),
                                  "nomor": urut})
            # Wajah mengejek/tertawa adalah aksi terdengar walau pose tubuh tidak berubah.
            for wa, ekspresi in wajah:
                if ekspresi not in {"tertawa", "ejek", "mengejek"} or (wa, ekspresi) in wajah_tercatat:
                    continue
                lokal = max(wa, lo) - off
                if not 0 <= lokal < dur or lokal >= akhir - off:
                    continue
                wajah_tercatat.add((wa, ekspresi))
                tampak, x, ukuran, y = keterlihatan(shot, i, lokal)
                if tampak >= .22:
                    tawa.append((mulai + lokal, x, ukuran, tampak, i))
    # Tawa yang berdekatan digabung per kelompok waktu, bukan ditumpuk satu per wajah.
    kelompok_tawa = []
    for item in sorted(tawa, key=lambda x: x[0]):
        if not kelompok_tawa or item[0] - kelompok_tawa[-1][0][0] > .18:
            kelompok_tawa.append([item])
        else:
            kelompok_tawa[-1].append(item)
    tawa_rek = []
    for dekat in kelompok_tawa:
        at = min(a[0] for a in dekat)
        x = sum(a[1] * a[3] for a in dekat) / sum(a[3] for a in dekat)
        jumlah = len(dekat)
        tawa_rek.append(_efek("aksi/tawa_ejekan", "kerumunan_cemas", at=at,
            vol=min(.48, .20 + .06 * (jumlah - 1)), x=x, sebab="tokoh tertawa/mengejek"))
    # Pilih aktor terdekat/terlihat, bukan urutan JSON; setiap aktor terpilih mendapat
    # satu bunyi sebelum slot berikutnya dibagikan ke ketukan tambahan.
    per_tokoh = {}
    for c in calon:
        if c["i"] >= 0:
            per_tokoh.setdefault(c["i"], []).append(c)
    wajib = [max(v, key=lambda c: c["score"]) for v in per_tokoh.values()]
    wajib.sort(key=lambda c: c["score"], reverse=True)
    tambahan = [c for c in calon if c not in wajib]
    dipilih = wajib[:MAKS_KETUK_PER_SHOT]
    sisa = MAKS_KETUK_PER_SHOT - len(dipilih)
    if sisa > 0:
        tambahan.sort(key=lambda c: c["score"], reverse=True)
        dipilih.extend(tambahan[:sisa])
    # Bila ketukan aktor sudah ada, jangan tambahkan ketukan kapal kedua untuk aksi yang sama.
    hasil = [c["rek"] for c in dipilih] + tawa_rek
    return hasil, len(dipilih)


def _ada_pemalu_dekat(shot, benda):
    bx, by, bs = nilai(benda.get("x"), 0, 540), nilai(benda.get("y"), 0, 1235), nilai(benda.get("s"), 0, 1)
    dur = float(shot["durasi"])
    for i, tk in enumerate(shot.get("tokoh", [])):
        off = i * .37
        jad = _jadwal(tk.get("gerak", tk.get("pose", "berdiri")))
        for k, (a, nama) in enumerate(jad):
            if nama != "palu":
                continue
            b = jad[k + 1][0] if k + 1 < len(jad) else dur + off
            lo, hi = max(a, off), min(b, dur + off)
            if hi <= lo:
                continue
            t = min(dur - .001, max(0.0, (lo + hi) / 2 - off))
            tampak, _, _, _ = keterlihatan(shot, i, t)
            tx, ty = nilai(tk.get("x"), t, 540), nilai(tk.get("y"), t, 960)
            if tampak >= .22 and abs(tx - bx) <= 650 * bs and abs(ty - by) <= 520 * bs:
                return True
    return False


def _aksi_benda(shot, mulai, slot_ketukan):
    dur = float(shot["durasi"])
    hasil = []
    if slot_ketukan <= 0:
        return hasil
    for b in shot.get("benda", []):
        jenis = b.get("jenis")
        if jenis == "bahtera" and waktu.adalah_kf(b.get("jadi")):
            kf = sorted(b["jadi"])
            if _ada_pemalu_dekat(shot, b):
                continue
            for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
                if v1 <= v0:
                    continue
                t, nomor = max(0.0, t0) + .18, 0
                while t < min(t1, dur) and len(hasil) < slot_ketukan:
                    x, y, z = _layar(shot, nilai(b.get("x"), t, 540), nilai(b.get("y"), t, 1235), t)
                    if -80 <= x <= LEBAR + 80 and -80 <= y <= TINGGI + 80:
                        speed, gain, shift = _acak(71, nomor)
                        hasil.append(_efek("aksi/palu_kayu", "satu/palu", at=mulai + min(dur - .001, t + shift),
                            vol=.48 * min(1.2, nilai(b.get("s"), t, 1) * z) * gain, x=x,
                            speed=speed, sebab="papan bahtera bertambah"))
                    t += .72
                    nomor += 1
            continue
        # Komponen benda lain dapat mengumumkan perubahan besar lewat keyframe keadaan.
        for kunci in ("jadi", "terbuka", "retak", "surut", "jebol", "runtuh"):
            kf = b.get(kunci)
            if not waktu.adalah_kf(kf):
                continue
            for (t0, v0), (t1, v1) in zip(sorted(kf), sorted(kf)[1:]):
                if len(hasil) >= slot_ketukan:
                    break
                if v1 <= v0 or v1 - v0 < .12:
                    continue
                t = max(0.0, t0)
                if t >= dur:
                    continue
                x, y, z = _layar(shot, nilai(b.get("x"), t, 540), nilai(b.get("y"), t, 1250), t)
                if -80 <= x <= LEBAR + 80 and -80 <= y <= TINGGI + 80:
                    berkas, cadangan = (("aksi/tanah_retak", "tanah_retak") if kunci in {"retak", "jebol", "runtuh"}
                                        else ("aksi/kabut_keluar", "dentum_jauh"))
                    hasil.append(_efek(berkas, cadangan, at=mulai + t, vol=.3 * min(1.2, z),
                        x=x, sebab=f"benda berubah: {jenis or 'benda'}"))
    return hasil


def efek_aksi(shot, mulai):
    dur = float(shot["durasi"])
    hasil, jumlah_ketukan = _hit_tokoh(shot, mulai)
    hasil.extend(_aksi_benda(shot, mulai, MAKS_KETUK_PER_SHOT - jumlah_ketukan))
    # Kerumunan jauh: ambience hanya jika sebagian rentang massa masuk bingkai.
    npc = shot.get("npc_jauh")
    if npc and npc.get("n", 0) > 0:
        x0, x1, y = nilai(npc.get("x0"), 0, 80), nilai(npc.get("x1"), 0, 1000), nilai(npc.get("y"), 0, 1262)
        sx0, sy0, _ = _layar(shot, x0, y, dur / 2)
        sx1, sy1, _ = _layar(shot, x1, y, dur / 2)
        fraksi = max(0, min(LEBAR, max(sx0, sx1)) - max(0, min(sx0, sx1))) / max(1, abs(sx1 - sx0))
        if fraksi > .05 and -60 <= sy0 <= TINGGI + 60:
            hasil.append(_efek("aksi/kerumunan_jauh", "kerumunan_cemas", at=mulai + .08,
                vol=min(.22, (.035 + npc["n"] * .008) * fraksi), x=(sx0 + sx1) / 2,
                sebab="kerumunan jauh", sampai=max(.2, dur - .08), loop=True))
    # Kabut dan retakan hanya berbunyi ketika nilai keluar meningkat.
    for m in shot.get("kabut_tanpa_wujud", []):
        kf = m.get("keluar")
        if not waktu.adalah_kf(kf):
            continue
        for (t0, v0), (t1, v1) in zip(sorted(kf), sorted(kf)[1:]):
            if v1 <= v0:
                continue
            x, _, _ = _layar(shot, nilai(m.get("x"), t0, 540), nilai(m.get("y"), t0, 1330), t0)
            hasil.append(_efek("aksi/kabut_keluar", "dentum_jauh", at=mulai + max(0, t0),
                vol=.22, x=x, sebab="kabut keluar", sampai=max(.2, min(dur, t1) - max(0, t0))))
            if m.get("retakan", True):
                hasil.append(_efek("aksi/tanah_retak", "tanah_retak", at=mulai + max(0, t0),
                    vol=.32, x=x, sebab="retakan tanah"))
    return sorted(hasil, key=lambda r: r["at"])


def filter_kecepatan(r):
    k = max(.90, min(1.10, float(r.get("kecepatan", 1.0))))
    return f"asetrate=44100*{k:.4f},aresample=44100"
