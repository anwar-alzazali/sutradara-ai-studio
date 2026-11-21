# Tahap lanjutan untuk pengembang AI lain (ChatGPT/Codex, dll.)

Pemilik memberikan satu tahap per sesi kepada pengembang AI. Hasil tiap tahap diaudit oleh Claude sebelum di-merge.
Idealnya tahap berikutnya dimulai setelah tahap sebelumnya lulus audit dan di-merge. Bila audit Claude belum
tersedia, pakai **mode bertumpuk** dan prompt siap tempel di `docs/PROMPT_CHATGPT.md`.
Kalimat untuk ditempel ke pengembang: **"Kerjakan Tahap X di docs/TAHAP_LANJUT.md di repo anwar-alzazali/sutradara-ai-studio."**

## Aturan umum (berlaku untuk SEMUA tahap)

**Cara bekerja**
- Kerjakan dengan kemampuan maksimal, seperti insinyur senior yang memiliki produk ini.
- Baca kodenya dulu, pahami alasan desain yang ada, lalu pilih solusi terbaik menurut penilaianmu sendiri. Cara
  teknisnya bebas; yang dinilai adalah mutu hasil, bukti, dan kejujuran laporan.
- Jika menurutmu tujuan sebuah poin keliru atau ada cara yang jelas lebih baik, kerjakan versi terbaikmu dan jelaskan
  alasannya di PR. Jangan diam-diam melewatkan poin.

**Bacaan wajib sebelum mulai:** `AGENTS.md`, `docs/ROADMAP.md`, `docs/PANDUAN_GAYA.md`, `docs/RESEP_SUTRADARA.md`.

**Cabang dan PR**
- Buat cabang baru dari `main` dengan nama `tahap-<huruf>-<ringkas>`.
- Buka PR ke `main`, **jangan di-merge sendiri**.
- Satu tahap = satu PR. PR boleh besar, asalkan setiap commit rapi.
- **Tuntaskan SEMUA poin tahap dalam satu sesi kerja.** Jangan berhenti di tengah dan jangan menyerahkan PR draft
  atau "belum lengkap": audit hanya dilakukan sekali, untuk PR yang sudah selesai.
  - Kalau sebuah poin benar-benar mustahil dikerjakan (misalnya butuh rahasia, kredit, atau keputusan pemilik),
    kerjakan semua bagian lain yang bisa dikerjakan, lalu tulis poin itu sebagai "terblokir" beserta alasan dan
    langkah yang dibutuhkan.
  - Kehabisan waktu atau tenaga bukan alasan sah untuk "belum".
- Sebelum menyerahkan, lakukan swa-audit:
  - baca ulang setiap poin tahap dan aturan umum ini;
  - periksa diff-mu sendiri seperti peninjau yang galak;
  - jalankan semua tes;
  - render dan lihat hasilnya;
  - perbaiki yang kurang.
- Status PR: siap ditinjau, bukan draft.

**Batas wajib (tidak bisa ditawar)**
- Isi `AGENTS.md` berlaku penuh, terutama:
  - dalil hanya sahih/hasan dan terverifikasi;
  - nabi, malaikat, dan sahabat digambar sebagai pilar cahaya (nur);
  - Allah tidak digambar;
  - bacaan Arab tidak disuarakan AI;
  - tidak mengarang klaim.
- Jangan melemahkan penjaga (`sutradara/rencana/penjaga.py`), jangan menghapus atau melonggarkan tes, dan jangan
  mengubah teks narasi, dalil, atau status verifikasi di `contoh/*.json` tanpa instruksi pemilik.
- Rahasia hanya ada di GitHub Secrets (`ELEVENLABS_API_KEY`, `ANTHROPIC_API_KEY`, `QURAN_FOUNDATION_CLIENT_ID`,
  `QURAN_FOUNDATION_CLIENT_SECRET`, dan nanti yang disebut di tahap terkait).
  - Jangan meminta, mencetak, atau menulis nilainya ke berkas atau log.
  - Workflow yang memakai rahasia HANYA boleh `workflow_dispatch` atau `schedule`, tidak pernah `push`, `pull_request`, atau `issues`.
- Jangan memanggil API berbayar dari kode yang berjalan di tes atau CI biasa. Yang berbayar dijalankan lewat workflow dispatch oleh pemilik.
- Kode yang disalin dari repo lama (`mesin-video`, `motion-studio-ai`) wajib diberi baris `Asal:` di docstring.
  Bawa yang terbukti berguna saja, bukan seluruh arsitektur lama.
- Repo ini public: lisensi aset dan data harus jelas, dan dicatat di repo.

