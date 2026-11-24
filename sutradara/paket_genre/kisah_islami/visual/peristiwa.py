"""Visual SVG untuk peristiwa lintas cerita yang telah disebut eksplisit dalam naskah.

Komponen ini bukan pengganti dalil atau penafsir cerita. Ia hanya menggambar
peristiwa yang sudah dipetakan oleh analisis_peristiwa.
"""
from __future__ import annotations


def render(peristiwa: dict) -> str:
    aksi = peristiwa.get("aksi")
    sasaran = peristiwa.get("sasaran")
    if aksi == "terbelah" and sasaran == "bumi":
        # Retakan utama membelah bidang tanah secara diagonal dan bercabang.
        # Dua lempeng tanah terangkat sedikit; debu dan serpihan memperjelas
        # pergeseran tanpa menambahkan gambaran alam gaib yang tidak ada di dalil.
        return (
            '<g class="peristiwa-bumi-terbelah">'
            '<defs>'
            '<linearGradient id="bumi-retak-kiri" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#b88f8d"/><stop offset="1" stop-color="#76545e"/>'
            '</linearGradient>'
            '<linearGradient id="bumi-retak-kanan" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#c39a94"/><stop offset="1" stop-color="#805c63"/>'
            '</linearGradient>'
            '</defs>'
            # Lempeng kiri dan kanan, dengan tepi patahan bergerigi.
            '<path d="M0 1260 Q150 1235 300 1260 L430 1245 L485 1218 L465 1270 '
            'L420 1290 L455 1330 L395 1310 L350 1360 L315 1315 L260 1350 '
            'L220 1305 L150 1335 L105 1295 L0 1325Z" fill="url(#bumi-retak-kiri)" '
            'stroke="#49333f" stroke-width="10" stroke-linejoin="round"/>'
            '<path d="M1080 1250 Q930 1228 790 1252 L650 1238 L575 1212 L590 1270 '
            'L640 1290 L605 1330 L665 1310 L710 1360 L745 1315 L800 1350 '
            'L840 1305 L910 1335 L955 1295 L1080 1325Z" fill="url(#bumi-retak-kanan)" '
            'stroke="#49333f" stroke-width="10" stroke-linejoin="round"/>'
            # Celah gelap yang lebar di pusat, bukan garis tipis dekoratif.
            '<path d="M485 1218 L540 1248 L575 1212 L590 1270 L548 1300 '
            'L605 1330 L548 1368 L510 1330 L465 1270Z" fill="#211722"/>'
            '<path d="M540 1240 L510 1285 L552 1312 L520 1350 L548 1382" '
            'fill="none" stroke="#f2c98d" stroke-width="11" stroke-linecap="round" '
            'stroke-linejoin="round" opacity=".95"/>'
            # Cabang retakan menjalar ke kedua sisi permukaan.
            '<g fill="none" stroke="#382833" stroke-width="13" stroke-linecap="round" '
            'stroke-linejoin="round">'
            '<path d="M500 1260 L440 1240 L405 1205 L350 1195 L315 1165"/>'
            '<path d="M485 1290 L420 1310 L390 1350 L335 1370 L300 1410"/>'
            '<path d="M580 1260 L650 1235 L690 1195 L755 1185 L795 1150"/>'
            '<path d="M595 1290 L660 1310 L700 1350 L760 1370 L805 1410"/>'
            '<path d="M350 1260 L300 1235 L260 1245 L220 1215"/>'
            '<path d="M730 1260 L790 1230 L840 1245 L890 1210"/>'
            '</g>'
            '<g fill="none" stroke="#e7b985" stroke-width="5" opacity=".8">'
            '<path d="M500 1260 L440 1240 L405 1205"/>'
            '<path d="M580 1260 L650 1235 L690 1195"/>'
            '<path d="M485 1290 L420 1310 L390 1350"/>'
            '<path d="M595 1290 L660 1310 L700 1350"/>'
            '</g>'
            # Serpihan kecil di sekitar garis patahan.
            '<g fill="#d2a18d" stroke="#49333f" stroke-width="4">'
            '<path d="M390 1175 l24 -22 18 28 -26 13Z"/>'
            '<path d="M690 1168 l28 -18 12 30 -27 12Z"/>'
            '<path d="M440 1380 l22 -16 16 24 -24 12Z"/>'
            '<path d="M635 1390 l18 -22 24 20 -22 17Z"/>'
            '</g>'
            # Debu lembut di sepanjang celah; tetap dalam palet ilustrasi referensi.
            '<g fill="#ead0b0" opacity=".42">'
            '<circle cx="455" cy="1198" r="13"/><circle cx="620" cy="1188" r="10"/>'
            '<circle cx="470" cy="1370" r="9"/><circle cx="610" cy="1378" r="12"/>'
            '<circle cx="540" cy="1175" r="7"/><circle cx="540" cy="1410" r="8"/>'
            '</g>'
            '</g>'
        )
    if aksi == "mendekat" and sasaran == "matahari":
        return (
            '<g class="peristiwa-matahari-dekat">'
            '<defs><radialGradient id="matahari_dekat"><stop offset="0" stop-color="#fff7d4"/>'
            '<stop offset=".42" stop-color="#ffd27a" stop-opacity=".9"/>'
            '<stop offset="1" stop-color="#ff9b55" stop-opacity="0"/></radialGradient></defs>'
            '<circle cx="540" cy="430" r="300" fill="url(#matahari_dekat)"/>'
            '<circle cx="540" cy="430" r="82" fill="#ffe8b0" opacity=".92"/>'
            '</g>'
        )
    if aksi == "berkumpul" and sasaran == "kerumunan":
        return (
            '<g class="peristiwa-kerumunan" fill="#40303a" stroke="#17121a" stroke-width="5">'
            + "".join(
                f'<g transform="translate({x} {y})"><circle cy="-36" r="17" fill="#b98768"/>'
                '<path d="M-23 0 Q0 -18 23 0 L30 100 L-30 100Z" fill="#62505a"/></g>'
                for y, xs in ((0, range(80, 1080, 100)), (85, range(35, 1080, 75)))
                for x in xs
            ) + '</g>'
        )
    if aksi == "berkeringat" and sasaran in {"kerumunan", "keringat"}:
        return (
            '<g class="peristiwa-keringat" fill="none" stroke="#9ed8ee" stroke-width="7" opacity=".8">'
            + "".join(f'<path d="M{x} {y} q -13 20 0 28 q 13 -8 0 -28Z" fill="#9ed8ee"/>'
                      for x, y in ((170, 1410), (330, 1460), (540, 1390), (760, 1450), (920, 1400)))
            + '</g>'
        )
    # "Tenggelam" tidak boleh divisualkan sebagai tetesan keringat.
    # Sampai tersedia komponen yang menyatakan peristiwa itu secara tepat,
    # lebih aman tidak menambahkan overlay yang salah makna.
    if aksi == "lari":
        return (
            '<g class="peristiwa-pelarian" fill="none" stroke="#d8b58a" stroke-width="8" opacity=".75">'
            '<path d="M170 1560 l-80 35 M210 1580 l-70 50 M870 1550 l90 35 M850 1580 l75 50"/>'
            '</g>'
        )
    return ""


def render_semua(peristiwa: list[dict]) -> str:
    """Gabungkan hanya komponen yang memiliki renderer; aksi lain tetap pada aktor."""
    return "".join(render(item) for item in peristiwa)
