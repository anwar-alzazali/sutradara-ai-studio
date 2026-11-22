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
from .gaya import akhir_zaman as AZ, malaikat as MA

DURASI_BAWAAN = 3.0


def _cahaya_mulia(n: dict, tg: float) -> str:
    """Pilih bentuk cahaya berdasarkan kategori; malaikat tidak pernah menjadi pilar."""
    if n.get("_kategori_peran") == "malaikat":
        return MA.berkas(n["x"], n["y"], tinggi=n.get("tinggi", 620),
                         lebar=n.get("lebar", 260), t=tg, seed=n.get("seed", 17))
    return NR.pilar(n["x"], n["y"], nama=n.get("nama"), sinar_ke=n.get("sinar_ke", "kanan"),
                    tinggi=n.get("tinggi", 400), lebar=n.get("lebar", 118),
                    pendar_rx=n.get("pendar_rx", 155), pendar_ry=n.get("pendar_ry", 190), t=tg)


def _npc_jauh(spec: dict, tg: float) -> list[str]:
    rnd = random.Random(spec.get("seed", 11))
    n, x0, x1, y = spec.get("n", 10), spec.get("x0", 80), spec.get("x1", 1000), spec.get("y", 1262)
    out = []
    for k in range(n):
        x = x0 + (x1 - x0) * (k / max(n - 1, 1)) + rnd.uniform(-14, 14)
        yy = y + rnd.uniform(-6, 10)
        s, gr = rnd.uniform(.34, .42), rnd.choice(["silang", "tertawa", "tunjuk", "angkat", "berdiri", "pinggang"])
        kp = rnd.choice(["imamah", "kain", "kopiah"])
        out.append((yy, TK.orang(x, yy, s, gerak=spec.get("gerak", gr), t=tg + k * 0.37, indeks=k + 3, kepala=kp, rinci=False)))
    return [s for _, s in sorted(out)]


def _muncul(svg: str, mulai: float, t: float, cy: float) -> str:
    """Teks muncul tepat di `mulai` dengan pop singkat (0,15 dtk)."""
    if t < mulai:
        return ""
    u = min(1.0, (t - mulai) / 0.15)
    s = 0.85 + 0.15 * (1 - (1 - u) ** 3)
    return f'<g opacity="{u:.3f}" transform="translate(540,{cy}) scale({s:.4f}) translate(-540,{-cy})">{svg}</g>'


