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
 penjaga dalil  ── Quran Foundation (ayat) · sunnah.com / dataset hadis (derajat)   [fase 3 ✔]
        │
        ▼
 SUTRADARA  ── menyusun RENCANA (resep G): visual inti + jalur keadaan, preset suasana,
        │      peran → cara tampil, hook, beat → shot, potong di kata kunci            [fase 4]
        ▼
 penjaga rencana (sutradara/rencana/penjaga.py) ── batas wajib, tidak bisa ditawar  [fase 0 ✔]
        │
        ├──► suara: narasi + efek ElevenLabs, waktu per kata                         [fase 2]
        ▼
 adegan bergerak: shot (SVG) + kamera + gerak dalam shot, sinkron waktu kata         [fase 1 ✔, sinkron kata fase 2]
        │
        ▼
 render: Chromium → frame → ffmpeg → MP4                                             [fase 0 PNG ✔, fase 1 MP4 ✔]
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
| `sutradara/waktu.py`, `kamera.py`, `video.py` | keyframe, kamera, render MP4 + lembar kontak |
| `sutradara/dalil/` | dataset hadis (sunnah.com), Quran Foundation, verifikasi dalil |
| `contoh/` | tiga rencana contoh: Nuh diejek, Dabbatul Ard, Dajjal dua sungai |

---

## Fase

Status: ✔ selesai · ▶ aktif · ○ belum. **Kriteria selesai selalu berupa bukti yang bisa dilihat/didengar.**

### ✔ Fase 0 — Fondasi (21 Nov 2026)
- Repo, CI gratis (runner public), aturan `AGENTS.md`, panduan gaya, resep sutradara.
- Pustaka gaya v0 sesuai keputusan pemilik; skema rencana + penjaga (11 tes aturan); render PNG.
- **Bukti:** `python -m sutradara gambar contoh/*.json` menghasilkan 8 shot; CI hijau.

### ✔ Fase 1 — Adegan bergerak, MP4 tanpa suara (21 Nov 2026)
- Angka mana pun di shot bisa keyframe `[[detik, nilai], …]` dengan kurva halus (`sutradara/waktu.py`).
- Kamera (`sutradara/kamera.py`): zoom/x/y beranimasi, `hentak` (kata kontras), `guncang` (dampak), pola bernama. Teks tidak ikut kamera.
- Gerak hidup (resep B5) memakai waktu global: butiran nur melayang & sinar berdenyut, kabut bergulung + `keluar` 0..1,
  api menjilat & air berkilau, tokoh bernapas/terguncang tertawa. Lapis depan tidak ikut zoom, bergeser parallax.
- Teks judul/subtitle muncul di detik tertentu dengan pop singkat.
- `python -m sutradara video rencana.json -o x.mp4 --lembar` → Chromium → ffmpeg H.264 veryfast + lembar kontak.
- **Bukti:** `contoh/nuh_mengejek.json` → MP4 15,5 dtk, 4 shot, kapal bertambah papan dari rangka sampai jadi.
- Catatan kecepatan: ±10 dtk render per 1 dtk video (30 fps, 1 peramban). Paralel per shot dikerjakan bila mengganggu (fase 6).

### ▶ Fase 2 — Suara dan waktu kata (mesin selesai 21 Nov 2026; tinggal uji suara asli)
Dibawa dari mesin-video (narasi_api.py, dlib.py, campur_rekaman, 47 efek `aset/suara`) lalu disempurnakan:
1. ✔ `sutradara/suara/narasi.py`: SATU permintaan ElevenLabs (with-timestamps) untuk seluruh video, cache per sidik isi
   (naskah+suara+model+setelan+lafal), kamus lafal dikembalikan ke tulisan asli di subtitle, penjaga Arab sebelum kirim.
2. ✔ `sutradara/garis_waktu.py`: durasi shot dari waktu kata; potongan 0,1 dtk sebelum kata `potong_di`
   (imbuhan -nya/-lah/... dikenali); semua waktu koreografi di dalam shot diskala ke durasi baru; kartu dalil =
   sisipan sesudah narasi beat (narasi diam selama dibaca); titik potong dibulatkan ke bingkai global.
