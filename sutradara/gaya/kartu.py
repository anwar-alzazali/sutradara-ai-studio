"""Kartu dalil BERTAHAP (keputusan pemilik 21 Nov 2026; diperbarui: di ATAS, lebih transparan, warna ikut suasana).

Bukan satu kartu besar yang menutupi layar: sebuah pita di atas berisi SATU potongan dalil, Arab (<= 2 baris)
di atas dan terjemah (<= 2 baris) di bawahnya, tampil bersamaan. Arab muncul seperti disapu dari kanan ke kiri,
terjemah muncul seperti diketik. Setelah waktu baca habis, potongan memudar dan diganti potongan berikutnya.
Adegan tetap terlihat di bawah pita. Sumber + derajat tampil kecil di kepala pita.
Pemotongan & waktu: sutradara/dalil/segmen.py. Teks yang tampil = teks terverifikasi apa adanya.
"""
from __future__ import annotations

from html import escape

from ..dalil import segmen as SG

Y_ATAS = 150           # tepi atas isi pita (di bawah bilah atas TikTok); pita memudar ke bawah
TINGGI = 470

# Warna kartu mengikuti preset suasana adegan (latar.PRESET): panel tembus pandang + teks yang kontras dengan langitnya.
TEMA = {
    "senja":       dict(panel="#1b1030", op=.42, ar="#fff6dd", id="#ffffff", aksen="#ffd27a", garis="#1b1030"),
    "malam":       dict(panel="#060918", op=.42, ar="#eef3ff", id="#ffffff", aksen="#bfe3ff", garis="#060918"),
    "malam_merah": dict(panel="#140808", op=.42, ar="#fff1e6", id="#ffffff", aksen="#ff9a6a", garis="#140808"),
    "fajar":       dict(panel="#2c2a52", op=.36, ar="#fffaf0", id="#ffffff", aksen="#ffd9a0", garis="#2c2a52"),
    "dhuha":       dict(panel="#fffaf0", op=.50, ar="#2a1c10", id="#2a1c10", aksen="#9a5a10", garis="#fffaf0"),
}
TEMA_BAWAAN = "senja"
UK_AR, UK_ID = 58, 44
JARAK_AR, JARAK_ID = 84, 58
PORSI_MUNCUL = 0.42     # bagian waktu potongan yang dipakai untuk menyapu/mengetik
PUDAR = 0.22


from functools import lru_cache


@lru_cache(maxsize=64)
def _potong_cache(ar: str, tr: str) -> tuple:
    return tuple(SG.potong(ar, tr))


def teks_kartu(dalil: dict) -> tuple[str, str]:
    """Teks yang tampil: kutipan (bila ada, wajib potongan persis teks terverifikasi) atau teks utuh."""
    return dalil.get("kutipan_ar") or dalil.get("teks_ar", ""), dalil.get("kutipan_id") or dalil.get("terjemah", "")


def potongan(dalil: dict) -> list[tuple[str, str]]:
    ar, tr = teks_kartu(dalil)
    return list(_potong_cache(ar, tr)) if ar and tr else []


def rencana_waktu(potongan: list[tuple[str, str]], mulai: float = 0.0) -> list[tuple[float, float]]:
    """(awal, akhir) tiap potongan, relatif awal shot."""
    out, t = [], mulai
    for _, tr in potongan:
        d = SG.durasi_baca(tr)
        out.append((t, t + d)); t += d
    return out


def durasi_total(potongan: list[tuple[str, str]], mulai: float = 0.0, ekor: float = 0.4) -> float:
    w = rencana_waktu(potongan, mulai)
    return round((w[-1][1] if w else mulai) + ekor, 2)


def _label(dalil: dict) -> str:
    lab = dalil.get("label", "")
    if dalil.get("jenis") == "hadis" and dalil.get("derajat") in ("sahih", "hasan"):
        lab += f" · {dalil['derajat'].upper()}"
    return lab