def susun(shot: dict, t: float = 0.0, tg: float | None = None, dalil: dict | None = None, sub=None) -> str:
    """SVG utuh untuk shot pada detik lokal `t`. `tg` = waktu global video (untuk gerak hidup yang menyambung antar shot).
    `dalil` = {id: entri dalil terverifikasi} dari rencana, dipakai oleh "kartu_dalil": {"dalil": id, "mulai": detik}.
    `sub` = (kata, indeks_aktif) dari garis waktu narasi (fase 2); menggantikan subtitle tulisan di shot."""
    tg = t if tg is None else tg
    sp = pada(shot, t)
    p = sp["preset"]
    dunia = [LT.langit(p, matahari=tuple(sp["matahari"]) if sp.get("matahari") else None)]
    for b in sp.get("belakang", ["gunung"]):
        dunia.append({"gunung": LT.gunung, "kota": LT.kota}[b](p))
    # Kabut atmosfer adalah bidang latar: selalu di belakang tanah, bahtera,
    # NPC, pilar, dan tokoh agar tidak membentuk pita di atas visual inti.
    if sp.get("npc_jauh"):
        dunia.append(LT.kabut_jauh(p))
    tanah_y = sp.get("tanah_y", 1250)
    dunia.append(LT.tanah(p, tanah_y))
    permukaan = sp.get("permukaan_tanah", LT.PERMUKAAN_BAWAAN[p])
    if permukaan != "tanpa":
        dunia.append(LT.tekstur_tanah(p, tanah_y, jenis=permukaan, seed=sp.get("seed_tanah", 3)))
    # Pilar tertentu boleh berada di belakang benda utama agar tidak menutupi kapal/objek.
    for n in sp.get("nur", []):
        if n.get("di_belakang_benda"):
            dunia.append(_cahaya_mulia(n, tg))
    for b in sp.get("buraq", []):
        dunia.append(AZ.buraq(b["x"], b["y"], b.get("s", 1), t=tg))
    tanda_overlay = []
    for b in sp.get("akhir_zaman", []):
        j = b["jenis"]
        if j == "dinding_yajuj":
            dunia.append(AZ.dinding_yajuj(b["x"], b["y"], b.get("s", 1), lubang=b.get("lubang", 0)))
        elif j == "danau_surut":
            dunia.append(AZ.danau_surut(b["x"], b["y"], b.get("s", 1), surut=b.get("surut", 0)))
        elif j == "tanda_wajah":
            tanda_overlay.append(AZ.tanda_wajah(b["x"], b["y"], b.get("s", 1)))
        else:
            raise ValueError(f"komponen akhir zaman tak dikenal: {j}")
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
    tengah: list[tuple[float, str]] = []
    # Sistem barang tunggal: status per-shot menentukan pemilik, tangan, dan titik serah.
    # IK tangan menghitung sudut sendi; geometri barang ditempelkan ke pergelangan.
    barang_pemilik: dict[str, list[dict]] = {}
    target_tangan: dict[str, dict] = {}
    for item in sp.get("barang", []):
        pemilik = item.get("pemilik")
        if not pemilik:
            raise ValueError(f"barang {item.get('id', '?')} wajib memiliki pemilik")
        aksi = item.get("aksi", "pegang")
        tangan = item.get("tangan", "ka")
        if item.get("posisi_genggam") is not None:
            posisi = item["posisi_genggam"]
            if not (isinstance(posisi, (list, tuple)) and len(posisi) == 2):
                raise ValueError(f"barang {item.get('id', '?')} posisi_genggam harus [x, y]")
            target_tangan.setdefault(pemilik, {})[tangan] = tuple(posisi)
        if aksi in {"ulurkan", "terima"}:
            titik = item.get("titik_serah")
            if not (isinstance(titik, (list, tuple)) and len(titik) == 2):
                raise ValueError(f"barang {item.get('id', '?')} aksi {aksi} wajib memiliki titik_serah [x, y]")
            target_tangan.setdefault(pemilik, {})[tangan] = tuple(titik)
            pasangan = item.get("penerima") if aksi == "ulurkan" else item.get("pemberi")
            if pasangan:
                target_tangan.setdefault(pasangan, {})[item.get("tangan_pasangan", "ka")] = tuple(titik)
        kategori_pemilik = next((tk.get("_kategori_peran") for tk in shot.get("tokoh", [])
                                 if tk.get("peran") == pemilik), None)
        kategori_pemilik = kategori_pemilik or next((n.get("_kategori_peran") for n in shot.get("nur", [])
                                                      if n.get("peran") == pemilik), None)
        if kategori_pemilik == "nabi":
            pilar = next((n for n in sp.get("nur", []) if n.get("peran") == pemilik), None)
            if pilar is None:
                raise ValueError(f"barang {item.get('id', '?')} milik nabi {pemilik} tetapi pilar tidak ada di shot")
            svg_barang = BD.barang(pilar["x"] + item.get("sisi_x", 105),
                                   pilar["y"] + item.get("sisi_y", -65), item["jenis"],
                                   angle=item.get("angle", -35), s=item.get("skala", .8),
                                   warna=item.get("warna"), cahaya=True)
            tengah.append((pilar["y"] + item.get("sisi_y", -65), svg_barang))
        else:
            barang_pemilik.setdefault(pemilik, []).append({
                "jenis": item["jenis"], "tangan": item.get("tangan", "ka"),
                "skala": item.get("skala", .72), "warna": item.get("warna"),
            })
    for m in sp.get("kabut_tanpa_wujud", []):
        s = (MK.retakan(m["x"], m["y"]) if m.get("retakan", True) else "") + MK.kabut_tanpa_wujud(
            m["x"], m["y"], tinggi=m.get("tinggi", 820), keluar=m.get("keluar", 1.0), t=tg)
        tengah.append((m["y"] - 1, s))
    for n in sp.get("nur", []):
        if not n.get("di_belakang_benda"):
            tengah.append((n["y"], _cahaya_mulia(n, tg)))
    for d in sp.get("dajjal", []):
        tengah.append((d["y"], DJ.belakang(d["x"], d["y"], d.get("s", 1), t=tg, jalan=d.get("jalan", False), jubah_berkibar=d.get("jubah_berkibar", 0.0), buka=d.get("buka", 0.0)) if d.get("arah") == "belakang" else DJ.sosok(d["x"], d["y"], d.get("s", 1), lengan=d.get("lengan", "terbuka"))))
    for i, (tk, asli) in enumerate(zip(sp.get("tokoh", []), shot.get("tokoh", []))):
        ident = tk.get("_identitas") or {}
        # gerak & wajah boleh jadwal [[detik, nama]] -> diambil dari spesifikasi ASLI (bukan hasil `pada`)
        tengah.append((tk["y"], TK.orang(tk["x"], tk["y"], tk.get("s", 1), gerak=asli.get("gerak", asli.get("pose", "berdiri")),
                                         t=t + i * 0.37, indeks=tk.get("indeks", i), mode=tk.get("mode", "siluet" if tk.get("_cara_tampil") == "siluet" else "pakaian"),
                                         kepala=tk.get("kepala"), jenis=tk.get("jenis", "pria"), wajah=asli.get("wajah", "datar"), arah=asli.get("arah", tk.get("arah", "depan")), usia=tk.get("usia", "dewasa"), zaman=tk.get("zaman", "arab_kuno"),
                                         bicara=asli.get("bicara"), detail_wajah=asli.get("detail_wajah"), balik=tk.get("balik", False),
                                          wajah_cahaya=tk.get("_kategori_peran") == "sahabat",
                                          barang=barang_pemilik.get(asli.get("peran"), []),
                                          target_tangan=target_tangan.get(asli.get("peran")),
                                          warna_kulit=ident.get("warna_kulit"), warna_baju=ident.get("warna_baju"),
                                          warna_aksen=ident.get("warna_aksen"), rambut=ident.get("rambut"),
                                          janggut=ident.get("janggut", "pendek"),
                                          warna_janggut=ident.get("warna_janggut"))))
    dunia += [s for _, s in sorted(tengah, key=lambda a: a[0])]
    # Tanda wajah adalah penanda ilustratif; letakkan di atas tokoh sasaran.
    dunia += tanda_overlay
    lapis = [f'<g transform="{KM.transform(sp.get("kamera"), t)}">' + "\n".join(dunia) + "</g>"]
    if sp.get("depan", False):
        # Lapis depan berupa siluet tajam (tanpa blur bawaan); tidak ikut zoom kamera,
        # hanya bergeser untuk parallax saat kamera menyamping.
        kx = float((sp.get("kamera") or {}).get("x", 540))
        lapis.append(f'<g transform="translate({-(kx - 540) * 0.35:.1f},0)">{LT.batu_depan(sp.get("warna_depan", "#120c16"))}</g>')
    tx = sp.get("teks") or {}
    kd = sp.get("kartu_dalil")
    kartu_aktif = bool(kd) and t >= kd.get("mulai", 0.0)
    if kartu_aktif:  # kartu menempati bagian atas: label sumber & judul disembunyikan (sumber sudah ada di kepala kartu)
        tx = {k: v for k, v in tx.items() if k not in ("sumber", "judul")}
    if tx.get("sumber"):
        lapis.append(TX.sumber(tx["sumber"]))
    if tx.get("judul") and t < tx.get("judul_sampai", 1e9):
        lapis.append(_muncul(TX.judul(tx["judul"], warna=tx.get("warna", "putih")), tx.get("judul_mulai", 0.0), t, 380))
    if kd:
        d = (dalil or {}).get(kd["dalil"])
        if d is None:
            raise ValueError(f"kartu_dalil merujuk dalil '{kd['dalil']}' yang tidak ada di rencana")
        lapis.append(KT.kartu(d, KT.potongan(d), t, mulai=kd.get("mulai", 0.0), idx_uid=f"kd{kd['dalil']}", preset=p))
    if sub:
        lapis.append(TX.subtitle_frasa(sub[0], sub[1]))
    elif tx.get("subtitle"):
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