3. ✔ Subtitle dari waktu kata: frasa putus di tanda baca/jeda/5 kata, kata yang diucapkan kuning, frasa panjang 2 baris.
4. ✔ `sutradara/suara/campur.py`: suasana per preset, efek dari peristiwa yang dirancang (hentak, guncang, kartu),
   whoosh di pergantian beat, efek bebas per beat di `@kata`, musik opsional; ducking sidechain; -15 LUFS, TP -1,5.
4b. ✔ **Efek terikat aksi** (permintaan pemilik): bunyi mengikuti yang sedang dilakukan di layar. Satu ketukan/langkah
   (`aset/suara/satu`, dipotong dari rekaman asli oleh `suara/sampel.py`) di setiap titik kena gerak palu/gali/jalan/
   lari/lompat, keras-pelan menurut ukuran tokoh, kiri-kanan menurut posisi; bahtera yang sedang bertambah papan
   berbunyi palu; efek satu-kali berhenti di akhir shotnya kecuali `"lewat": true`. Gerak baru `gali` (beliung dua
   tangan) + alat di tangan (palu/beliung) otomatis dari jadwal gerak.
5. ✔ Workflow `suara.yml` (hanya `workflow_dispatch`) -> cabang `suara`; `python -m sutradara naskah` mengecek gratis dulu.
- **Catatan:** bunyi `gali` sementara dipotong dari `tanah_retak`; bunyi beliung-menghantam-batu yang tepat perlu
  dibuat lewat ElevenLabs sound-generation (kredit kecil) saat adegan Ya'juj dikerjakan.
- **Sisa:** narasi asli Nuh setelah naskah disetujui pemilik -> render bersuara -> dengar di ponsel & headphone.
- **Kriteria selesai:** video Nuh dengan narasi, potongan di kata kunci (diuji otomatis), tanpa clipping (diukur), disetujui pemilik.

### ✔ Fase 1b — Tokoh bergerak (21 Nov 2026, permintaan pemilik)
- Tokoh dibangun ulang dengan **rangka bersendi** (`sutradara/gaya/tokoh.py`): panggul, badan, kepala, lengan atas/bawah,
  paha/betis; gamis mengikuti bahu-pinggul-lutut (berayun saat jalan, menjuntai saat duduk), celana + kaki terlihat.
- **Pustaka gerak** (`sutradara/gerak.py`): jalan, lari, joget, lompat, duduk (+bangku otomatis), melambai, palu,
  menggeleng, mengangguk, tertawa; pose: berdiri, tunjuk, angkat, silang, kaget, mundur, tutup (mulut), tutup_telinga,
  tutup_wajah, berdoa, menengadah, lemas, pinggang, dagu (berpikir), kepala (bingung).
  Gestur yang menyentuh tubuh memakai **IK**: tangan diarahkan ke titik tujuan (telinga, mulut, wajah, pinggang).
- **Ekspresi**: datar, senyum, tertawa, ejek, cemberut, sedih, marah, takut, kaget, pejam; kedip otomatis; mulut bicara.
- Jadwal di shot: `"gerak": [[0, "jalan"], [2.2, "tunjuk"]]`, `"wajah": [[0, "datar"], [2.2, "ejek"]]`,
  `"bicara": [[2.3, 3.4]]`, posisi `x` beranimasi untuk berjalan melintas. Perpindahan gerak dicampur halus 0,35 dtk.
- Tokoh wanita (`"jenis": "wanita"`): kerudung, tanpa janggut.
- **Bukti:** `contoh/demo_gerak.json` (11,5 dtk: berjalan masuk lalu melambai, duduk sambil bicara, joget, lompat,
  tertawa, kaget→mundur, menutup telinga, lari keluar); 47 tes gerak/ekspresi baru.
- Berikutnya: gerak dipicu kata kunci narasi (fase 2), set pose khusus tokoh (Dajjal berjalan, dsb., fase 7).

