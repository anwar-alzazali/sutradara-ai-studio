# Sutradara AI Studio

Mesin produksi video pendek **Kisah Islami** yang bertindak seperti sutradara: naskah → rencana penyutradaraan → visual bercerita, dengan dalil terverifikasi dan tokoh suci tidak pernah digambar.

- Aturan kerja: [AGENTS.md](AGENTS.md)
- Roadmap & status: [docs/ROADMAP.md](docs/ROADMAP.md)
- Keputusan visual: [docs/PANDUAN_GAYA.md](docs/PANDUAN_GAYA.md)
- Resep penyutradaraan: [docs/RESEP_SUTRADARA.md](docs/RESEP_SUTRADARA.md)

## Mulai cepat
```bash
pip install -r requirements.txt
python -m playwright install chromium        # atau set CHROME_PATH ke Chrome yang terpasang
python -m pytest -q
python -m sutradara periksa contoh/nuh_mengejek.json
python -m sutradara gambar contoh/dajjal_dua_sungai.json -o keluaran --semua
```

Font: Nunito & Amiri Quran (SIL Open Font License, lihat `aset/font/`).
