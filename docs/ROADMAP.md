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
| `sutradara/genre.py` | kontrak `PaketGenre`, registri, fallback rencana lama, dan pemuatan paket secara dinamis |
| `sutradara/paket_genre/kisah_islami/` | adapter, renderer adegan, komponen visual, validator, ekstensi skema, modul dalil, bawaan, panduan gaya, dan resep Kisah Islami |
| `sutradara/gaya/` | primitif inti yang netral: rig tokoh, latar, teks; modul visual genre lama dipertahankan sebagai shim kompatibilitas |
| `sutradara/adegan.py` | komposisi shot netral-genre; elemen adegan datang dari renderer dan registri komponen paket |
| `sutradara/rencana/` | skema umum dan pemeriksaan kontinuitas/geometri; aturan domain dan ekstensi skema dimiliki paket |
| `sutradara/dalil/` | shim impor lama; implementasi Quran Foundation, hadis, koreksi, dan verifikasi berada di paket Kisah Islami |
| `sutradara/render.py` | SVG → PNG lewat Chromium headless |
| `sutradara/waktu.py`, `kamera.py`, `video.py` | keyframe, kamera, render MP4 + lembar kontak |
| `contoh/` | rencana contoh untuk pengujian lintas renderer dan genre |


Rencana lama tanpa kolom `genre` tetap memakai paket `kisah_islami` sebagai fallback kompatibilitas. Paket lain dapat memasok validator, ekstensi skema, renderer adegan, data render, durasi, dan komponen sendiri tanpa menambahkan cabang elemen genre ke inti. Nilai `kategori` dan `tampil` pada skema inti bersifat string; daftar yang sah ditetapkan oleh ekstensi skema paket.

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
  waqaf/kata sambung و ف pada proporsi yang sama. Gabungan potongan = teks utuh terverifikasi (dites). Pasangan Arab-terjemah awalnya perkiraan; Tahap C menambahkan
  pasangan word-by-word Quran Foundation bila seluruh token kata memiliki terjemah, dengan fallback aman bila tidak.
- Hadis memakai `kutipan_ar`/`kutipan_id` (matan saja, tanpa sanad) yang WAJIB potongan persis teks terverifikasi
  (`KUTIPAN_TIDAK_ADA_DI_SUMBER`). Label kartu hadis menyertakan derajat.
- Durasi shot kartu otomatis dari waktu baca (±13 huruf/dtk, min 2,6 dtk per potongan); di fase 2 disesuaikan narasi.
- Fondasi transliterasi Quran Foundation disiapkan di balik bendera mati; tidak dipanggil/ditampilkan sampai pemilik meminta.
- **Bukti:** contoh Nuh + kartu QS Hud 38 (4 potongan), contoh Dajjal + kartu HR Muslim 2934 (3 potongan); 5 tes.

### ○ Fase 4 — Sutradara otomatis v1
**Penegasan keputusan pemilik (24 Nov 2026):** sutradara harus membangun visual dari peristiwa yang tertulis pada setiap beat, bukan sekadar memilih ulang resep visual Nuh. Jalur produksi utama bersifat deterministik dan tidak memerlukan arahan model AI; model opsional hanya boleh membantu kasus ambigu di D3. Keadaan benda/lingkungan mengikuti peristiwa yang disebut naskah, dan keputusan shot harus dapat ditelusuri ke narasi. Nuh dan Hud tetap bukti wajib; Mahsyar 1 menjadi uji tambahan lintas cerita.

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

