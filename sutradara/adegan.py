"""Menyusun SATU bingkai dari satu shot pada detik tertentu.

Urutan lapis selalu sama (resep B4): langit -> lapis belakang -> tanah -> benda -> NPC jauh -> kabut jauh
-> makhluk/pilar cahaya/Dajjal/tokoh (diurutkan menurut y kaki: yang lebih bawah = lebih dekat, digambar belakangan)
-> lapis depan. Semua itu = DUNIA, digerakkan kamera. Teks layar digambar di atasnya dan TIDAK ikut kamera.

Angka mana pun boleh keyframe `[[detik, nilai], ...]` (lihat `waktu.py`). Kamera: lihat `kamera.py`.

Spesifikasi shot (contoh lengkap di contoh/*.json):
{
  "preset": "senja", "durasi": 4.0, "matahari": [860, 1060], "belakang": ["gunung"] | ["kota"] | [],
  "kamera": {"zoom": [[0, 1.0], [4, 1.12]], "x": 540, "y": 1000, "guncang": [[2.0, 30]], "hentak": [[0.1, 0.06]]},
  "benda": [{"jenis": "bahtera", "x": 790, "y": 1215, "s": 0.55, "jadi": [[0, 0.0], [4, 0.3]]}, {"jenis": "lapak", ...},
            {"jenis": "sungai", "isi": "air" | "api", "sisi": "kiri" | "kanan"}, {"jenis": "bukit"}],
  "npc_jauh": {"n": 11, "x0": 470, "x1": 1000, "y": 1262},
  "nur": [{"x": 270, "y": 1330, "nama": "Nabi Nuh a.s."}],
  "tokoh": [{"x": 620, "y": 1395, "s": 0.92, "pose": "tunjuk", "wajah": "ejek", "kepala": "imamah", "mode": "pakaian"}],
  "kabut_tanpa_wujud": [{"x": 540, "y": 1330, "keluar": [[0, 0.1], [2, 1.0]], "retakan": true}],
  "dajjal": [{"x": 540, "y": 1240, "s": 1.2, "lengan": "terbuka"}],
  "depan": true,
  "teks": {"sumber": "QS HUD 38", "judul": ["MEREKA", "MENGEJEK"], "warna": "putih", "judul_mulai": 0.4,
           "subtitle": "setiap kali lewat", "sorot": "lewat", "subtitle_mulai": 0.0}
}
"""
from __future__ import annotations

import math
import random

from . import kamera as KM
from .gaya import benda as BD, dajjal as DJ, dasar, kartu as KT, latar as LT, makhluk as MK, nur as NR, teks as TX, tokoh as TK
from .waktu import pada

DURASI_BAWAAN = 3.0


def _npc_jauh(spec: dict, tg: float) -> list[str]:
    rnd = random.Random(spec.get("seed", 11))
    n, x0, x1, y = spec.get("n", 10), spec.get("x0", 80), spec.get("x1", 1000), spec.get("y", 1262)
    out = []
    for k in range(n):
        x = x0 + (x1 - x0) * (k / max(n - 1, 1)) + rnd.uniform(-14, 14)
        yy = y + rnd.uniform(-6, 10)
        s, pose, kp = rnd.uniform(.34, .42), rnd.choice(["silang", "tertawa", "tunjuk", "angkat", "berdiri"]), rnd.choice(["imamah", "kain"])
        out.append((yy, TK.orang(x, yy + _goyang(pose, k, tg) * .4, s, pose=pose, indeks=k + 3, kepala=kp, rinci=False)))
    return [s for _, s in sorted(out)]


def _goyang(pose: str, i: int, tg: float) -> float:
    """Gerak idle tokoh (px): tertawa terguncang cepat, lainnya bernapas pelan."""
    if pose == "tertawa":
        return 4 * abs(math.sin(tg * 7 + i))
    if pose in ("kaget", "mundur", "tutup"):
        return 2 * math.sin(tg * 5 + i)
    return 1.5 * math.sin(tg * 1.8 + i * 0.9)


def _muncul(svg: str, mulai: float, t: float, cy: float) -> str:
    """Teks muncul tepat di `mulai` dengan pop singkat (0,15 dtk)."""
    if t < mulai:
        return ""
    u = min(1.0, (t - mulai) / 0.15)
    s = 0.85 + 0.15 * (1 - (1 - u) ** 3)
    return f'<g opacity="{u:.3f}" transform="translate(540,{cy}) scale({s:.4f}) translate(-540,{-cy})">{svg}</g>'


