"""Visual SVG untuk peristiwa lintas cerita yang telah disebut eksplisit dalam naskah."""
from __future__ import annotations


def render(peristiwa: dict) -> str:
    aksi = peristiwa.get("aksi")
    sasaran = peristiwa.get("sasaran")
    if aksi == "terbelah" and sasaran == "bumi":
        return (
            '<g class="peristiwa-bumi-terbelah">'
            '<path d="M0 1280 Q180 1250 350 1280 L500 1280 L470 1320 L390 1300 L330 1370 L270 1310 L190 1390 L120 1310 L0 1340Z" fill="#17121a"/>'
            '<path d="M540 1280 Q720 1250 1080 1280 L1080 1340 L930 1310 L850 1390 L770 1310 L690 1370 L610 1300 L570 1320Z" fill="#17121a"/>'
            '<path d="M540 1270 L505 1320 L548 1350 L510 1400" stroke="#f4d39a" stroke-width="9" fill="none" stroke-linecap="round"/>'
            '</g>'
        )
    if aksi == "mendekat" and (sasaran == "matahari" or peristiwa.get("tujuan") == "matahari"):
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