**Implementasi Tahap D1 (PR #45):** format antrean divalidasi dan dirancang oleh paket genre; inti hanya menyediakan
kontrak, CLI, dan pemeriksaan umum. Keputusan paket Kisah Islami mencakup visual inti/jalur keadaan, preset, peran,
hook, resep data, tata panggung, dialog, arah hadap, dan lintasan jalan/lari. Model bersifat opsional, mati secara
  bawaan, menerima adapter yang diinjeksi lewat `--adapter modul:fungsi`, dan biaya agregat dicatat tanpa prompt atau rahasia. Bukti render Nuh/Hud
dan batas cakupan D1 tercatat di deskripsi PR; penilaian layak tayang tetap keputusan pemilik.

**Tambahan implementasi visual dari peristiwa naskah pada HEAD PR #48 (24 Nov 2026):** parser peristiwa menyertakan aksi, peran, sasaran, perubahan keadaan eksplisit, dan bukti frasa. Panggung padang dipilih dari deskripsi ruang, dan komponen SVG berbasis peristiwa tersedia untuk tanah terbelah, matahari dekat, kerumunan, keringat, serta jejak pelarian. Tes unit memakai frasa Mahsyar 1. Ini belum merupakan render MP4, belum membuktikan keseluruhan naskah, dan belum mengganti seluruh resep/keadaan khusus Nuh/Ya'juj. Status D2 tetap belum selesai sampai cakupan visual generik, tes regresi, render, dan tinjauan manusia terbukti.

**Status Tahap D2 pada PR #48: belum dicentang / belum selesai.** Implementasi mencakup (3) blocking otomatis dari visual inti, penempatan pihak lawan, pemeriksaan kedekatan pelaku dan kontinuitas panggung; (3b) shot–reverse shot dengan sisipan reaksi pendengar; (3c) arah hadap interaksi dan tiga-perempat; (3d) tujuan serta lintasan x/y, cadence, konsistensi 180 derajat, pengejaran kanan/kiri dengan kedua tokoh searah, dan putar balik sesuai cerita.

**Bukti CI #529 pada HEAD `76c068e` (run `45207029799`):** sukses dengan 320 tes Python, tes bot Telegram, render D2 14 shot / 644 bingkai / 53,7 detik (95 detik waktu render, 1 worker), dan pemeriksaan enam contoh tanpa GAGAL. Lembar kontak dan MP4 diunggah. Bukti statis tidak menggantikan pemeriksaan gerak kontinu dan variasi artistik oleh pemilik.

**Uji audio-cache pada HEAD `76c068e` (run `45284285899`):** sukses dengan 29 kata terjajar, MP3 13,52 detik, padding hening 0,43 detik, video 15,12 detik, stream audio-video 15,11 detik (selisih 0,01 detik), -16,89 LUFS, dan -1,75 dBTP. Memakai cache produksi yang sudah ada; tidak membuat narasi baru dan tidak memanggil API berbayar. Setelah pipefail diterapkan, uji audio-cache ulang pada HEAD `4a6d061` (run `45288876269`) juga sukses: 29 kata, selisih stream 0,01 detik, -16,89 LUFS, -1,75 dBTP; cache yang ada dipakai tanpa panggilan API berbayar.

**Catatan PERIKSA yang tetap terbuka:** hook kronologis dan kesinambungan `surat_amanah` pada contoh B2; derajat hadis Tirmidzi 3153 diperselisihkan; beberapa shot dialog/reaksi memakai komposisi close-up mirip. Jangan ubah tingkat temuan tanpa alasan/bukti. D2 tetap belum selesai sampai pemilik meninjau gerak kontinu dan komposisi video; D3 tidak termasuk PR ini.

### Arah hasil akhir dan urutan kerja berikutnya (keputusan pemilik, 24 Nov 2026)

Target bukan sekadar membuat beberapa adegan contoh terlihat bagus. Targetnya adalah satu alur otomatis yang dapat
menerjemahkan naskah berbeda menjadi peristiwa, keputusan visual, kesinambungan adegan, lalu MP4 yang layak ditinjau.

**Urutan kerja setelah D2, tanpa membuat sistem paralel:**
1. Audit peta kepemilikan fitur pada kode dan cabang kerja: kemampuan, modul pemilik, antarmuka, pemanggil, dan tes pembukti.
   Cocokkan juga dengan implementasi yang sudah ada di `mesin-video`; ambil konsep yang terbukti, bukan arsitektur kedua.
2. Selesaikan satu jalur event-to-visual deterministik: bukti frasa naskah → peristiwa terstruktur → keputusan visual → shot.
   Perluas parser/perencana peristiwa yang sudah ada; jangan membuat parser atau skema peristiwa kedua.
3. Lengkapi state benda dan lingkungan yang berubah hanya ketika peristiwa menyatakannya. Satu pemilik state harus
   mengendalikan nilai awal, transisi, dan kesinambungan lintas shot; jangan menambah state manager kedua.
4. Hubungkan peristiwa ke komponen SVG yang sudah dimiliki renderer. Jika belum ada komponen yang cocok, catat
   kebutuhan dan buat komponen yang dapat dipakai ulang di registri/pemilik visual yang sama; jangan menaruh SVG
   duplikat di parser, sutradara, dan renderer.
5. Uji dengan Nuh, Hud, dan Mahsyar 1 tanpa koordinat/shot manual. Bandingkan keputusan visual dengan narasi sumber,
   lalu nilai kualitas pencahayaan, kedalaman, komposisi, skala, dan gerak. Ambil teknik visual yang berhasil dari
   contoh Nuh/Ya'juj sebagai prinsip yang dapat dipakai lintas cerita, bukan menyalin resep lengkapnya.
6. Setelah jalur otomatis lintas cerita terbukti, lanjutkan pustaka resep (D3), lalu pemeriksa/kritikus (E), dan
   otomatisasi MP4 end-to-end (F). Model AI tetap opsional dan tidak menjadi syarat jalur utama.

**Peta pemilik fitur yang harus dipertahankan (perlu diverifikasi terhadap HEAD sebelum mengubah kode):**

| Kemampuan | Pemilik yang sudah ada | Aturan perubahan |
|---|---|---|
| Format masukan antrean | `sutradara/antrean.py` | Perluas format ini; jangan membuat format naskah kedua |
| Kontrak genre | `sutradara/genre.py` | Semua mekanisme lintas genre tetap di inti |
| Perencanaan Kisah Islami | `sutradara/paket_genre/kisah_islami/sutradara.py` | Satu pengarah genre; jangan membuat sutradara alternatif |
| Ekstraksi peristiwa | `paket_genre/kisah_islami/peristiwa.py` (PR #48, belum di main) | Perluas pemilik ini; jangan membuat parser kedua |
| Skema dan penjaga rencana | `sutradara/rencana/` + ekstensi paket | Tambah field melalui skema resmi dan tes penjaga |
| Komposisi shot | `sutradara/adegan.py` | Mekanisme komposisi generik tetap di sini |
| Rig tokoh dan gerak | `sutradara/gaya/tokoh.py`, `sutradara/gerak.py` | Jangan gambar ulang rangka/gerak di paket genre |
| Kamera dan waktu | `sutradara/kamera.py`, `sutradara/waktu.py`, `sutradara/garis_waktu.py` | Perluas API yang ada; hindari sistem keyframe/timeline kedua |
| Renderer dan komponen visual | `paket_genre/kisah_islami/renderer.py`, `visual/` | SVG berada pada pemilik renderer/komponen, bukan parser |
| Audio | `sutradara/suara/` | Gunakan satu jalur narasi, sinkronisasi, dan pencampuran |

PR #48 tetap terbuka dan tidak di-merge sampai keputusan pemilik berikutnya. Temuan render satu mata yang terlihat
pada tokoh dicatat sebagai cacat visual yang perlu ditelusuri di pemilik rig/wajah dan diuji pada tampak depan,
tiga-perempat, serta samping; jangan membuat modul mata baru sebelum penyebab di renderer wajah ditemukan.

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

### ○ Fase 6b — Pematangan: belajar dari hasil (Tahap G)
- Data per video (keputusan sutradara + persetujuan pemilik + angka penonton) → eksperimen bandit pada pilihan setara
  → laporan mingguan → usulan perubahan resep yang disetujui pemilik. Tanpa melatih model; LLM opsional.
- Dalil, penjaga, dan batas wajib tidak pernah dioptimasi.
- **Kriteria selesai:** beberapa minggu data menunjukkan resep yang bertahan atau membaik, dan pemilik menyetujui perluasan.

### Referensi gaya dari pemilik (21 Nov 2026)
- **Sibuntel** (TikTok): 2D datar sederhana, dua tokoh, kamera bergantian saat dialog, ekspresi lewat mata/alis, gerak
  minimal -> ekspresi halus (Tahap B2) + liputan dialog (Tahap D). Hampir siap pakai untuk genre komedi kelak.
- **Meja Putih** (TikTok): tokoh kartun 2D di atas latar 3D sederhana (piramida, balok, gurun) dengan kamera bergerak di
  ruang 3D dan latar kabur/tokoh tajam -> rencana latar 3D sebagai PUSTAKA KLIP yang dirender sekali lalu dipakai ulang
  (Three.js low-poly/toon, palet preset sama). Belajar dari film3d mesin-video: render 3D tanpa GPU ±1 dtk/bingkai,
  jadi jangan dirender per video. Dikerjakan setelah Tahap D–F; uji pertama: banjir Nuh.

### Kebutuhan pemakaian publik (dicatat 21 Nov 2026; baru setelah Fase 6/6b)
- Pustaka pemeran per saluran: pemeran dibangkitkan dari kode unik saluran (kombinasi ciri), pemeriksaan kemiripan
  dengan saluran lain, bisa disetel pengguna. Fondasinya = kartu identitas pemeran (Tahap B2).
- Ciri khas saluran: palet, huruf judul, gaya kartu dalil, suara narator per saluran.
- Adab penggambaran tokoh mulia & verifikasi dalil SAMA untuk semua pengguna (batas wajib, bukan pilihan).

### ○ Fase 7 — Perluasan genre (baru dibuka setelah fase 6 terbukti dan disetujui pemilik)
- Genre lain (komedi, edukasi, cerita anak) sebagai paket genre di atas inti yang sama (sambungannya disiapkan di Tahap D langkah 0).
- Catatan: set pose Dajjal, Ya'juj Ma'juj, Buraq, dan ragam tokoh dulu tercatat di sini; sejak 21 Nov 2026 dipindah ke
  Tahap B karena itu kebutuhan Kisah Islami sendiri, bukan perluasan genre.

## Peta tahap kerja (A–F) ke fase
Fase = tahapan produk di dokumen ini. Tahap = paket kerja untuk pengembang AI (`docs/TAHAP_LANJUT.md`).
| Tahap | Isi | Fase |
|---|---|---|
| A | Celah efek suara terikat aksi (selesai) | 2 |
| B | Visual & tokoh: tampak samping, ragam tokoh, Dajjal, Ya'juj, Buraq, Dabbah, render cepat | 1b lanjutan |
| B2 | Adab tokoh mulia (pilar khusus nabi, malaikat beda, sahabat wajah cahaya) + sistem barang | 1b lanjutan |
| C | Penguatan dalil | 3 lanjutan |
| D | Pisah inti/genre + sutradara otomatis | 4 |
| E | Periksa & kritikus | 5 |
| F | Otomatisasi penuh (F1 bot pindah + persetujuan: selesai, tunggu langkah pindah pemilik) | 6 |
| G | Belajar dari hasil (pematangan) | 6b |
| — | Genre lain | 7 (belum dibuka) |

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
- [x] Arah pandang depan/samping/belakang dengan interpolasi smoothstep; proyeksi tubuh dan visibilitas wajah mengikuti arah. Uji render visual masih perlu tinjauan manusia.
- [x] Kamera shot pembuka Nuh diperketat; lambung bahtera dinaikkan dan terlihat pada lembar kontak Tahap B. Komposisi akhir masih menunggu persetujuan pemilik.
- [x] Parameter anak/lansia, variasi busana Mesir kuno/umum, dan variasi kerudung tetap memakai rangka yang sama.
- [x] Dajjal desain B: arah belakang, langkah/bobbing, jubah berkibar, dan pembukaan lengan bertahap tersedia serta diuji. Komposisi gerak utuh masih menunggu tinjauan visual pemilik.
- [x] Ya'juj Ma'juj: contoh rencana penggalian, turun dari tempat tinggi, dan danau surut tersedia; QS Al-Anbiya 96 dan HR. Tirmidzi 2240 diverifikasi workflow (sahih).
- [x] Komponen Buraq putih berkaki empat tanpa sayap/wajah manusia; penjaga menolak penunggang yang ditandai eksplisit. Proporsi dan jarak langkah masih perlu tinjauan visual.
- [x] Dabbah ditampilkan hanya sebagai gumpalan kabut/debu tanpa anatomi dan tanpa tanda wajah; dialog disampaikan melalui narasi/teks. Tidak mengarang bentuk yang tidak dijelaskan dalil.

### Dalil
- [x] Fondasi bacaan latin ayat disiapkan di balik `FITUR_BACAAN_LATIN = False`; tidak dipanggil dan tidak tampil sampai pemilik meminta.
- [ ] Musnad Ahmad tetap ditolak penjaga. Audit kandidat belum menemukan bukti yang sekaligus memastikan lisensi publik, teks Arab, dan penilaian derajat yang dapat ditelusuri untuk riwayat yang diperlukan; jangan mengimpor atau mengarang derajat.
- [ ] Diagnostik akses Quran Foundation diarahkan ke tiga route resmi Hadith References v4: `GET /hadith_references/by_ayah/{ayah_key}`, `GET /hadith_references/by_ayah/{ayah_key}/hadiths`, dan `GET /hadith_references/count_within_range?from={verse_key}&to={verse_key}`. Scope `content.hadith.read` tercantum pada token, tetapi uji sebelumnya memakai route keliru `/hadiths/by_ayah/{ayah_key}` dan menghasilkan 403; uji ulang live menunggu workflow dispatch `verifikasi dalil` pada cabang Tahap C. Pemeriksa kedua hanya dapat membandingkan hadis yang ada dalam peta referensi ayat Quran Foundation; API ini bukan pencarian bebas berdasarkan kitab+nomor. Jika tidak ada referensi/matan yang cocok di peta, hasilnya `tidak_tercakup`/`tidak_terbukti`, bukan lulus; gunakan dataset lokal sebagai sumber pemeriksaan selanjutnya. Jangan menyimpulkan status dari hasil kosong.
- [x] Koreksi Muslim 2934b (`mendatangi surga yang ia lihat berupa api` → `mendatangi sungai yang ia lihat berupa api`, النهر) telah disetujui pemilik pada 22 Nov 2026 (commit `c05926c`); status `disetujui_pemilik`. Jangan membatalkan atau menimpa persetujuan tersebut.
- [x] Pasangan Arab–terjemah memakai data word-by-word Quran Foundation bila semua kata memiliki terjemah resmi; jika tidak tersedia, tidak mengklaim pasangan kata dan memakai pemotongan lama.

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
- 22 Nov 2026 — Tahap C: pemeriksa scope hadis dipisah dari diagnosa ayat; perintah `diagnosa-quran` kini juga meminta `content.hadith.read` dan menguji endpoint hadis tanpa mencetak rahasia. Pemeriksaan live harus dijalankan pemilik melalui workflow `verifikasi dalil` yang sudah ada di `main` dengan memilih cabang Tahap C; belum dijalankan, sehingga pemeriksa hadis kedua tetap terblokir.
- 22 Nov 2026 — Tahap C: koreksi terjemah disimpan sebagai usulan terpisah dari dataset sumber. Muslim 2934b: `surga` → `sungai` (lafaz `النهر`) belum disetujui; renderer hanya memakai koreksi dengan status `disetujui_pemilik`.
- 22 Nov 2026 — Tahap C: pasangan kata ayat diambil dari `words[].translation` Quran Foundation; hanya dipakai bila setiap kata punya pasangan. Bendera transliterasi latin tetap mati dan tidak ada bacaan latin yang ditampilkan.
- 22 Nov 2026 — Tahap C: Musnad Ahmad belum ditambahkan. Untuk Ahmad 22308 ditemukan halaman yang menyebut matan dan derajat Sahih menurut Al-Arna'ut ([HadithWeb](https://hadithweb.com/ahmad%3A22308), [Abu Amina Elias](https://www.abuaminaelias.com/dailyhadithonline/2014/11/30/mark-of-the-beast/)); izin lisensi/penerbitan ulang data halaman itu tidak jelas. Kandidat tambahan: [HadeethEnc 65149](https://hadeethenc.com/ar/browse/hadith/65149) menampilkan derajat Sahih dan rujukan Ahmad 36/646 (22308), tetapi [dataset quranlab/hadith](https://huggingface.co/datasets/quranlab/hadith) memisahkan ahmad-ar (matan tanpa derajat) dari hadeethenc-ar (pilihan hadis berderajat) dengan lisensi per baris; pencocokan baris, lisensi teks Arab, dan asal penilai untuk riwayat ini belum diverifikasi. [Sanadset 650K](https://takhrij.org/en/sources/) menyatakan CC BY 4.0 untuk teks Arab, tetapi pasangan teks/grade/edisi untuk riwayat ini belum terbukti. Karena itu tidak ada rekaman yang diimpor dan penjaga tetap menolak kitab yang belum didukung. Rujukan audit: [Quran Foundation scope](https://api-docs.quran.foundation/docs/user_related_apis_versioned/scopes/), [quranlab/hadith sources](https://huggingface.co/datasets/quranlab/hadith/blob/main/SOURCES.md), [quranlab/hadith licenses](https://huggingface.co/datasets/quranlab/hadith/blob/main/LICENSES.md).
- 21 Nov 2026 — Tanah bertekstur menjadi bawaan preset; jenis dan seed dapat diatur per shot. Tekstur statis di koordinat dunia, berkontras rendah, dan dirender di bawah benda/tokoh. Batu foreground tetap tajam tanpa blur.
- 21 Nov 2026 — Tahap B: dokumentasi audit delapan kriteria diperbarui; bukti teknis dan batas tinjauan visual dicatat di `docs/TAHAP_B_AUDIT.md`. Dabbah dikunci sebagai kabut tanpa wujud dan tanpa penanda wajah.
- 21 Nov 2026 — Tanah bertekstur menjadi bawaan preset; jenis dan seed dapat diatur per shot. Tekstur statis di koordinat dunia, berkontras rendah, dan dirender di bawah benda/tokoh. Batu foreground tetap tajam tanpa blur.
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
- 21 Nov 2026 — mesin-video & motion-studio-ai akan dihapus. Bot Mesin KONTEN dipindah ke repo ini di Tahap F (bot/token/Worker tetap); syarat hapus mesin-video: bot jalan dari repo ini + periksa.py terpindah.
- 21 Nov 2026 — Adab saluran (AGENTS.md): pilar cahaya khusus nabi; malaikat cahaya bentuk lain; semua sahabat tubuh berbaju + wajah cahaya; orang saleh lain tokoh manusia. Alasan: kedudukan nabi tidak disamakan. Dikerjakan di Tahap B2.
- 21 Nov 2026 — Bot jadi pintu masuk naskah: /naskah, /ide, kartu status per tahap, /status. Format naskah ditetapkan (`sutradara/antrean.py`) sebagai masukan Tahap D; naskah disetujui menunggu sutradara otomatis.
- 21 Nov 2026 — F1 dikerjakan Claude: `bot/` (Worker mesin-konten) = persetujuan + balas komentar + chat pribadi; fitur saldo/proyek/Studio ditinggal. Aktif setelah pemilik memindah sumber build Cloudflare (bot/README.md).
- 21 Nov 2026 — Struktur inti vs paket genre (`kisah_islami` dulu) dipisah di awal Tahap D, sebelum resep sutradara dibangun, agar genre lain kelak tidak menyentuh inti. Genre lain tetap belum dibangun.
- 21 Nov 2026 — Fase 1b didahulukan (permintaan pemilik). Tokoh lama (pose diam) diganti rangka bersendi; nama pose lama tetap berlaku.
- 21 Nov 2026 — Tahap A efek terikat aksi: keterlihatan kamera/lapis depan, variasi ketukan, permukaan/fallback, tawa/NPC/kabut/retakan, sumber palu Nuh, ekor efek, batas 40 ketukan, tes render dan workflow manual; rekaman khusus tetap menunggu dispatch pemilik.
- 21 Nov 2026 — Aset suara lama dipakai sebagai fallback sesuai kebutuhan Tahap A; provenance/lisensi aset lama belum terdokumentasi penuh. Rekaman dari workflow tunduk pada ketentuan lisensi akun ElevenLabs pemilik; PR tidak menyatakan asetnya public-domain.

- 22 Nov 2026 — Bukti visual Tahap C disimpan di cabang bukti-tahap-c. Cabang lama bukti dipertahankan agar bukti Tahap B/B2 dan tautannya tidak rusak; Git tidak dapat membuat ref bukti/tahap-c ketika ref bukti masih ada.


## Catatan tambahan Tahap C — 22 Nov 2026

- Dokumentasi Content API v4 mengonfirmasi route referensi `GET /hadith_references/by_ayah/{ayah_key}` ([referensi per ayat](https://api-docs.quran.foundation/docs/content_apis_versioned/4.0.0/hadith-references-by-ayah/)), payload `GET /hadith_references/by_ayah/{ayah_key}/hadiths` ([hadis per ayat](https://api-docs.quran.foundation/docs/content_apis_versioned/4.0.0/hadiths-by-ayah/)), dan hitungan `GET /hadith_references/count_within_range?from=...&to=...` ([hitungan rentang](https://api-docs.quran.foundation/docs/content_apis_versioned/4.0.0/hadith-count-within-range/)). Route lama `/hadiths/by_ayah/{ayah_key}` tidak sesuai; 403 sebelumnya tidak membuktikan scope tidak diberikan. Diagnostik sekarang memeriksa ketiga route dan bentuk responsnya.
- Hadith References memetakan hubungan hadis↔ayat, bukan endpoint pencarian kitab+nomor. Pemeriksa kedua hanya berlaku bila peta mengembalikan referensi yang cocok; tidak ditemukan bukan lulus dan dataset lokal tetap menjadi jalur untuk hadis di luar peta. Uji live harus diulang melalui workflow dispatch `verifikasi dalil`.
- Persetujuan pemilik Muslim 2934b tercatat pada commit `c05926c`: frasa lengkap `mendatangi surga yang ia lihat berupa api` dikoreksi menjadi `mendatangi sungai yang ia lihat berupa api`; status `disetujui_pemilik`. Perubahan berikutnya tidak mengubah berkas koreksi yang disetujui.

- 22 Nov 2026 — Tahap D0: pemeriksaan kontinuitas identitas stabil (kartu pemeran vs atribut per shot, termasuk pemeran individu dalam kerumunan) dipindahkan ke `sutradara/rencana/pemeriksaan_umum.py`. Pemeriksaan mode tampil tetap berada di paket Kisah Islami; tidak mengubah kategori adab atau aturan visual genre.

- 22 Nov 2026 — Tahap D0 pemisahan renderer: komponen visual dan data dalil khusus Kisah Islami dipindahkan ke `sutradara/paket_genre/kisah_islami/`; jalur impor lama dipertahankan sebagai shim. Renderer inti menerima hasil lapisan netral melalui kontrak paket. Skema dalil menjadi ekstensi paket, bukan properti inti.

- 22 Nov 2026 — Tahap D1 (bertumpuk di PR #44): format antrean diperluas dengan `peran` per beat dan validator menjelaskan kesalahan struktur dalam bahasa Indonesia. Templat ChatGPT/Gemini ditempatkan di paket Kisah Islami; rujukan dalil tetap berupa ID untuk diverifikasi mesin, bukan teks Arab/terjemahan buatan AI.

- 22 Nov 2026 — Tahap D1, poin 0b: aturan sisipan waktu baca dan efek kemunculan dipindahkan ke hook `PaketGenre`. Garis waktu dan pencampur suara hanya memanggil kontrak generik; paket Kisah Islami mendaftarkan perilaku kartu dan kilau. Waktu konfigurasi genre yang bersifat absolut tetap dipertahankan saat skala shot berubah. Tes membuktikan hook paket tiruan bekerja dan inti tidak menyebut `kartu_dalil`/`kilau_cahaya`.

- 22 Nov 2026 — Tahap D2 (implementasi parsial, bukti dasar lulus): blocking dari visual inti, shot–reverse shot, interaksi eksplisit, gestur menunjuk/ulurkan, tujuan perjalanan benda/tokoh/tepi, dan lintasan kedalaman x/y sudah memiliki tes. CI run 45036513464: 288 tes lulus; render contoh 34,5 detik/414 bingkai; lembar kontak diperiksa. D2 tetap belum dicentang karena pemeriksaan overlap/formasi umum, reaksi pendengar, tiga-perempat, konsistensi 180 derajat lintas-beat, pengejar, putar balik, dan pembalikan badan belum lengkap.

- 23 Nov 2026 — Tahap D2: render bukti diperluas dengan sisipan reaksi pendengar dan pengejaran ke kiri; CI #501 lulus (tes, render, dan pemeriksaan contoh), artefak lembar kontak/MP4 tersedia. Audit visual mengonfirmasi tiga bagian dialog (seruan, reaksi, jawaban), tujuan perjalanan, putar balik, dan dua arah pengejaran. Tes tambahan kini mengunci perubahan arah ke tujuan yang sama (kaidah 180 derajat) dan perhitungan cadence dari kecepatan lintasan; hasil CI commit terbaru masih menunggu. D2 belum dinyatakan selesai sampai hasil tes terbaru dan audit sinkronisasi subtitle/narasi diperiksa.


## Koreksi uji audio nyata D2 — ekor alignment (23 Nov 2026)
- Log workflow #45184440991 menunjukkan render video, mux FFmpeg, dan unggah artefak berhasil; kegagalan terjadi pada pemeriksaan akhir karena a1 potongan terakhir mencakup ekor 0,35 detik setelah kata terakhir (13,95 dtk), sementara MP3 berdurasi 13,52 dtk.
- Perbaikan membedakan akhir kata dari akhir potongan: akhir kata alignment wajib berada dalam toleransi 0,15 detik dari durasi MP3; ekor jeda di luar MP3 ditambahkan sebagai hening oleh FFmpeg (apad) sebelum potongan diambil. Pemeriksaan durasi stream audio-video, LUFS, dan true peak tetap dipertahankan.
- Ditambahkan tes regresi untuk ekor hening, kata yang benar-benar melewati sumber, dan kasus tanpa padding. Tes menggunakan data tiruan; tidak memanggil API ElevenLabs.
- Status: kode dan tes telah dikomit; hasil CI serta workflow dispatch uji_d2 masih harus diverifikasi. Belum ada panggilan API ElevenLabs baru.


- 23 Nov 2026 — Audit ulang PR #48: status D2 dipisah antara implementasi, tes otomatis, render, dan tinjauan pemilik. 320 tes Python + 10 tes bot dan render 14 shot pada SHA 660ea9a tercatat; uji audio-cache pada HEAD masih wajib. Catatan PERIKSA B2/Tirmidzi 3153 dan kebutuhan tinjauan gerak kontinu dipertahankan.


**Catatan penutupan D2 — 24 Nov 2026:** audit visual dan suara telah dinyatakan lulus oleh pemilik. Perbaikan lapisan wajah/penutup kepala dari PR #50 dipindahkan ke cabang PR #48; regresi SVG dan model rambut ditambahkan. Pemetaan visual `tenggelam` tidak lagi memakai komponen keringat. Ekstraksi aktor kini hanya mengisi aktor yang disebut eksplisit; kontrak peristiwa memisahkan `tujuan` perpindahan dari `sasaran` aksi. Perubahan ini menambah field wajib `tujuan` pada skema peristiwa. **Belum dinyatakan selesai/siap merge:** CI pada HEAD final terbaru belum tersedia karena pembaruan melalui API tidak memicu workflow PR pada integrasi ini; uji lengkap dan render harus dijalankan pada HEAD akhir. Cabang masih 6 commit di belakang `main`; enam commit di main hanya menambah empat berkas antrean, yang harus tetap dipertahankan saat integrasi.

## Bukti verifikasi D2 pada HEAD 0322740 — 24 Nov 2026

- Commit terverifikasi: `032274075becc09d21084c2cc02e15e4db6d3f17`.
- GitHub Actions CI #628: **Success**; `python -m pytest -q` menghasilkan **338 passed in 10.74s**; tes bot Telegram lulus.
- Render D2 berhasil: **14 shot, 644 bingkai, durasi 53,7 detik, waktu render 98 detik pada 1 worker**. Artefak: [run CI #628](https://github.com/anwar-alzazali/sutradara-ai-studio/actions/runs/45388739587) · [bukti visual](https://github.com/anwar-alzazali/sutradara-ai-studio/actions/runs/45388739587/artifacts/14916434304).
- Pemeriksaan final enam contoh menghasilkan **0 GAGAL**. Catatan non-blocking yang perlu keputusan editorial: `b2_adab_barang.json` (hook kronologis dan kesinambungan `surat_amanah`), serta `yajuj_majjuj.json` (derajat HR. Tirmidzi 3153 diperselisihkan). Empat contoh lainnya lulus tanpa catatan.
- Audit visual dan suara telah dinyatakan lulus oleh pemilik; CI ini menambah bukti tes otomatis dan render pada HEAD terbaru. CI #628 tidak menjalankan ulang workflow audio-cache.
- PR #48 tetap terbuka dan tidak di-merge. Cabang masih 145 commit di depan dan 6 commit di belakang `main`; enam commit di `main` hanya menambahkan empat berkas antrean. Integrasi harus mempertahankan seluruh berkas tersebut dan menunggu keputusan pemilik sebelum merge.

**Status:** verifikasi otomatis dan render D2 pada HEAD ini lulus. Penutupan integrasi masih menunggu rekonsiliasi enam commit `main` serta keputusan editorial atas catatan `PERIKSA`. Tidak ada perubahan pada batas adab tokoh suci atau aturan dalil.