**Standar selesai (setiap tahap)**
- `python -m pytest -q` lulus, ditambah tes baru untuk semua perilaku baru yang bisa diuji otomatis.
- Bila tahap menyentuh visual atau suara:
  - render contoh yang relevan (narasi tiruan seperti `tests/test_suara.py` boleh dipakai);
  - lampirkan lembar kontak atau tangkapan bingkai di PR;
  - ukur kenyaringan, target ±-15 LUFS dengan puncak ≤ -1 dBTP.
- Perbarui `docs/ROADMAP.md`: centang daftar kebutuhan yang selesai dan tambahkan log keputusan. Perbarui juga
  `PANDUAN_GAYA.md` dan `RESEP_SUTRADARA.md` bila aturan gaya atau resep berubah. Tulis singkat.
- Isi deskripsi PR untuk setiap poin tahap:
  - apa yang dikerjakan dan alasan memilih cara itu;
  - cara memeriksanya;
  - apa yang belum atau tidak bisa diperiksa tanpa mata atau telinga manusia;
  - risiko yang tersisa.
- Jujur: poin yang terblokir ditulis "terblokir", jangan "selesai". Klaim tanpa bukti tes atau render akan ditolak saat audit.
- **Ringkasan audit di awal deskripsi PR**, supaya audit cepat dan hemat:
  - tabel satu baris per poin: nomor | status (selesai/terblokir) | berkas utama | nama tes yang membuktikan |
    bukti render/angka;
  - perintah persis untuk mengulang buktinya (tes, render contoh, ukur kenyaringan);
  - hasil `python -m pytest -q` (jumlah lulus);
  - daftar keputusan desain yang menyimpang dari teks tahap, beserta alasannya.

---

## Tahap A — Celah aturan "efek terikat aksi" (Fase 2)
Tutup celah aturan efek suara di `sutradara/suara/campur.py` (lihat `PANDUAN_GAYA.md` bagian 3b).
1. Tokoh yang tidak terlihat jangan terdengar seolah terlihat. Ini mencakup tokoh yang keluar bingkai karena kamera
   dan tokoh yang tertutup benda di depan.
2. Bunyi berulang jangan terdengar seperti mesin, termasuk saat beberapa tokoh beraksi bersamaan.
3. Kiri-kanan dan keras-pelan mengikuti posisi dan ukuran tokoh sepanjang shot, termasuk bila nilainya keyframe.
4. Bunyi menyesuaikan permukaan atau bahan: tanah/pasir, kayu, air, batu/besi.
5. Aksi lain yang terlihat bisa berbunyi bila masuk akal: tertawa/mengejek, kerumunan jauh, kabut_tanpa_wujud yang
   keluar, retakan, dan perubahan besar benda. Tidak semua gerak perlu berbunyi; bila memilih diam, jelaskan alasannya.
6. Bunyi palu pembangunan bahtera di `contoh/nuh_mengejek.json` punya sumber yang terlihat, misalnya pengikut tanpa
   nama dan tanpa dialog yang sedang memalu. Nabi Nuh tetap nur.
7. Efek satu-kali yang terpotong di akhir shot jangan terdengar putus terlalu pendek.
8. Batas jumlah ketukan per shot harus adil; utamakan tokoh yang paling dekat atau paling terlihat.

Rekaman baru:
- Buat `.github/workflows/efek.yml` (hanya `workflow_dispatch`) yang membaca daftar prompt efek dari berkas di repo,
  memanggil ElevenLabs sound-generation, melewati berkas yang sudah ada, lalu meng-commit hasilnya.
- Sertakan daftar prompt yang dibutuhkan.
- Sebelum rekaman ada, gunakan cadangan dari `aset/suara`.

## Tahap B — Visual dan tokoh (lanjutan Fase 1b)
Tujuan: tokoh dan adegan cukup kaya untuk kisah-kisah akhir zaman tanpa melanggar PANDUAN_GAYA.
1. **Tampak samping dan berbalik badan.** Tokoh bisa berjalan menyamping, menoleh penuh, dan membelakangi kamera.
   Peralihan antar-arah harus halus. Gerak, alat, ekspresi, dan mulut bicara yang sudah ada tetap bekerja di semua arah.
2. **Ragam tokoh:**
   - anak dan lansia;
   - variasi perempuan berkerudung;
   - pakaian per zaman/wilayah (Arab kuno, Mesir kuno, dan lain-lain) sebagai pilihan yang bisa ditambah tanpa
     mengubah kode rangka.
3. **Set pose Dajjal desain B:** berjalan, tampak dari belakang, jauh di tengah pengikut, jubah berkibar, lengan
   membuka perlahan. Ciri hadis tetap tampil dan tidak ditambah ciri karangan.