### ✔ Fase 3 — Penjaga dalil (21 Nov 2026, dikerjakan sebelum fase 2 atas permintaan pemilik)
- **Hadis** (`sutradara/dalil/hadis.py`): dataset lokal dari github.com/fawazahmed0/hadith-api (Unlicense, teks sunnah.com),
  6 kitab (Bukhari, Muslim, Abu Dawud, Tirmidzi, Nasa'i, Ibnu Majah), Arab + Indonesia + Inggris + penilaian derajat.
  Penomoran = sunnah.com (Muslim memakai `arabicnumber` Fuad Abdul Baqi, riwayat berhuruf 2934a/b). Dibangun dengan
  `python -m sutradara.dalil.unduh_hadis` ke `data/hadis/` (±18 MB, tidak masuk git; di CI disimpan di cache).
- **Derajat**: Bukhari/Muslim sahih; kitab lain menurut Al-Albani (mursal/munkar/maudu/syadz = ditolak); tanpa Al-Albani
  = mayoritas, seri ditolak. Penilai lain yang menolak dicatat (`DERAJAT_DIPERSELISIHKAN`); mauquf/maqtu ditandai (`BUKAN_MARFU`).
- **Ayat** (`sutradara/dalil/quran.py`): Quran Foundation API (port dari motion-studio-ai), terjemah Kemenag, cache 7 hari.
- **Verifikasi** (`python -m sutradara verifikasi rencana.json`, workflow `verifikasi dalil`): mengisi status, derajat,
  teks Arab, terjemah, tautan, tanda `diverifikasi_oleh`. Penjaga `--final` menolak status yang diketik tangan,
  dalil tanpa rujukan terstruktur, hadis daif, nomor tidak ditemukan, dan kitab di luar dataset (mis. Musnad Ahmad).
- Makna pemakaian dalil tetap `perlu_tinjauan_pemilik`.
- **Bukti:** 9 tes dalil; Bukhari 7123 & Muslim 2934/2941 terverifikasi dari dataset; ayat diverifikasi lewat workflow (butuh rahasia QF).

### ✔ Fase 3b — Kartu dalil bertahap (21 Nov 2026, permintaan pemilik)
- Bukan satu kartu besar yang menutupi layar: pita ATAS tembus pandang (warna ikut preset suasana) berisi SATU potongan (Arab <= 2 baris + terjemah <= 2 baris),
  Arab disapu kanan->kiri, terjemah diketik, lalu diganti potongan berikutnya (`sutradara/gaya/kartu.py`).
- Pemotongan (`sutradara/dalil/segmen.py`): terjemah dipotong lebih dulu di akhir kalimat/kata sambung, Arab di tanda
  waqaf/kata sambung و ف pada proporsi yang sama. Gabungan potongan = teks utuh terverifikasi (dites). Pasangan
  Arab-terjemah = perkiraan (tidak ada pemetaan kata resmi).
- Hadis memakai `kutipan_ar`/`kutipan_id` (matan saja, tanpa sanad) yang WAJIB potongan persis teks terverifikasi
  (`KUTIPAN_TIDAK_ADA_DI_SUMBER`). Label kartu hadis menyertakan derajat.
- Durasi shot kartu otomatis dari waktu baca (±13 huruf/dtk, min 2,6 dtk per potongan); di fase 2 disesuaikan narasi.
- Belum: bacaan latin ayat (transliterasi Quran Foundation) — ditunda sampai diminta.
- **Bukti:** contoh Nuh + kartu QS Hud 38 (4 potongan), contoh Dajjal + kartu HR Muslim 2934 (3 potongan); 5 tes.

### ○ Fase 4 — Sutradara otomatis v1
Inti "kecerdasan". Masukan: naskah terstruktur. Keluaran: rencana (resep G) yang lulus penjaga.
1. **Templat naskah** untuk AI gratis (ChatGPT/Gemini): per beat → narasi, kata kunci, dalil, suasana, peran. Templat juga
   mendorong mutu cerita: fakta terkuat di depan, cerita utuh, tanpa kalimat ulang.
2. **Keputusan tingkat video** (aturan + resep): visual inti & jalur keadaan, peta busur emosi → preset (penutup paling terang),
   peran → cara tampil (tabel PANDUAN_GAYA), hook = beat paling dramatis dipindah ke depan.
3. **Penataan panggung otomatis (blocking)**: pelaku aksi ditempatkan di samping visual inti, pihak lawan di sisi
   seberang/melintas di depan, posisi tiap pihak tetap antar-shot. Sekarang baru DICEK penjaga (`PELAKU_JAUH`,
   `BUKAN_PELAKU_DEKAT`); di fase ini sutradara yang MENENTUKAN koordinatnya, bukan ditulis tangan.
4. **Keputusan tingkat shot**: pecah enumerasi jadi shot per kata, eskalasi pada pengulangan (resep B2), kamera dari posisi
   beat (hook/isi/klimaks/penutup), teks layar 1–3 kata yang menamai makna.
5. **Perpustakaan resep adegan**: setiap video yang disetujui pemilik disimpan sebagai potongan siap pakai
   (mis. "azab datang", "doa sunyi", "kaum mengejek"). Sutradara memilih & merangkai resep.
6. Opsional, di belakang bendera: model murah (Haiku/Sonnet) untuk memilih resep bila aturan ragu. Biaya dicatat per video.
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

## Daftar kebutuhan berikutnya (dicatat 21 Nov 2026)
Pembagian kerja per tahap untuk pengembang AI lain (A–F, diaudit sebelum merge): `docs/TAHAP_LANJUT.md`.

Semua yang sudah disebut pemilik/sesi tetapi BELUM dikerjakan. Centang di PR yang menyelesaikannya; jangan hapus baris.

### Segera (fase 2 — suara & waktu kata)
- [ ] Narasi ElevenLabs satu permintaan per video + waktu per kata (port `mesin-video/narasi_api.py`, `papan/kisah/dlib.py`).
- [ ] Potong shot tepat di kata kunci (`potong_di`); teks layar, gerak tokoh, dan mulut bicara dipicu kata narasi.
- [ ] Subtitle per frasa (±4 kata, satu baris) dari waktu kata.
- [ ] Waktu kartu dalil mengikuti narasi (sekarang dari waktu baca).
- [ ] Efek suara berlapis + cache (resep D), campur ±-15 LUFS, puncak ≤ -1 dBTP; workflow `workflow_dispatch` saja.
- [ ] Pastikan nama rahasia `ELEVENLABS_API_KEY` & `ANTHROPIC_API_KEY` benar (baru `QURAN_FOUNDATION_*` yang terbukti terbaca).
- [ ] Render ulang video Nuh untuk tinjauan pemilik: kartu dalil di atas + warna suasana, kaum berjalan lalu mengejek, suara.

### Visual & tokoh
- [ ] Tampak samping / berbalik badan (berjalan menyamping, menoleh penuh); kini semua tokoh tampak depan.
- [ ] Kamera shot pembuka Nuh lebih dekat ke kapal (visual inti masih kecil di layar).
- [ ] Ragam tokoh: anak, lansia, pakaian per zaman/wilayah, variasi perempuan.
- [ ] Set pose Dajjal desain B: berjalan, dari belakang, jauh di tengah pengikut; jubah berkibar, lengan membuka perlahan.
- [ ] Ya'juj Ma'juj: manusia biasa, kengerian dari jumlah & gerak (turun dari setiap tempat tinggi, QS Al-Anbiya 96),
      menggali dinding, meminum habis danau; tanpa ciri ras/bentuk aneh.
- [ ] Buraq: hewan putih antara keledai & bagal, langkah sejauh pandangan; tanpa sayap, tanpa wajah manusia,
      tidak pernah dengan penunggang (penunggang = pilar cahaya).
- [ ] Dabbatul Ard adegan lanjutan: "berbicara kepada manusia" (teks + narator), tanda di wajah orang pasar (abstrak, berlabel ilustrasi).

### Dalil
- [ ] Bacaan latin ayat di kartu (transliterasi Quran Foundation) — hanya bila pemilik meminta.
- [ ] Musnad Ahmad belum ada di dataset (mis. Ahmad 22308, tanda di wajah oleh Dabbah) — cari sumber berlisensi jelas.
- [ ] Pakai scope `content.hadith.read` Quran Foundation sebagai pemeriksa hadis kedua.
- [ ] Terjemah hadis dataset kadang keliru (mis. Muslim 2934b: "surga" padahal النهر = sungai): tandai untuk tinjauan pemilik,
      pertimbangkan terjemah sendiri yang ditinjau.
- [ ] Pasangan Arab–terjemah di kartu masih perkiraan; pertimbangkan pemetaan kata (word-by-word) Quran Foundation.

### Mesin & otomatisasi
- [ ] Fase 4 sutradara otomatis: templat naskah untuk AI gratis, keputusan visual inti/preset/peran/hook, **penataan panggung
      otomatis** (pelaku di samping visual inti), gerak & ekspresi dari kata kerja narasi, perpustakaan resep adegan.
- [ ] Fase 5 kritikus: periksa teknis (port `periksa.py`), lembar kontak otomatis, kritik visual opsional.
- [ ] Fase 6: workflow `buat_video` → kirim Telegram → persetujuan; tugas terjadwal harian; laporan biaya.
- [ ] Percepat render (sekarang ±10 dtk kerja per 1 dtk video untuk adegan berat): paralel per shot di Actions.

### Rumah tangga repo
- [ ] Hapus cabang yang sudah digabung di repo ini (`fondasi`, `fase1-gerak`, …) — sesi pengembang tidak bisa menghapus cabang.
- [ ] mesin-video: 252 cabang sudah diarsip di cabang `arsip-cabang`; penghapusannya menunggu keputusan pemilik
      (usulan: workflow `workflow_dispatch` yang menghapus semua kecuali `main`, `feat/short-term-production-intelligence`,
      `narasi`, `efek`, `arsip-cabang`).
- [ ] Tagihan GitHub akun: run mesin-video 20 Nov gagal karena "recent account payments have failed or spending limit";
      repo ini (public) tidak terdampak, tetapi cek *Billing & plans*.

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
- 21 Nov 2026 — Fase 1: lapis depan dikeluarkan dari kamera (kalau ikut zoom, batu jadi bercak hitam besar).
- 21 Nov 2026 — Penataan panggung: pemilik melihat NPC lebih dekat ke kapal daripada Nabi Nuh. Contoh diperbaiki dan aturan dijadikan pemeriksaan penjaga.
- 21 Nov 2026 — Fase 3 didahulukan. Dataset hadis tidak dimasukkan ke git (±18 MB); dibangun ulang dari sumber + cache CI. Rahasia: QURAN_FOUNDATION_CLIENT_ID/_SECRET, ELEVENLABS_API_KEY, ANTHROPIC_API_KEY.
- 21 Nov 2026 — Kunci Quran Foundation valid di produksi tetapi belum diberi scope `content` (diagnosa: 403 'access token does not have the required scopes'). Sementara verifikasi ayat otomatis memakai API publik quran.com (penyedia sama), ditandai di `sumber_teks`. Ternyata scope sudah diberikan dalam bentuk RINCI (`content.quran.read`, `content.translations.read`, …); kode kini memintanya dan jalur resmi berkunci terbukti jalan (HTTP 200). Cadangan publik tetap ada untuk gangguan.
- 21 Nov 2026 — Kartu dalil dipindah ke atas, lebih transparan, warna ikut suasana (permintaan pemilik). Render ulang ditunda sampai uji suara.
- 21 Nov 2026 — Struktur inti vs paket genre (`kisah_islami` dulu) dipisah di awal Tahap D, sebelum resep sutradara dibangun, agar genre lain kelak tidak menyentuh inti. Genre lain tetap belum dibangun.
- 21 Nov 2026 — Fase 1b didahulukan (permintaan pemilik). Tokoh lama (pose diam) diganti rangka bersendi; nama pose lama tetap berlaku.
