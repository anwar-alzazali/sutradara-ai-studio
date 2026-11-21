"""Menyusun SATU shot (gambar diam 1080x1920) dari spesifikasi JSON.

Urutan lapis selalu sama (resep B4): langit -> lapis belakang -> tanah -> benda -> NPC jauh -> kabut jauh
-> makhluk/pilar cahaya/tokoh (diurutkan menurut y: yang lebih bawah = lebih dekat, digambar belakangan) -> lapis depan -> teks.

Spesifikasi shot (semua kunci opsional kecuali `preset`), contoh lengkap di contoh/*.json:
{
  "preset": "senja", "matahari": [860, 1060], "belakang": ["gunung"] | ["kota"],
  "benda": [{"jenis": "bahtera", "x": 520, "y": 1215, "jadi": 0.4}, {"jenis": "lapak", ...}, {"jenis": "sungai", "isi": "air", "sisi": "kiri"}],
  "npc_jauh": {"n": 11, "x0": 470, "x1": 1000, "y": 1262},
  "nur": [{"x": 270, "y": 1330, "nama": "Nabi Nuh a.s."}],
  "tokoh": [{"x": 620, "y": 1395, "s": 0.92, "pose": "tunjuk", "wajah": "ejek", "kepala": "imamah", "mode": "pakaian"}],
  "kabut_tanpa_wujud": [{"x": 540, "y": 1330, "retakan": true}],
  "dajjal": [{"x": 540, "y": 1240, "s": 1.2, "lengan": "terbuka"}],
  "depan": true,
  "teks": {"sumber": "QS HUD 38", "judul": ["MEREKA", "MENGEJEK"], "warna": "putih", "subtitle": "setiap kali lewat", "sorot": "lewat"}
}
"""
from __future__ import annotations

import random

from .gaya import benda as BD, dajjal as DJ, dasar, latar as LT, makhluk as MK, nur as NR, teks as TX, tokoh as TK


def _npc_jauh(spec: dict) -> list[str]:
    rnd = random.Random(spec.get("seed", 11))
    n, x0, x1, y = spec.get("n", 10), spec.get("x0", 80), spec.get("x1", 1000), spec.get("y", 1262)
    out = []
    for k in range(n):
        x = x0 + (x1 - x0) * (k / max(n - 1, 1)) + rnd.uniform(-14, 14)
        out.append((y + rnd.uniform(-6, 10), TK.orang(x, y + rnd.uniform(-6, 10), rnd.uniform(.34, .42),
                                                       pose=rnd.choice(["silang", "tertawa", "tunjuk", "angkat", "berdiri"]),
                                                       indeks=k + 3, kepala=rnd.choice(["imamah", "kain"]), rinci=False)))
    return [s for _, s in sorted(out)]


def susun(shot: dict) -> str:
    """Kembalikan SVG utuh untuk satu shot."""
    p = shot["preset"]
    lap = [LT.langit(p, matahari=tuple(shot["matahari"]) if shot.get("matahari") else None)]
    for b in shot.get("belakang", ["gunung"]):
        lap.append({"gunung": LT.gunung, "kota": LT.kota}[b](p))
    lap.append(LT.tanah(p, shot.get("tanah_y", 1250)))
    for b in shot.get("benda", []):
        j = b["jenis"]
        if j == "bahtera":
            lap.append(BD.bahtera(b["x"], b["y"], b.get("s", 1), jadi=b.get("jadi", .6)))
        elif j == "lapak":
            lap.append(BD.lapak(b["x"], b["y"], b.get("warna", "#b8452e")))
        elif j == "sungai":
            lap.append(BD.sungai(b["isi"], sisi=b["sisi"]))
        elif j == "bukit":
            lap.append(f'<path d="M300 1260 Q 540 1060 780 1260Z" fill="{b.get("warna", "#160e18")}"/>')
        else:
            raise ValueError(f"benda tak dikenal: {j}")
    if shot.get("npc_jauh"):
        lap += _npc_jauh(shot["npc_jauh"])
        lap.append(LT.kabut_jauh(p))
    # lapis tengah-depan diurutkan menurut y kaki
    tengah: list[tuple[float, str]] = []
    for m in shot.get("kabut_tanpa_wujud", []):
        s = (MK.retakan(m["x"], m["y"]) if m.get("retakan", True) else "") + MK.kabut_tanpa_wujud(m["x"], m["y"], tinggi=m.get("tinggi", 820))
        tengah.append((m["y"] - 1, s))
    for n in shot.get("nur", []):
        tengah.append((n["y"], NR.pilar(n["x"], n["y"], nama=n.get("nama"), sinar_ke=n.get("sinar_ke", "kanan"), tinggi=n.get("tinggi", 400))))
    for d in shot.get("dajjal", []):
        tengah.append((d["y"], DJ.sosok(d["x"], d["y"], d.get("s", 1), lengan=d.get("lengan", "terbuka"))))
    for i, t in enumerate(shot.get("tokoh", [])):
        tengah.append((t["y"], TK.orang(t["x"], t["y"], t.get("s", 1), pose=t.get("pose", "berdiri"), indeks=t.get("indeks", i),
                                        mode=t.get("mode", "pakaian"), kepala=t.get("kepala", "imamah"),
                                        wajah=t.get("wajah", "datar"), balik=t.get("balik", False))))
    lap += [s for _, s in sorted(tengah, key=lambda a: a[0])]
    if shot.get("depan", True):
        lap.append(LT.batu_depan(shot.get("warna_depan", "#120c16")))
    tx = shot.get("teks") or {}
    if tx.get("sumber"):
        lap.append(TX.sumber(tx["sumber"]))
    if tx.get("judul"):
        lap.append(TX.judul(tx["judul"], warna=tx.get("warna", "putih")))
    if tx.get("subtitle"):
        lap.append(TX.subtitle(tx["subtitle"], sorot=tx.get("sorot")))
    return dasar.dokumen("\n".join(lap))