4. **Adegan Ya'juj Ma'juj** (contoh rencana baru, dalil terverifikasi):
   - manusia biasa berpakaian, tanpa ciri ras atau bentuk aneh;
   - kengerian datang dari jumlah dan gerak: menggali dinding sampai tipis, turun dari setiap tempat tinggi
     (QS Al-Anbiya 96), danau yang diminum habis;
   - benda baru yang dibutuhkan (dinding, lubang yang membesar, danau yang surut) dibuat sebagai komponen yang bisa dipakai ulang.
5. **Buraq:**
   - hewan putih, ukurannya antara keledai dan bagal, langkahnya sejauh pandangan;
   - tanpa sayap dan tanpa wajah manusia;
   - tidak pernah digambar dengan penunggang; penunggang adalah pilar cahaya.
   - Tambahkan aturan penjaga yang mencegah pelanggaran ini.
6. **Dabbatul Ard lanjutan:** "berbicara kepada manusia" lewat teks dan narator, dan tanda di wajah orang di pasar
   (abstrak, berlabel ilustrasi). Bila dalilnya ada di Musnad Ahmad, ikuti poin dalil di Tahap C. Jangan menampilkan dalil yang belum terverifikasi.
7. **Shot pembuka Nuh:** kamera lebih dekat ke kapal, karena visual inti masih kecil di layar.
8. **Percepat render:** paralel per shot, baik di mesin lokal maupun di Actions, tanpa mengubah hasil gambar
   (bandingkan bingkai sebelum dan sesudah). Laporkan angka kecepatan sebelum dan sesudah.

## Tahap C — Penguatan dalil
1. Pemeriksa hadis kedua memakai scope `content.hadith.read` Quran Foundation. Kalau dua sumber berbeda,
   tandai untuk ditinjau pemilik; jangan memilih sendiri.
2. **Musnad Ahmad.** Cari sumber dengan lisensi jelas yang punya teks Arab dan penilaian derajat yang bisa
   ditelusuri. Kalau tidak ada sumber yang layak, laporkan dan biarkan penjaga tetap menolak.
3. **Terjemah hadis dataset yang keliru** (contoh: Muslim 2934b, "surga" padahal النهر berarti sungai):
   - buat mekanisme koreksi terjemah yang ditinjau pemilik;
   - simpan teks asli dan koreksi berdampingan beserta alasannya;
   - di layar, tampilkan terjemah yang sudah disetujui saja.
4. **Pasangan Arab–terjemah di kartu ayat:** gunakan pemetaan kata (word-by-word) Quran Foundation bila tersedia,
   supaya potongan Arab dan terjemah benar-benar sepadan.
5. **Bacaan latin di kartu:** JANGAN dikerjakan sebelum pemilik memintanya. Cukup siapkan kodenya di balik bendera yang mati.

## Tahap D — Sutradara otomatis v1 (Fase 4) — inti produk
**Langkah 0 — pisahkan inti dan genre, kerjakan SEBELUM poin lainnya** (keputusan pemilik 21 Nov 2026).
Kelak akan ada genre lain (komedi, edukasi, cerita anak). Genre itu belum dibangun sekarang, tetapi sambungannya harus
sudah ada supaya kesulitannya tidak bertambah seiring kode membesar.
- **Inti** (netral genre): render, kamera, keyframe, latar, tokoh bersendi + gerak + ekspresi, garis waktu, suara,
  pemeriksaan umum (skema, penataan panggung, mutu teknis). Inti tidak boleh menyebut nama elemen genre mana pun.
- **Paket genre**, mulai dari `kisah_islami`, berisi semua yang khas genre itu:
  - elemen adegan (nur, Dajjal, kabut tanpa wujud, kartu dalil, dan lain-lain);
  - aturan penjaga;
  - tambahan skema rencana (misalnya `dalil`);
  - modul dalil;
  - panduan gaya, resep sutradara, dan bawaan seperti jenis kepala tokoh.
- Rencana menyebut genrenya, misalnya `"genre": "kisah_islami"`. Rencana lama tanpa kolom ini otomatis dianggap
  `kisah_islami`. Paket genre mendaftarkan elemennya ke inti; inti tidak mengimpor genre secara langsung.
- **Syarat lulus langkah 0:**
  - semua tes lama tetap lulus;
  - bingkai hasil render semua `contoh/*.json` identik sebelum dan sesudah pemisahan (bandingkan beberapa bingkai per shot);
  - penjaga Kisah Islami tetap menolak semua pelanggaran yang dulu ditolak;
  - ada tes dengan paket genre tiruan yang sangat kecil (hanya di folder tes), yang membuktikan genre baru bisa
    ditambahkan tanpa menyentuh berkas inti sama sekali.