def kartu(dalil: dict, potongan: list[tuple[str, str]], t: float, *, mulai: float = 0.0, idx_uid: str = "k",
          preset: str = TEMA_BAWAAN) -> str:
    """SVG pita kartu pada detik lokal t. Kosong sebelum `mulai`."""
    waktu = rencana_waktu(potongan, mulai)
    if not waktu or t < mulai:
        return ""
    i = next((j for j, (a, b) in enumerate(waktu) if t < b), len(waktu) - 1)
    a, b = waktu[i]
    akhir = i == len(waktu) - 1
    u = max(0.0, t - a)
    muncul = min(1.0, u / max(0.6, (b - a) * PORSI_MUNCUL))
    op = min(1.0, u / 0.15) if i == 0 else 1.0
    if not akhir and t > b - PUDAR:
        op = max(0.0, (b - t) / PUDAR)
    ar, tr = potongan[i]
    baris_ar, baris_id = SG.baris(ar, True), SG.baris(tr, False)

    w = TEMA.get(preset, TEMA[TEMA_BAWAAN])
    garis = f'stroke="{w["garis"]}" stroke-width="6" stroke-opacity=".55" paint-order="stroke"'  # tepi halus supaya terbaca di langit apa pun
    g = [f'<g class="kartu-dalil" opacity="{op:.3f}">',
         f'<defs><linearGradient id="{idx_uid}p" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{w["panel"]}" stop-opacity="{w["op"]}"/>'
         f'<stop offset=".78" stop-color="{w["panel"]}" stop-opacity="{w["op"] * .8:.2f}"/><stop offset="1" stop-color="{w["panel"]}" stop-opacity="0"/></linearGradient></defs>',
         f'<rect x="-10" y="-20" width="1100" height="{Y_ATAS + TINGGI + 40}" fill="url(#{idx_uid}p)"/>',
         f'<text x="540" y="{Y_ATAS + 22}" text-anchor="middle" font-size="26" font-weight="800" fill="{w["aksen"]}" letter-spacing="1.5" {garis}>{escape(_label(dalil))}</text>',
         f'<line x1="440" y1="{Y_ATAS + 40}" x2="640" y2="{Y_ATAS + 40}" stroke="{w["aksen"]}" stroke-width="2" opacity=".6"/>']
    # Arab: sapuan kanan -> kiri, baris demi baris (proporsi panjang tiap baris)
    pj = [max(1, SG.panjang_arab(x)) for x in baris_ar]
    total = sum(pj); sudah = 0
    for k, br in enumerate(baris_ar):
        y = Y_ATAS + 120 + k * JARAK_AR
        mulai_b, porsi_b = sudah / total, pj[k] / total; sudah += pj[k]
        p = min(1.0, max(0.0, (muncul - mulai_b) / porsi_b))
        lebar = min(1000.0, SG.panjang_arab(br) * UK_AR * 0.47 + 60)
        kanan = 540 + lebar / 2
        g.append(f'<clipPath id="{idx_uid}c{k}"><rect x="{kanan - p * lebar:.1f}" y="{y - 80}" width="{p * lebar + 4:.1f}" height="120"/></clipPath>'
                 f'<text x="540" y="{y}" text-anchor="middle" direction="rtl" font-family="Amiri" font-size="{UK_AR}" fill="{w["ar"]}" {garis} '
                 f'clip-path="url(#{idx_uid}c{k})">{escape(br)}</text>')
    # terjemah: diketik kiri -> kanan, baris demi baris
    y0 = Y_ATAS + 120 + len(baris_ar) * JARAK_AR + 26
    huruf = sum(len(x) for x in baris_id); tampil = int(round(muncul * huruf))
    for k, br in enumerate(baris_id):
        bagian = br[:max(0, min(len(br), tampil))]; tampil -= len(br)
        if not bagian:
            continue
        kursor = f'<tspan fill="{w["aksen"]}">▍</tspan>' if 0 < len(bagian) < len(br) else ""
        # jangkar kiri tetap (perkiraan lebar baris penuh) supaya teks tidak bergeser saat bertambah
        g.append(f'<text x="{540 - len(br) * UK_ID * 0.26:.0f}" y="{y0 + k * JARAK_ID}" text-anchor="start" font-size="{UK_ID}" '
                 f'font-weight="700" fill="{w["id"]}" {garis}>{escape(bagian)}{kursor}</text>')
    # penanda jumlah potongan
    if len(potongan) > 1:
        g.append("".join(f'<circle cx="{540 + (j - (len(potongan) - 1) / 2) * 22:.0f}" cy="{Y_ATAS + TINGGI - 10}" r="5" '
                         f'fill="{w["aksen"] if j == i else w["id"]}" opacity="{1 if j == i else .35}"/>' for j in range(len(potongan))))
    g.append("</g>")
    return "\n".join(g)
