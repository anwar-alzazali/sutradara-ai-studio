# Roadmap Sutradara AI Studio

Tujuan: **mesin yang bertindak seperti sutradara**. Naskah masuk, lalu keluar video Kisah Islami yang visualnya bercerita,
dalilnya terverifikasi, dan mutunya mendekati video yang dulu disutradarai manual oleh Claude di sesi chat
(Nabi Nuh, Ya'juj Ma'juj). Biaya serendah mungkin: kreativitas dibakukan jadi resep + aturan, model AI hanya di titik yang perlu.

Ukuran keberhasilan proyek: **video yang disetujui pemilik**, bukan jumlah kode, tes, atau dokumen.

---

## Arsitektur

```
 naskah terstruktur (pengguna + AI gratis memakai templat)          [fase 4]
        │
        ▼
 penjaga dalil  ── Quran Foundation (ayat) · sunnah.com / dataset hadis (derajat)   [fase 3]
        │
        ▼
 SUTRADARA  ── menyusun RENCANA (resep G): visual inti + jalur keadaan, preset suasana,
        │      peran → cara tampil, hook, beat → shot, potong di kata kunci            [fase 4]
        ▼
 penjaga rencana (sutradara/rencana/penjaga.py) ── batas wajib, tidak bisa ditawar  [fase 0 ✔]
        │
        ├──► suara: narasi + efek ElevenLabs, waktu per kata                         [fase 2]
        ▼
 adegan bergerak: shot (SVG) + kamera + gerak dalam shot, sinkron waktu kata         [fase 1]
        │
        ▼
 render: Chromium → frame → ffmpeg → MP4                                             [fase 0 PNG ✔, fase 1 MP4]
        │
        ▼
 periksa teknis + KRITIKUS (lembar kontak) → perbaiki & render ulang (maks 2×)        [fase 5]
        │
        ▼
 kirim Telegram → persetujuan pemilik → unggah                                       [fase 6]
```

Lapisan yang sudah ada di repo:

| Paket | Isi |
|---|---|
| `sutradara/gaya/` | pustaka visual v0: tokoh berpakaian/siluet, pilar nur, kabut tanpa wujud, Dajjal desain B, latar preset, benda, teks |
| `sutradara/adegan.py` | menyusun satu shot (JSON → SVG 1080×1920) dengan urutan lapis tetap |
| `sutradara/rencana/` | skema rencana sutradara + penjaga keselamatan/resep |
| `sutradara/render.py` | SVG → PNG lewat Chromium headless |
| `contoh/` | tiga rencana contoh: Nuh diejek, Dabbatul Ard, Dajjal dua sungai |

---

## Fase

Status: ✔ selesai · ▶ aktif · ○ belum. **Kriteria selesai selalu berupa bukti yang bisa dilihat/didengar.**

### ✔ Fase 0 — Fondasi (21 Nov 2026)
- Repo, CI gratis (runner public), aturan `AGENTS.md`, panduan gaya, resep sutradara.
- Pustaka gaya v0 sesuai keputusan pemilik; skema rencana + penjaga (11 tes aturan); render PNG.
- **Bukti:** `python -m sutradara gambar contoh/*.json` menghasilkan 8 shot; CI hijau.

### ▶ Fase 1 — Adegan bergerak (MP4 tanpa suara)
Tujuan: satu rencana → MP4 yang hidup, belum bersuara.
1. Model waktu per shot: `mulai`, `durasi`, dan nilai beranimasi `[[detik, nilai], …]` untuk kamera (zoom/x/y),
   parameter keadaan visual inti (`jadi`, `lubang`, …), posisi tokoh, opasitas.
2. Kosakata kamera resep B3: dorong pelan, dekat, sangat dekat, tarik mundur, menjauh, `guncang`, `hentak`.
3. Gerak hidup resep B5: butiran nur melayang, kabut bergulung, api menjilat, hujan, kerumunan berjalan.
4. Render frame (Chromium, 30 fps) → ffmpeg H.264 `-preset veryfast`. Render paralel per shot di Actions bila lambat.
- **Kriteria selesai:** `contoh/nuh_mengejek.json` → MP4 ±15 dtk; kamera bergerak di setiap shot, kapal berubah dari
  rangka ke jadi, butiran cahaya bergerak. Lembar kontak + MP4 dilampirkan di PR, disetujui pemilik.
- Rujukan: animasi `[[t, v]]` dan kamera `K(...)` di `mesin-video/papan/cerita.js` (konsep, bukan disalin utuh).

### ○ Fase 2 — Suara dan waktu kata
1. Narasi ElevenLabs satu permintaan per video, ambil waktu per kata (salin dari `mesin-video/narasi_api.py`, `papan/kisah/dlib.py`).
2. Shot dipotong di kata kunci (`potong_di`), teks layar muncul tepat saat kata diucapkan (resep B1, C).
3. Subtitle per frasa/tanda baca (maks ±4 kata, satu baris).
4. Efek suara berlapis (resep D) dengan cache per prompt (salin konsep `efek.yml` + `aset/suara`), campur & normalisasi ±-15 LUFS, puncak ≤ -1 dBTP.
5. Workflow `buat_suara.yml` **hanya `workflow_dispatch`** (memakai rahasia ElevenLabs).
- **Kriteria selesai:** video Nuh ±30–45 dtk dengan narasi, potongan shot jatuh di kata kunci (dicek dari waktu kata), audio tidak clipping.