def susun(shot: dict, t: float = 0.0, tg: float | None = None, dalil: dict | None = None) -> str:
    """SVG utuh untuk shot pada detik lokal `t`. `tg` = waktu global video (untuk gerak hidup yang menyambung antar shot).
    `dalil` = {id: entri dalil terverifikasi} dari rencana, dipakai oleh "kartu_dalil": {"dalil": id, "mulai": detik}."""
    tg = t if tg is None else tg
    sp = pada(shot, t)
    p = sp["preset"]
    dunia = [LT.langit(p, matahari=tuple(sp["matahari"]) if sp.get("matahari") else None)]
    for b in sp.get("belakang", ["gunung"]):
        dunia.append({"gunung": LT.gunung, "kota": LT.kota}[b](p))
    dunia.append(LT.tanah(p, sp.get("tanah_y", 1250)))
    for b in sp.get("benda", []):
        j = b["jenis"]
        if j == "bahtera":
            dunia.append(BD.bahtera(b["x"], b["y"], b.get("s", 1), jadi=b.get("jadi", 1.0), goyang=b.get("goyang", 0.0),
                                    cahaya=b.get("cahaya", .8), pintu=b.get("pintu", 0.0), orang=int(b.get("orang", 0)),
                                    darat=b.get("darat", True), t=tg))
        elif j == "lapak":
            dunia.append(BD.lapak(b["x"], b["y"], b.get("warna", "#b8452e")))
        elif j == "sungai":
            dunia.append(BD.sungai(b["isi"], sisi=b["sisi"], t=tg))
        elif j == "bukit":
            dunia.append(f'<path d="M300 1260 Q 540 1060 780 1260Z" fill="{b.get("warna", "#160e18")}"/>')
        else:
            raise ValueError(f"benda tak dikenal: {j}")
    if sp.get("npc_jauh"):
        dunia += _npc_jauh(sp["npc_jauh"], tg)
        dunia.append(LT.kabut_jauh(p))
    tengah: list[tuple[float, str]] = []
    for m in sp.get("kabut_tanpa_wujud", []):
        s = (MK.retakan(m["x"], m["y"]) if m.get("retakan", True) else "") + MK.kabut_tanpa_wujud(
            m["x"], m["y"], tinggi=m.get("tinggi", 820), keluar=m.get("keluar", 1.0), t=tg)
        tengah.append((m["y"] - 1, s))
    for n in sp.get("nur", []):
        tengah.append((n["y"], NR.pilar(n["x"], n["y"], nama=n.get("nama"), sinar_ke=n.get("sinar_ke", "kanan"),
                                        tinggi=n.get("tinggi", 400), t=tg)))
    for d in sp.get("dajjal", []):
        tengah.append((d["y"], DJ.sosok(d["x"], d["y"], d.get("s", 1), lengan=d.get("lengan", "terbuka"))))
    for i, tk in enumerate(sp.get("tokoh", [])):
        pose = tk.get("pose", "berdiri")
        tengah.append((tk["y"], TK.orang(tk["x"], tk["y"] - _goyang(pose, i, tg), tk.get("s", 1), pose=pose,
                                         indeks=tk.get("indeks", i), mode=tk.get("mode", "pakaian"), kepala=tk.get("kepala", "imamah"),
                                         wajah=tk.get("wajah", "datar"), balik=tk.get("balik", False))))
    dunia += [s for _, s in sorted(tengah, key=lambda a: a[0])]
    lapis = [f'<g transform="{KM.transform(sp.get("kamera"), t)}">' + "\n".join(dunia) + "</g>"]
    if sp.get("depan", True):
        # lapis depan tidak ikut zoom kamera (kalau ikut, batu membesar jadi bercak hitam); hanya bergeser
        # lebih jauh dari dunia saat kamera menyamping -> rasa kedalaman (parallax)
        kx = float((sp.get("kamera") or {}).get("x", 540))
        lapis.append(f'<g transform="translate({-(kx - 540) * 0.35:.1f},0)">{LT.batu_depan(sp.get("warna_depan", "#120c16"))}</g>')
    tx = sp.get("teks") or {}
    if tx.get("sumber"):
        lapis.append(TX.sumber(tx["sumber"]))
    if tx.get("judul") and t < tx.get("judul_sampai", 1e9):
        lapis.append(_muncul(TX.judul(tx["judul"], warna=tx.get("warna", "putih")), tx.get("judul_mulai", 0.0), t, 380))
    kd = sp.get("kartu_dalil")
    if kd:
        d = (dalil or {}).get(kd["dalil"])
        if d is None:
            raise ValueError(f"kartu_dalil merujuk dalil '{kd['dalil']}' yang tidak ada di rencana")
        lapis.append(KT.kartu(d, KT.potongan(d), t, mulai=kd.get("mulai", 0.0), idx_uid=f"kd{kd['dalil']}"))
    elif tx.get("subtitle"):  # pita kartu menempati zona subtitle
        lapis.append(_muncul(TX.subtitle(tx["subtitle"], sorot=tx.get("sorot")), tx.get("subtitle_mulai", 0.0), t, 1700))
    return dasar.dokumen("\n".join(lapis))


def durasi(shot: dict, dalil: dict | None = None) -> float:
    """Durasi shot. Shot berkartu dalil tanpa `durasi` = waktu baca semua potongan (otomatis)."""
    if "durasi" in shot:
        return float(shot["durasi"])
    kd = shot.get("kartu_dalil")
    if kd and dalil and kd["dalil"] in dalil:
        return KT.durasi_total(KT.potongan(dalil[kd["dalil"]]), kd.get("mulai", 0.0))
    return DURASI_BAWAAN
