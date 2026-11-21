"""Buat crop tanah 1:1 dari frame video render Nuh untuk audit layar ponsel."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from PIL import Image


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("-o", "--keluar", type=Path, default=Path("keluaran/crop-tanah-1x1.jpg"))
    ap.add_argument("--detik", type=float, default=2.0)
    args = ap.parse_args()

    args.keluar.parent.mkdir(parents=True, exist_ok=True)
    frame = args.keluar.with_suffix(".frame.png")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", str(args.detik), "-i", str(args.video),
         "-frames:v", "1", str(frame)],
        check=True,
    )
    with Image.open(frame) as im:
        im = im.convert("RGB")
        w, h = im.size
        side = min(w, 800)
        left = max(0, (w - side) // 2)
        # Area tanah tepat di bawah tokoh; koordinat mengikuti kanvas 1080x1920.
        top = min(max(0, 1000), h - side)
        crop = im.crop((left, top, left + side, top + side))
        crop.save(args.keluar, "JPEG", quality=95, optimize=True)
    frame.unlink(missing_ok=True)
    print(f"CROP_TANAH_1X1={args.keluar} ukuran={side}x{side}")


if __name__ == "__main__":
    main()
