# Bukti render Tahap D1

- `nuh.mp4`: salinan bukti 360×640 dari render penuh `naskah/nuh.json`, tanpa TTS, 1 fps; 52 detik.
- `hud.mp4`: salinan bukti 360×640 dari render penuh `naskah/hud.json`, tanpa TTS, 1 fps; 28 detik.
- `nuh-kontak.jpg` dan `hud-kontak.jpg`: 16 bingkai merata dari masing-masing MP4.
- `perbandingan-nuh.jpg`: kontak Nuh otomatis di atas, rencana manual acuan `contoh/nuh_mengejek.json` di bawah.

Untuk poin 0b, 60 sampel PNG (awal/tengah/akhir tiap shot dari enam rencana contoh) pada `main` dan head awal PR
memiliki SHA-256 identik. Tes hook genre tiruan juga tetap lulus; inti garis waktu/pencampur suara tidak menyebut
`kartu_dalil` atau `kilau_cahaya`.

Dalil kedua naskah diperiksa dengan `python -m sutradara verifikasi`; `python -m sutradara periksa ... --final`
memberi `LULUS: tidak ada temuan` untuk keduanya. Video bukti ini menguji jalur naskah → rencana → renderer
tanpa memanggil TTS atau model. Perbandingan visual memperlihatkan transisi keadaan, blocking, kelompok,
shot dialog, dan pilar cahaya; penilaian layak tayang tetap milik pemilik.

Perintah reproduksi dari akar repo:

```powershell
python -m sutradara sutradarai naskah/nuh.json -o keluaran/d1/nuh.json
python -m sutradara verifikasi keluaran/d1/nuh.json
python -m sutradara periksa keluaran/d1/nuh.json --final
python -m sutradara video keluaran/d1/nuh.json -o keluaran/d1/nuh.mp4 --fps 1 --lembar
```

Ulangi empat perintah terakhir dengan `hud.json` untuk Hud. Saat mengulang di PowerShell lokal, tetapkan
`CHROME_PATH` ke Chrome yang terpasang bila Playwright Chromium belum dipasang.