- Jangan membangun genre komedi atau genre nyata lain di tahap ini.
- Poin 1–7 di bawah dibangun di atas pemisahan ini: resep, templat naskah, dan keputusan sutradara yang khas Kisah
  Islami masuk ke paket genrenya, sedangkan mekanismenya berada di inti.

Tujuan: dari naskah terstruktur menjadi rencana lengkap yang lulus penjaga, dengan mutu setara video yang
disutradarai manual (contoh Nuh dan Ya'juj di `RESEP_SUTRADARA.md`). Baca ROADMAP Fase 4.
1. **Templat naskah untuk AI gratis.** FORMAT NASKAH SUDAH DITETAPKAN di `sutradara/antrean.py` (dipakai bot: antrean
   `antrean/<id>/naskah.json` yang disetujui pemilik = masukan sutradara). Jangan membuat format kedua; perluas bila perlu.
   - Format per beat: narasi, kata kunci, dalil (rujukan saja; teks diambil oleh verifikasi), suasana, dan peran.
   - Templatnya juga harus mendorong mutu cerita: fakta terkuat di depan, cerita utuh dalam satu video, setiap
     kalimat menambah informasi atau ketegangan.
   - Sertakan validator yang menjelaskan kesalahan dalam bahasa Indonesia yang bisa dipahami orang awam.
2. **Keputusan tingkat video:**
   - visual inti dan jalur perubahannya;
   - busur emosi diterjemahkan ke preset suasana;
   - peran diterjemahkan ke cara tampil (sesuai tabel PANDUAN_GAYA);
   - hook diambil dari beat paling dramatis.
3. **Penataan panggung otomatis:** sutradara yang menentukan koordinat. Pelaku aksi ditempatkan di samping visual
   inti, pihak lawan di seberang atau melintas, posisi konsisten antar-shot, dan tidak saling menutupi. Penjaga
   `PELAKU_JAUH`/`BUKAN_PELAKU_DEKAT` harus lulus tanpa koordinat yang ditulis tangan.
4. **Keputusan tingkat shot:**
   - pecah enumerasi menjadi shot per kata dan eskalasi pada pengulangan;
   - kamera mengikuti posisi beat;
   - teks layar 1–3 kata yang menamai makna;
   - `potong_di` dipilih otomatis;
   - gerak dan ekspresi tokoh diturunkan dari kata kerja dan emosi narasi;
   - efek suara mengikuti aksi (Tahap A).
5. **Perpustakaan resep adegan:** potongan siap pakai yang diambil dari video yang disetujui pemilik, misalnya
   "kaum mengejek", "azab datang", "doa sunyi". Sutradara memilih dan merangkainya. Format resep harus bisa
   ditambah orang lain tanpa menyentuh kode inti.
6. **Model AI (opsional, di balik bendera, mati secara bawaan):**
   - model murah dipakai hanya ketika aturan ragu;
   - biaya dicatat per video;
   - mesin harus tetap menghasilkan rencana yang layak tanpa model.
7. **Bukti:**
   - naskah kisah Nabi Nuh dijadikan rencana dan video otomatis penuh;
   - satu kisah baru (misalnya Nabi Hud) juga dibuat tanpa menyunting kode atau rencana dengan tangan;
   - lampirkan lembar kontak keduanya dan perbandingan dengan versi manual.
   Kelayakan tayang diputuskan pemilik, bukan pengembang.

## Tahap E — Periksa dan kritikus (Fase 5)
1. **Periksa teknis.** Port `mesin-video/periksa.py` dengan baris `Asal:`. Yang diperiksa: resolusi, durasi, audio
   hilang, clipping, layar kosong, teks terpotong atau bertumpuk, dan teks di zona antarmuka TikTok.
   - GAGAL hanya untuk kerusakan teknis atau pelanggaran batas wajib.
   - Masalah estetika ditandai PERIKSA (lihat prinsip di `AGENTS.md`).
2. **Kritik terhadap resep dari lembar kontak dan rencana:**
   - visual inti tidak berubah;
   - shot terlalu mirip berturut-turut;
   - tokoh keluar layar;
   - pelaku jauh dari visual inti;
   - subtitle menutupi kartu;
   - bunyi tanpa sumber yang terlihat.
3. **Perbaikan otomatis:** temuan yang bisa diperbaiki diperbaiki oleh sutradara (Tahap D), lalu dirender ulang,
   paling banyak 2 putaran. Kritikus visual berbasis model AI hanya opsional, di balik bendera, dan biayanya dicatat.
4. **Bukti:** sisipkan cacat secara sengaja pada video uji (teks bertumpuk, shot kosong, tokoh di luar layar, clipping).
   Semua cacat itu harus tertangkap, dan yang bisa diperbaiki harus benar-benar terperbaiki.

## Tahap F — Otomatisasi penuh (Fase 6)
1. **Workflow `buat_video.yml`** (`workflow_dispatch`, masukan naskah) menjalankan berurutan: verifikasi dalil,
   narasi, sutradara, render, campur suara, periksa/kritikus, lalu kirim ke Telegram untuk disetujui.
   - Nama rahasia Telegram diusulkan di PR. Pemilik yang mengisinya; jangan meminta nilainya.
1b. **Persetujuan lewat Telegram: SUDAH dikerjakan Claude (F1, 21 Nov 2026).** Bot Mesin KONTEN dipindah ke `bot/`
   (lihat `bot/README.md`): persetujuan Setujui/Tolak + alasan → `data/persetujuan/<id>.json`, balas komentar, chat
   pribadi. Di tahap ini cukup: kirim video ke Telegram dengan tombol `st:<id>`/`tl:<id>` (seperti workflow
   `tes telegram`), dan baca `data/persetujuan/` sebagai masukan antrean & Tahap G. Workflow pengirim memakai Secret
   `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` repo ini (sudah terisi dan teruji).
   - **Syarat sebelum mesin-video boleh dihapus:** bot sudah berjalan dari repo ini dan teruji, dan `periksa.py` sudah
     dipindah di Tahap E.
2. **Antrean naskah dan tugas terjadwal** (satu video per hari):
   - hanya mengirim untuk disetujui;
   - tidak pernah mengunggah ke TikTok atau Facebook sendiri;
   - persetujuan atau penolakan pemilik tercatat dan menjadi bahan perpustakaan resep.
3. **Laporan biaya per video:** kredit ElevenLabs, model AI, dan menit Actions. Sertakan peringatan bila melewati
   batas yang bisa diatur.
4. **Ketahanan:** gagal di satu langkah tidak membayar ulang langkah berbayar yang sudah selesai (cache). Pesan galat
   ke pemilik harus bisa dipahami orang awam.
5. **Bukti:** jalankan uji kering (tanpa kirim dan tanpa kredit) untuk satu naskah dari awal sampai akhir, lalu
   tunjukkan log dan berkas hasilnya. Kriteria akhir fase ini, yaitu 5 hari berturut-turut dengan ≥3 video disetujui
   pemilik, dinilai setelah merge, bukan di PR.

## Tahap G — Belajar dari hasil (Fase 6b; baru setelah Tahap F berjalan dan video rutin tayang)
Tujuan: mesin makin baik dari keputusan pemilik dan respons penonton, tanpa melatih model sendiri (datanya terlalu
sedikit), dan tanpa pernah melonggarkan batas wajib.
1. **Catatan per video:** keputusan sutradara (resep, jenis hook, durasi, preset, efek), keputusan pemilik dan
   alasannya (dari Tahap F), serta angka penonton bila ada. Untuk angka penonton, cek dulu apa yang benar-benar bisa
   diambil lewat API TikTok/Facebook dan laporkan. Bila tidak bisa, sediakan cara isi manual yang mudah lewat bot
   (misalnya mengirim tangkapan layar statistik).
2. **Eksperimen otomatis** (multi-armed bandit) hanya pada pilihan yang setara dan aman (gaya hook, ritme, pilihan
   resep), dengan eksplorasi yang tetap ada dan bisa dimatikan.
3. **Laporan mingguan** berupa angka dan grafik dari kode biasa, tanpa LLM.
4. **Usulan perbaikan:** bawaannya laporan ditempel pemilik ke AI gratis. Opsi LLM otomatis (di balik bendera,
   biaya dicatat) membuat PR usulan perubahan resep. Mesin tidak pernah mengubah dirinya sendiri tanpa persetujuan.
5. **Pagar:** dalil, penjaga, dan batas wajib tidak pernah menjadi bahan eksperimen atau optimasi. Ada tes yang
   membuktikan sinyal penonton tidak bisa mendorong pelanggaran (misalnya topik berat dibuat sensasional).

## Sesudah Tahap G
Fase 7 (perluasan genre) **tidak dibuka** sebelum Fase 6 terbukti berjalan, pematangan (Tahap G) menunjukkan hasil dan pemilik menyetujuinya secara tertulis. Ini sesuai keputusan pemilik bahwa Kisah Islami harus
konsisten dulu. Jangan memulai Fase 7 atas inisiatif sendiri.
