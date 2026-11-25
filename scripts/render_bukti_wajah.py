"""Buat bukti PNG before-after renderer wajah pada commit dasar PR."""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "keluaran-bukti" / "wajah"
CASES = [
    ("depan-senyum", {"arah": "depan", "wajah": "senyum"}),
    ("depan-marah", {"arah": "depan", "wajah": "marah"}),
    ("depan-kaget", {"arah": "depan", "wajah": "kaget"}),
    ("profil-curiga", {"arah": "samping", "wajah": "curiga"}),
    ("depan-heran", {"arah": "depan", "wajah": "heran"}),
]


def renderer_svg(cwd: Path, env: dict[str, str], kwargs: dict) -> str:
    code = (
        "import json; from sutradara.gaya import tokoh; "
        "print(json.dumps(tokoh.orang(500, 1500, kepala='tanpa', "
        "jenis='pria', janggut='tanpa', model_rambut='pendek', "
        "t=0.5, **json.loads(" + repr(json.dumps(kwargs)) + "))))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=cwd, env=env,
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, help="SHA commit dasar PR")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="renderer-wajah-base-") as temp:
        base_dir = Path(temp)
        subprocess.run(
            ["git", "fetch", "--no-tags", "--depth=1", "origin", args.base],
            cwd=ROOT, check=True,
        )
        archive = subprocess.run(
            ["git", "archive", args.base], cwd=ROOT, check=True,
            capture_output=True,
        )
        with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
            tar.extractall(base_dir, filter="data")

        env_base = dict(os.environ)
        env_base["PYTHONPATH"] = str(base_dir)
        env_new = dict(os.environ)
        env_new["PYTHONPATH"] = str(ROOT)

        before_after = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 480, "height": 480}, device_scale_factor=1)
            for name, expression in CASES:
                common = dict(expression)
                svg_before = renderer_svg(base_dir, env_base, common)
                svg_after = renderer_svg(ROOT, env_new, common)
                for version, fragment in (("sebelum", svg_before), ("sesudah", svg_after)):
                    document = (
                        '<html><body style="margin:0;background:#f5eee5">'
                        '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="480" '
                        'viewBox="380 1060 240 240">'
                        '<rect x="380" y="1060" width="240" height="240" fill="#f5eee5"/>'
                        + fragment + "</svg></body></html>"
                    )
                    page.set_content(document, wait_until="load")
                    path = OUT / f"{version}-{name}.png"
                    page.screenshot(path=str(path))
                    before_after.append((name, version, Image.open(path).convert("RGB")))
            browser.close()

    tile_w, tile_h, label_h = 360, 360, 34
    sheet = Image.new("RGB", (tile_w * 2, (tile_h + label_h) * len(CASES)), "#e9e1d8")
    draw = ImageDraw.Draw(sheet)
    by_key = {(name, version): image for name, version, image in before_after}
    for row, (name, _) in enumerate(CASES):
        y = row * (tile_h + label_h)
        draw.text((12, y + 10), f"{name} — SEBELUM", fill="#241d18")
        draw.text((tile_w + 12, y + 10), f"{name} — SESUDAH", fill="#241d18")
        for col, version in enumerate(("sebelum", "sesudah")):
            tile = by_key[(name, version)].resize((tile_w, tile_h))
            sheet.paste(tile, (col * tile_w, y + label_h))
    sheet.save(OUT / "perbandingan-wajah.png", optimize=True)
    for path in sorted(OUT.glob("*.png")):
        print(f"BUKTI_WAJAH {path.relative_to(ROOT)} {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