### ○ Fase 3 — Penjaga dalil
1. Ayat: Quran Foundation API (salin `motion-studio-ai/providers/quran_foundation.py`), cocokkan surah:ayat + teks Arab.
2. Hadis: sunnah.com API (minta kunci lewat issue di repo sunnah-com/api) atau dataset hadis lokal berlisensi jelas
   (mis. fawazahmed0/hadith-api) sebagai cadangan; simpan derajat & penilai.
3. `status` dalil di rencana diisi otomatis oleh modul ini, bukan diketik tangan. Rencana `--final` gagal bila ada dalil belum terverifikasi.
4. Pencocokan makna tetap ditandai "perlu tinjauan pemilik" (mesin hanya menjamin dalil ada, nomor benar, derajat sahih/hasan).
- **Kriteria selesai:** tes dengan dalil benar (lulus), nomor salah (gagal), hadis daif (gagal), kutipan karangan (gagal).

### ○ Fase 4 — Sutradara otomatis v1
Inti "kecerdasan". Masukan: naskah terstruktur. Keluaran: rencana (resep G) yang lulus penjaga.
1. **Templat naskah** untuk AI gratis (ChatGPT/Gemini): per beat → narasi, kata kunci, dalil, suasana, peran. Templat juga
   mendorong mutu cerita: fakta terkuat di depan, cerita utuh, tanpa kalimat ulang.
2. **Keputusan tingkat video** (aturan + resep): visual inti & jalur keadaan, peta busur emosi → preset (penutup paling terang),
   peran → cara tampil (tabel PANDUAN_GAYA), hook = beat paling dramatis dipindah ke depan.
3. **Keputusan tingkat shot**: pecah enumerasi jadi shot per kata, eskalasi pada pengulangan (resep B2), kamera dari posisi
   beat (hook/isi/klimaks/penutup), teks layar 1–3 kata yang menamai makna.
4. **Perpustakaan resep adegan**: setiap video yang disetujui pemilik disimpan sebagai potongan siap pakai
   (mis. "azab datang", "doa sunyi", "kaum mengejek"). Sutradara memilih & merangkai resep.
5. Opsional, di belakang bendera: model murah (Haiku/Sonnet) untuk memilih resep bila aturan ragu. Biaya dicatat per video.
- **Kriteria selesai:** naskah kisah Nabi Nuh → video otomatis penuh; pemilik menilai "layak tayang" dibanding versi manual.
  Lalu satu kisah baru (mis. Nabi Hud) juga layak tanpa campur tangan kode.

### ○ Fase 5 — Periksa & kritikus
1. Periksa teknis (salin `mesin-video/periksa.py`): resolusi, durasi, audio hilang, clipping, layar kosong, teks terpotong.
2. Lembar kontak otomatis (16 bingkai) + kritik terhadap resep: visual inti tidak berubah, shot terlalu mirip berturut-turut,
   teks menumpuk, tokoh keluar layar.
3. Opsional: kritikus visual memakai model AI yang melihat lembar kontak (konsep `mesin-video` cabang `kritikus-visual`), maks 2 putaran perbaikan.
- **Kriteria selesai:** cacat yang disengaja (teks bertumpuk, shot kosong) tertangkap dan diperbaiki otomatis pada video uji.

### ○ Fase 6 — Otomatisasi penuh
1. Workflow `buat_video.yml` (`workflow_dispatch`, input: naskah) menjalankan fase 2–5 lalu mengirim ke Telegram (salin konsep cabang `kiriman`).
2. Antrean naskah + tugas terjadwal (satu video per hari) yang hanya mengirim untuk disetujui; tidak pernah mengunggah sendiri.
3. Laporan biaya per video (ElevenLabs, model AI).
- **Kriteria selesai:** 5 hari berturut-turut video harian sampai ke Telegram tanpa sentuhan manual, ≥3 disetujui pemilik.

### ○ Fase 7 — Perluasan (baru dibuka setelah fase 6 terbukti)
- Set pose per tokoh (Dajjal: berjalan, dari belakang, jauh di tengah pengikut; Ya'juj Ma'juj; Buraq tanpa penunggang).
- Pustaka tokoh lebih kaya (perempuan berkerudung, anak, lansia, pakaian per zaman).
- Genre lain (edukasi, cerita anak) sebagai "engine" terpisah di atas fondasi yang sama.

---

## Yang sengaja TIDAK dibawa dari repo lama
- Penyimpanan tugas SQLite, buku catatan operasi, registri & matriks engine, ratusan dokumen audit (`feat/short-term-production-intelligence`).
- Boneka "kamu" sebagai avatar penonton; siluet sebagai tampilan bawaan; nur berbentuk lampu sorot.
- Bot & Studio lama, film3d, cabang hasil per video, berkas audio/video lama.

## Log keputusan
- 21 Nov 2026 — Repo baru tanpa riwayat; mesin-video & motion-studio-ai jadi arsip rujukan.
- 21 Nov 2026 — Gaya visual dikunci (lihat PANDUAN_GAYA): tokoh berpakaian, NPC jauh pudar oleh kabut, nur = pilar cahaya,
  Dabbah = kabut tanah gelap, Dajjal = desain B (ciri hadis tampil), Ya'juj Ma'juj = manusia.
- 21 Nov 2026 — Sutradara berbasis resep + aturan; model AI hanya opsional (biaya). Naskah boleh dibuat pengguna dengan AI gratis.
- 21 Nov 2026 — Repo public: runner Actions gratis; workflow berahasia hanya `workflow_dispatch`.
