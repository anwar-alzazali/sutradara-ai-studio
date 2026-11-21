"""Ukur overhead tekstur tanah lewat Chromium pada shot Nuh dan Dabbah."""
from __future__ import annotations

import json
import time
from pathlib import Path
import sys
import tempfile

AKAR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AKAR))

from sutradara import adegan
from sutradara.gaya import dasar
from sutradara.render import peramban

OUT = Path("keluaran-bukti/tahap-b")
OUT.mkdir(parents=True, exist_ok=True)


def ukur(pg, nama: str, shot: dict, tekstur: bool, frames: int = 36) -> float:
    spec = dict(shot)
    if not tekstur:
        spec["permukaan_tanah"] = "tanpa"
    mulai = time.perf_counter()
    for i in range(frames):
        # t berubah seperti render sungguhan; pola tanah tetap harus identik.
        svg = adegan.susun(spec, i / 12)
        pg.evaluate("s => { document.getElementById('k').innerHTML = s; }", svg)
        if i == 0:
            pg.evaluate("document.fonts.ready")
        pg.screenshot(type="jpeg", quality=88)
    return time.perf_counter() - mulai


def main():
    nuh = json.loads(Path("contoh/nuh_mengejek.json").read_text(encoding="utf-8"))
    dabbah = json.loads(Path("contoh/dabbah_dhuha.json").read_text(encoding="utf-8"))
    sampel = {
        "Nuh": nuh["beat"][0]["shot"][0],
        "Dabbah": dabbah["beat"][1]["shot"][0],
    }
    hasil = {}
    with tempfile.TemporaryDirectory() as tmp, peramban() as pg:
        halaman = Path(tmp) / "ukur.html"
        halaman.write_text(dasar.html('<div id="k"></div>'), encoding="utf-8")
        pg.goto(halaman.as_uri())
        for nama, shot in sampel.items():
            # Pemanasan singkat agar biaya peluncuran Chromium tidak masuk hitungan.
            ukur(pg, nama, shot, False, frames=3)
            tanpa = ukur(pg, nama, shot, False)
            dengan = ukur(pg, nama, shot, True)
            hasil[nama] = {
                "frames_per_mode": 36,
                "tanpa_tekstur_seconds": round(tanpa, 3),
                "dengan_tekstur_seconds": round(dengan, 3),
                "tambahan_seconds": round(dengan - tanpa, 3),
                "overhead_percent": round((dengan / tanpa - 1) * 100, 2) if tanpa else None,
                "tambahan_ms_per_frame": round((dengan - tanpa) * 1000 / 36, 2),
            }
    laporan = {
        "metode": "Chromium yang sama, 36 frame per mode, kualitas JPEG 88; mencakup susun SVG dan screenshot",
        "catatan": "Pengukuran runner CI; angka dipengaruhi beban mesin dan bukan jaminan perangkat pengguna.",
        "hasil": hasil,
    }
    tujuan = OUT / "benchmark-tekstur.json"
    tujuan.write_text(json.dumps(laporan, ensure_ascii=False, indent=2), encoding="utf-8")
    print("BENCHMARK_TEKSTUR_TANAH", json.dumps(laporan, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
