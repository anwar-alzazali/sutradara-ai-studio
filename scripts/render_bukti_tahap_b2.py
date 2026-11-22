"""Render bukti visual Tahap B2: golongan tokoh, barang, dan serah-terima."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageOps

AKAR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AKAR))

from sutradara import adegan, render, video  # noqa: E402
from sutradara.gaya import tokoh  # noqa: E402

OUT = Path("keluaran-bukti/tahap-b2")
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    rencana = json.loads(Path("contoh/b2_adab_barang.json").read_text(encoding="utf-8"))
    shots = video.daftar_shot(rencana)
    label = [
        "Serah: manusia + malaikat + sahabat",
        "Terima: pemilik berpindah",
        "Serah: manusia menuju pilar nabi",
        "Barang nabi di sisi pilar (tanpa tangan)",
    ]
    kartu = []
    with render.peramban() as pg:
        for i, shot in enumerate(shots):
            file = OUT / f"b2-shot-{i + 1:02d}.jpg"
            render.png(adegan.susun(shot, 1.0), file, halaman=pg)
            im = Image.open(file).convert("RGB")
            im.thumbnail((360, 640))
            panel = Image.new("RGB", (390, 690), "white")
            panel.paste(im, ((390 - im.width) // 2, 38))
            ImageDraw.Draw(panel).text((12, 12), label[i] if i < len(label) else f"Shot {i + 1}", fill="black")
            kartu.append(panel)
        lembar = Image.new("RGB", (390 * len(kartu), 690), (238, 238, 238))
        for i, panel in enumerate(kartu):
            lembar.paste(panel, (390 * i, 0))
        lembar.save(OUT / "lembar-kontak-b2.jpg", quality=88, optimize=True)

        # Bukti close-up seluruh preset ekspresi; memakai renderer wajah produksi.
        # Ambil seluruh preset produksi: semua ekspresi lama dan tambahan mikro baru.
        ekspresi = list(tokoh.WAJAH)
        kartu_wajah = []
        import tempfile
        with tempfile.TemporaryDirectory() as sementara:
            for nama in ekspresi:
                svg = (
                    '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" '
                    'viewBox="0 0 220 390"><rect width="220" height="390" fill="#f3e9dc"/>'
                    '<ellipse cx="110" cy="185" rx="34" ry="43" fill="#c98b62"/>'
                    '<path d="M76 185 C75 140 145 140 144 185 C132 167 88 167 76 185Z" fill="#2a1b14"/>'
                    + "".join(tokoh._wajah(nama, 0.0, False, False, 110, 185))
                    + '</svg>'
                )
                png = Path(sementara) / f"{nama}.png"
                render.png(svg, png, halaman=pg)
                wajah = Image.open(png).convert("RGB")
                wajah = ImageOps.fit(wajah, (220, 150), centering=(0.5, 0.48))
                panel = Image.new("RGB", (240, 190), "white")
                panel.paste(wajah, ((240 - wajah.width) // 2, 4))
                ImageDraw.Draw(panel).text((8, 164), nama, fill="black")
                kartu_wajah.append(panel)
        kolom = 5
        baris = (len(kartu_wajah) + kolom - 1) // kolom
        lembar_wajah = Image.new("RGB", (240 * kolom, 190 * baris), (238, 238, 238))
        for i, panel in enumerate(kartu_wajah):
            lembar_wajah.paste(panel, ((i % kolom) * 240, (i // kolom) * 190))
        lembar_wajah.save(OUT / "lembar-ekspresi-b2.jpg", quality=92, optimize=True)

    for file in sorted(OUT.glob("*.jpg")):
        print("BUKTI_B2", file, file.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
