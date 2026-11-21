"""CLI.

  python -m sutradara periksa contoh/nuh_mengejek.json          # cek rencana (skema + penjaga)
  python -m sutradara gambar contoh/nuh_mengejek.json -o keluaran # render shot pertama tiap beat ke PNG
  python -m sutradara video contoh/nuh_mengejek.json -o keluaran/nuh.mp4 [--fps 30] [--lembar]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import adegan, render, video
from .rencana import periksa, ringkas


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sutradara")
    sub = ap.add_subparsers(dest="perintah", required=True)
    a = sub.add_parser("periksa"); a.add_argument("rencana"); a.add_argument("--final", action="store_true")
    b = sub.add_parser("gambar"); b.add_argument("rencana"); b.add_argument("-o", "--keluar", default="keluaran")
    b.add_argument("--semua", action="store_true", help="render semua shot, bukan hanya shot pertama tiap beat")
    c = sub.add_parser("video"); c.add_argument("rencana"); c.add_argument("-o", "--keluar", default="keluaran/video.mp4")
    c.add_argument("--fps", type=int, default=30); c.add_argument("--lembar", action="store_true", help="buat juga lembar kontak .jpg")
    arg = ap.parse_args(argv)

    r = json.loads(Path(arg.rencana).read_text(encoding="utf-8"))
    temuan = periksa(r, final=getattr(arg, "final", False))
    print(ringkas(temuan))
    if any(x.tingkat == "GAGAL" for x in temuan):
        return 1
    if arg.perintah == "gambar":
        out = Path(arg.keluar)
        with render.peramban() as pg:
            for i, bt in enumerate(r["beat"]):
                for j, s in enumerate(bt["shot"] if arg.semua else bt["shot"][:1]):
                    f = render.png(adegan.susun(s), out / f"b{i:02d}_s{j}.png", halaman=pg)
                    print("ditulis", f)
    if arg.perintah == "video":
        mp4 = video.buat(r, Path(arg.keluar), fps=arg.fps)
        if arg.lembar:
            print("lembar kontak:", video.lembar(mp4, mp4.with_suffix(".jpg")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
