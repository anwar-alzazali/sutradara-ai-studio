# Tahap lanjutan untuk pengembang AI lain (ChatGPT/Codex, dll.)

Pemilik memberikan satu tahap per sesi kepada pengembang AI. Hasil tiap tahap diaudit oleh Claude sebelum di-merge.
Idealnya tahap berikutnya dimulai setelah tahap sebelumnya lulus audit dan di-merge. Bila audit Claude belum
tersedia, pakai **mode bertumpuk** dan prompt siap tempel di `docs/PROMPT_CHATGPT.md`.
Dokumen aturan selalu dibaca dari cabang `main` (cabang kerja bisa tertinggal). Kalimat untuk ditempel ke pengembang: **"Kerjakan Tahap X di docs/TAHAP_LANJUT.md di repo anwar-alzazali/sutradara-ai-studio."**

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

## Tahap B2 — Adab penggambaran tokoh mulia + sistem barang (setelah Tahap B di-merge, sebelum D)
Aturan wajibnya ada di `AGENTS.md` (tabel adab saluran). Kerjakan:
1. **Bentuk cahaya malaikat** yang jelas berbeda dari pilar nabi (mis. berkas sinar dari atas / cahaya tanpa wujud).
2. **Mode tokoh "wajah cahaya" untuk sahabat:** tubuh berbaju, gerak, gestur, dan barang tetap berfungsi; wajah
   diganti cahaya lembut (tanpa mata/mulut/ekspresi wajah). Tetap santun di semua arah hadap (depan/samping/belakang).
3. **Penjaga:** peran nabi -> wajib pilar; malaikat -> wajib bentuk malaikat; sahabat -> wajib wajah cahaya; pilar
   dilarang untuk selain nabi; wajah sahabat tidak boleh punya ekspresi/rincian. Tes untuk setiap pelanggaran.
4. **Sistem barang** (memegang, mengulurkan, menerima, pindah pemilik, tetap terbawa antar shot, tangan/lengan
   mengikuti barang): kembangkan dari `alat` dan IK tangan yang sudah ada, jangan membuat sistem kedua. Barang milik
   nabi ditampilkan di sisi pilar dengan cahaya (tanpa tangan); serah-terima dengan nabi = barang bergerak ke/dari pilar.
5. **Kartu identitas pemeran + pemeriksa kesinambungan.** Tokoh individual punya identitas tetap (ciri wajah,
   kulit, rambut/janggut, penutup kepala, palet baju, aksesori, suara) yang dirujuk rencana lewat id, dan tampil sama
   di semua shot/episode. Pemeriksa membandingkan ciri stabil antar shot: beda ciri = PERIKSA (bukan GAGAL, karena
   ganti kostum bisa disengaja); perubahan cara tampil (mis. siluet -> terungkap) dicatat sebagai perubahan gaya yang
   disengaja. Ide ini SUDAH dibangun di mesin-video cabang `feat/short-term-production-intelligence`
   (`docs/INTELLIGENCE_GOAL_JANGKA_PENDEK.md` bagian "Pemeriksaan kontinuitas identitas tokoh", `docs/AI_STORY_DIRECTOR.md`
   bagian identitas & serah-terima benda, `docs/PRODUCTION_JSON_V1.md` bagian `characters`, beserta kode/tesnya):
   pelajari, bawa konsep dan bagian kode yang terbukti dengan baris `Asal:`, sesuaikan ke rig & rencana repo ini.
   Jangan membawa arsitektur registri/SQLite/kontrak produksi utuhnya.
   Desain identitas sebagai data sehingga kelak bisa diperluas menjadi pustaka pemeran per saluran (pemakaian publik).
6. **Ekspresi wajah yang lebih halus** (referensi pemilik: akun TikTok Sibuntel — emosi hampir seluruhnya lewat mata,
   tubuh nyaris diam). Tambah kendali wajah: kelopak mata (setengah turun–terangkat), arah lirikan, alis (naik/turun,
   miring ujung dalam/luar, merapat), kerutan pangkal hidung, mulut kecil bulat. Ekspresi baru minimal:
   **kepergok/panik** (alis cemas: ujung dalam naik; mata melotot tegang; kerut hidung; mulut "eh…"), **jijik/ilfil**
   (alis turun merapat; kerut hidung), **sinis**, **curiga**, **heran**. Pelajaran: garis wajah yang sama terbaca
   berbeda tergantung bentuk alis — alis harus bisa diatur halus. Untuk Kisah Islami dipakai lebih tertahan (meremehkan,
   bukan lucu). Wajah cahaya (sahabat) dan pilar (nabi) TIDAK memakai ekspresi wajah.
7. Perbarui tabel "siapa digambar bagaimana" di `docs/PANDUAN_GAYA.md` sesuai `AGENTS.md`, dan contoh yang terdampak.
8. Bukti: lembar ekspresi (semua ekspresi lama+baru berdampingan), render tiap golongan berdampingan + adegan serah-terima (manusia–manusia dan manusia–nabi) + satu tokoh
   yang sama di beberapa shot.

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
**Dikerjakan dalam 4 PR berurutan** (keputusan pemilik 22 Nov 2026):

| Bagian | Isi | Status |
|---|---|---|
| D0 | Langkah 0: pisahkan inti dan paket genre | selesai (#44, #46) |
| D1 | Poin 0b, 1, 2, 4: sisa kebocoran genre, templat naskah + validator, keputusan tingkat video dan shot | selesai (#45) |
| D2 | Poin 3, 3b, 3c, 3d: penataan panggung, liputan dialog, arah hadap, berjalan dengan tujuan dan lintasan | implementasi + tes/render dasar lulus; audit ulang menunggu bukti audio pada HEAD dan pemeriksaan pemilik |
| D3 | Poin 5, 6, 7: perpustakaan resep, model AI opsional, bukti video Nuh dan Hud otomatis | belum |

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
0b. **Sisa kebocoran genre di inti (temuan audit Claude D0, 22 Nov 2026), kerjakan di awal D1:**
   `sutradara/garis_waktu.py` masih mengenal `kartu_dalil` dan `rencana["dalil"]` (sisipan waktu baca), dan
   `sutradara/suara/campur.py` masih menambah kilau untuk kartu dalil. Jadikan keduanya kait (hook) yang didaftarkan
   paket genre, misalnya "sisipan waktu baca" dan "efek kemunculan elemen", sehingga inti tidak menyebut nama elemen
   genre. Syarat lulus sama dengan D0: render identik dan tes genre tiruan tetap lulus.
1. **[D1] Templat naskah untuk AI gratis.** FORMAT NASKAH SUDAH DITETAPKAN di `sutradara/antrean.py` (dipakai bot: antrean
   `antrean/<id>/naskah.json` yang disetujui pemilik = masukan sutradara). Jangan membuat format kedua; perluas bila perlu.
   - Format per beat: narasi, kata kunci, dalil (rujukan saja; teks diambil oleh verifikasi), suasana, dan peran.
   - Templatnya juga harus mendorong mutu cerita: fakta terkuat di depan, cerita utuh dalam satu video, setiap
     kalimat menambah informasi atau ketegangan.
   - Sertakan validator yang menjelaskan kesalahan dalam bahasa Indonesia yang bisa dipahami orang awam.
2. **[D1] Keputusan tingkat video:**
   - visual inti dan jalur perubahannya;
   - busur emosi diterjemahkan ke preset suasana;
   - peran diterjemahkan ke cara tampil (sesuai tabel PANDUAN_GAYA);
   - hook diambil dari beat paling dramatis.
3. **[D2] Penataan panggung otomatis:** sutradara yang menentukan koordinat. Pelaku aksi ditempatkan di samping visual
   inti, pihak lawan di seberang atau melintas, posisi konsisten antar-shot, dan tidak saling menutupi. Penjaga
   `PELAKU_JAUH`/`BUKAN_PELAKU_DEKAT` harus lulus tanpa koordinat yang ditulis tangan.
3b. **[D2] Liputan dialog (shot–reverse shot)**: dari naskah, sutradara tahu siapa bicara dan siapa menjawab, lalu kamera
   bergantian dekat (setengah badan) ke pembicara, dengan sisipan reaksi pendengar bila reaksinya penting. Konsep
   `dialogue_exchanges` (pembicara -> penjawab) sudah ada di mesin-video cabang `feat/short-term-production-intelligence`
   (`docs/AI_STORY_DIRECTOR.md`): bawa konsepnya. Layar tenang/gerak minimal boleh bila dialog yang membawa cerita.
3c. **[D2] Arah hadap saat berinteraksi** (pemilik, 22 Nov 2026, dari bukti serah-terima B2 yang semua tokohnya
   menghadap kamera): tokoh yang saling bicara, menyerahkan/menerima barang, menunjuk, atau mengejek harus
   menghadap lawannya (samping atau tiga-perempat, sisi kiri/kanan sesuai posisi), bukan menghadap kamera. Tampak
   depan untuk berbicara ke penonton, kerumunan yang menonton, atau reaksi; tampak belakang untuk sudut pandang
   ikut tokoh, kepergian, atau tokoh yang sedang memandang sesuatu. Sutradara yang memilih arah hadap, bukan nilai
   bawaan. Bila perlu, tambahkan arah tiga-perempat di rangka tokoh. Penjaga memberi PERIKSA (bukan GAGAL) bila
   pasangan serah-terima/dialog sama-sama menghadap kamera tanpa alasan.
3d. **[D2] Berjalan/berlari sesuai tujuan** (pemilik, 22 Nov 2026). Saat ini `jalan`/`lari` hanya siklus kaki di
   tempat; tokoh tidak berpindah dan tidak otomatis menghadap arah gerak.
   - Tokoh yang berjalan/berlari punya **tujuan** (benda, tokoh, atau tepi layar yang mewakili tempat) dan
     **lintasan** x/y dari awal ke tujuan. Tubuh menghadap arah lintasan (samping dan sisi kiri/kanan otomatis
     dari arah gerak), atau menjauh/mendekat (belakang/depan) bila lintasannya ke dalam/keluar layar.
   - Kecepatan langkah selaras dengan kecepatan berpindah, supaya kaki tidak tampak meluncur.
   - **Arah layar konsisten antar-shot:** perjalanan menuju tempat yang sama tetap bergerak ke sisi layar yang
     sama (kaidah 180 derajat). Kembali/kabur = arah sebaliknya. Pengejar dan yang dikejar searah.
   - Berbalik arah hanya bila cerita memang berbalik, dengan putaran badan (depan/samping/belakang sudah bisa
     diinterpolasi).
   - Penjaga: GAGAL bila `jalan`/`lari` tidak punya lintasan atau tujuan, kecuali ditandai `di_tempat` dengan
     alasan (mis. kamera ikut bergerak). PERIKSA bila arah hadap berlawanan dengan arah gerak, atau arah layar
     berganti antar-shot menuju tujuan yang sama.
**3e. [D2 — tambahan atas keputusan pemilik, 24 Nov 2026] Pemahaman peristiwa dan keputusan visual dari naskah.**
- Sutradara tidak boleh hanya memilih resep berdasarkan kata kunci atau menyalin komposisi contoh Nuh. Setiap beat harus diurai menjadi peristiwa terstruktur: pelaku, aksi, sasaran/objek, lokasi atau arah, perubahan keadaan yang benar-benar disebut, serta hubungan urutan/sebab-akibat bila dinyatakan naskah.
- Dari peristiwa itu, sutradara memilih apa yang harus terlihat: siapa yang tampil, apa yang dilakukan, benda/lingkungan mana yang berubah, pose/ekspresi, blocking, arah hadap, ukuran shot, kamera, dan gerak. Keputusan harus merujuk bagian narasi pemicunya; jangan menambah aksi, benda, atau akibat yang tidak didukung naskah/dalil.
- Keadaan visual harus digerakkan oleh peristiwa, bukan persentase indeks beat. Contoh: benda baru berubah menjadi rusak setelah beat menyebut kerusakan; perjalanan baru berakhir saat tujuan naratif tercapai. Keadaan harus berlanjut konsisten ke shot/beat berikutnya.
- Jalur dasar wajib deterministik dan berjalan tanpa model AI, tanpa koordinat/shot yang ditulis tangan, serta tidak boleh bergantung pada frasa khusus cerita Nuh/Ya'juj. Model opsional D3 tidak boleh menjadi syarat untuk menghasilkan rencana.
- Jika pelaku, sasaran, atau perubahan keadaan tidak dapat dipastikan dari naskah terstruktur dan aturan, jangan mengarang. Pertahankan visual aman yang tidak menyatakan fakta baru dan tandai PERIKSA dengan alasan yang jelas.
- Bukti D2 tambahan: uji naskah dari kisah yang berbeda dengan Nuh/Ya'juj dan periksa bahwa perubahan visual mengikuti peristiwa per beat. Mahsyar 1 dipakai sebagai salah satu naskah uji lintas cerita pada D3, bukan pengganti bukti wajib Nuh dan Hud.
 
**Implementasi awal pemetaan peristiwa ke visual (24 Nov 2026, masih perlu audit):**
- `peristiwa.py` mengekstrak aksi eksplisit, peran beat, sasaran yang disebut, dan perubahan keadaan eksplisit beserta bukti frasa.
- `sutradara.py` menyertakan peristiwa pada beat dan shot; aksi eksplisit dapat mengarahkan pose/gerak. Tidak ada perubahan keadaan berdasarkan persentase indeks beat pada jalur visual padang.
- Latar padang dipilih dari deskripsi ruang (padang/tanah rata/bumi putih), bukan nama Nabi atau judul kisah.
- `visual/peristiwa.py` dan renderer menyediakan komponen SVG untuk tanah terbelah, matahari didekatkan, kerumunan, keringat, dan jejak pelarian. Peristiwa lain belum memiliki komponen visual khusus dan tidak boleh dipaksakan menjadi objek yang tidak didukung.
- Tes baru mencakup frasa nyata Mahsyar 1. Ini baru uji unit/pemetaan, belum render MP4 Mahsyar 1 dan belum membuktikan seluruh naskah bisa divisualkan. Pengenalan bahasa masih berbasis pola eksplisit, bukan pemahaman bahasa bebas.

**Status D2: implementasi utama tersedia; belum dinyatakan selesai.** Status dibedakan antara implementasi, tes otomatis, bukti render, dan tinjauan manusia.

| Poin | Implementasi | Tes otomatis | Bukti render | Batas audit |
|---|---|---|---|---|
| 3 — blocking | Koordinat pelaku dihitung dari visual inti; pihak lawan ditempatkan berseberangan; penjaga kedekatan tegas untuk rencana otomatis; pemeriksa kontinuitas panggung mendeteksi tumpang tindih/pergeseran posisi. | Tes blocking, pelaku jauh, overlap, dan stabilitas posisi. | 14 shot / 644 bingkai / 53,7 detik memuat pembangunan bahtera dan kelompok. | Belum membuktikan seluruh variasi formasi dan jarak; perlu tinjauan pemilik. |
| 3b — dialog | Shot–reverse shot bergantian pada pembicara/penjawab; sisipan reaksi pendengar bila reaksi penting disebut dalam narasi. | Tes dua-shot dan tiga-shot seruan–reaksi–jawaban. | Render menampilkan seruan, reaksi penentang, dan jawaban. | Variasi sudut/ukuran close-up dan gerak kontinu perlu ditinjau. |
| 3c — arah hadap | Dialog, serah-terima, tunjuk, dan interaksi mengarahkan tokoh kepada lawan; mendekat/menjauh dan tiga-perempat didukung. | Tes arah hadap interaksi dan tiga-perempat. | Render memuat serah-terima, tunjuk, dan tiga-perempat. | Tidak semua kombinasi interaksi/komposisi ditinjau manusia. |
| 3d — perjalanan | Tujuan benda/tokoh/tepi/kedalaman, lintasan x/y, cadence, arah 180 derajat, pengejaran searah kanan/kiri, dan putar balik sesuai cerita. | Tes tujuan/lintasan, cadence, 180 derajat, pengejaran dua arah, dan putar balik. | Render memuat perjalanan, menjauh ke kedalaman, putar balik, dan pengejaran kanan/kiri. | Contoh tidak mencakup semua lintasan kompleks; pemilik perlu menonton MP4. |

**CI #529 pada HEAD `76c068e` (run `45207029799`):** sukses. Tes bot Telegram dan tes lengkap lulus; `python -m pytest -q` menghasilkan **320 passed**. Render bukti D2 menghasilkan **14 shot / 644 bingkai / 53,7 detik video** (95 detik waktu render, 1 worker). Pemeriksaan final enam contoh (`b2_adab_barang`, `dabbah_dhuha`, `dajjal_dua_sungai`, `demo_gerak`, `nuh_mengejek`, `yajuj_majjuj`) sukses tanpa GAGAL. Artefak `bukti-visual-tahap-d2` diunggah. Langkah validasi lama untuk fase lain berstatus skipped karena tidak relevan pada job ini.

**Uji audio-cache pada HEAD `76c068e` (workflow run `45284285899`):** sukses. Menggunakan cache produksi ElevenLabs yang sudah ada; langkah cek naskah, pembuatan narasi, dan simpan ke cabang suara dilewati. Laporan: 29 kata terjajar; durasi MP3 13,52 dtk; padding ekor hening 0,43 dtk; durasi video 15,12 dtk; durasi stream audio-video 15,11 dtk (selisih 0,01 dtk); -16,89 LUFS; true peak -1,75 dBTP. Artefak `bukti-audio-elevenlabs-d2` berisi laporan JSON, lembar kontak, dan MP4. Ini bukan panggilan API berbayar baru.

Uji audio-cache sudah diulang setelah perubahan pipefail pada HEAD `4a6d061` (run `45288876269`) dan sukses; detail bukti terbaru tercatat pada log 24 Nov 2026 di bawah. D2 tetap menunggu tinjauan video kontinu/komposisi oleh pemilik.

**Catatan PERIKSA dipertahankan:** hook kronologis dan kesinambungan `surat_amanah` pada contoh B2; derajat hadis Tirmidzi 3153 diperselisihkan; beberapa shot dialog/reaksi memiliki komposisi close-up mirip. Ini bukan GAGAL otomatis dan tidak boleh dihapus dari laporan.

D2 belum dicentang. CI #529 dan uji audio-cache run `45284285899` lulus pada SHA `76c068e`, tetapi perubahan pipefail/dokumentasi sesudahnya memerlukan uji ulang audio-cache pada HEAD baru. Penutupan tetap menunggu bukti audio terbaru dan tinjauan pemilik atas kelancaran gerak kontinu/variasi komposisi video. D3 tidak dikerjakan dalam PR ini.

4. **[D1] Keputusan tingkat shot:**
   - pecah enumerasi menjadi shot per kata dan eskalasi pada pengulangan;
   - kamera mengikuti posisi beat;
   - teks layar 1–3 kata yang menamai makna;
   - `potong_di` dipilih otomatis;
   - gerak dan ekspresi tokoh diturunkan dari kata kerja dan emosi narasi;
   - efek suara mengikuti aksi (Tahap A).
5. **[D3] Perpustakaan resep adegan:** potongan siap pakai yang diambil dari video yang disetujui pemilik, misalnya
   "kaum mengejek", "azab datang", "doa sunyi". Sutradara memilih dan merangkainya. Format resep harus bisa
   ditambah orang lain tanpa menyentuh kode inti.
6. **[D3] Model AI (opsional, di balik bendera, mati secara bawaan):**
   - model murah dipakai hanya ketika aturan ragu;
   - biaya dicatat per video;
   - mesin harus tetap menghasilkan rencana yang layak tanpa model.
7. **[D3] Bukti:**
   - naskah kisah Nabi Nuh dijadikan rencana dan video otomatis penuh;
   - satu kisah baru (misalnya Nabi Hud) juga dibuat tanpa menyunting kode atau rencana dengan tangan;
   - lampirkan lembar kontak keduanya dan perbandingan dengan versi manual.
   - Tambahkan naskah Mahsyar 1 dari repo `mesin-video` sebagai uji lintas cerita: gunakan `naskah/mahsyar1.txt` dan alignment `audio_manual/mahsyar1_ozhy/narasi.waktu.json` sebagai sumber uji; jangan mengubah naskah atau menganggap MP3 sebagai bukti visual.
   - Untuk setiap contoh, catat pemetaan beat/peristiwa ke visual yang dihasilkan; bukti harus menunjukkan visual berubah karena peristiwa narasi, bukan karena urutan beat atau resep yang dikunci ke satu kisah.
   Kelayakan tayang diputuskan pemilik, bukan pengembang.

### Catatan arah hasil akhir dan larangan duplikasi (keputusan pemilik, 24 Nov 2026)

D2 **ditahan, tidak di-merge sekarang**. PR #48 tetap menjadi satu-satunya cabang implementasi D2; pekerjaan berikutnya
tidak boleh menyalin atau membuat ulang fitur D2 di cabang lain.

Sebelum menambah kode setelah D2:
1. Buat peta fitur dari kode aktual: nama kemampuan, satu modul pemilik, antarmuka publik, semua pemanggil, dan tes.
2. Periksa apakah kemampuan sudah ada di inti, paket Kisah Islami, PR #48, atau repo referensi. Jika ada, perbaiki/perluas
   pemiliknya; jangan membuat parser, state manager, renderer, rig, kamera, timeline, atau pipeline suara kedua.
3. Jaga batas inti vs paket genre dari D0. Peristiwa khusus Kisah Islami berada di paket genre; komposisi, kamera,
   rig, gerak, waktu, dan audio generik tetap memakai modul inti yang sudah ada.
4. Kerjakan jalur event-to-visual deterministik dari bukti narasi hingga shot. Keadaan benda/lingkungan harus berasal
   dari peristiwa yang disebut dan bertahan lintas shot; jangan dihitung dari nomor/indeks beat.
5. Gunakan Nuh dan Ya'juj sebagai sumber prinsip visual (cahaya, kedalaman, komposisi, skala, atmosfer), bukan cetakan
   adegan. Buktikan transfer prinsip pada Hud dan Mahsyar 1 tanpa mengubah naskah/koordinat secara manual.
6. Catat kebutuhan visual yang belum didukung sebagai PERIKSA; jangan mengarang aksi, objek, atau akibat.

**Temuan visual pemilik:** hasil render yang dikirim pemilik memperlihatkan mata tokoh hanya satu. Ini menjadi temuan
PERIKSA terbuka untuk audit rig/wajah dan renderer; belum ditetapkan akar masalahnya. Periksa geometri kedua mata,
arah hadap, clipping, dan urutan lapisan. Tes wajib mencakup depan dan tiga-perempat agar perbaikan tidak hanya
menutupi cacat pada satu sudut. Jangan membuat sistem mata alternatif.

### Hasil audit kepemilikan fitur dan jalur peristiwa (24 Nov 2026)

Audit dilakukan pada kode `main` dan cabang PR #48. Ini audit statis alur data/kepemilikan, bukan klaim bahwa render MP4 baru sudah diuji.

**Peta pemilik yang terkonfirmasi dari kode:**

| Kemampuan | Pemilik aktual | Temuan audit |
|---|---|---|
| Kontrak/pemuatan genre | `sutradara/genre.py` | Satu kontrak `PaketGenre`; pertahankan |
| Masukan dan validasi naskah | `sutradara/antrean.py` + paket genre | Jangan membuat format antrean kedua |
| Orkestrasi netral | `sutradara/direktur.py` | Memanggil satu sutradara milik paket |
| Keputusan Kisah Islami | `paket_genre/kisah_islami/sutradara.py` | Satu pemilik perencanaan; perluas di sini |
| Ekstraksi peristiwa | `paket_genre/kisah_islami/peristiwa.py` pada PR #48 | Fondasi ada, tetapi akurasi relasi aktor/aksi/sasaran belum memadai |
| Skema peristiwa | `sutradara/rencana/rencana.schema.json` | Definisi bersama sudah tersedia; perluas definisi ini, jangan buat skema kedua |
| Komposisi adegan | `sutradara/adegan.py` | Pemilik komposisi dan pemanggil renderer paket |
| Komponen visual genre | `paket_genre/kisah_islami/visual/` | Satu pustaka visual genre; jangan menggambar ulang di parser/sutradara |
| Render genre | `paket_genre/kisah_islami/renderer.py` | Sudah memanggil `visual.peristiwa.render_semua` |
| Rig/wajah tokoh | `sutradara/gaya/tokoh.py` | Satu pemilik geometri tubuh dan wajah |
| Gerak tokoh | `sutradara/gerak.py` | Satu pustaka gerak |
| Kamera | `sutradara/kamera.py` | Satu transform kamera |
| Keyframe/waktu shot | `sutradara/waktu.py`, `sutradara/garis_waktu.py` | Jangan menambah sistem waktu kedua |
| Audio | `sutradara/suara/` | Satu jalur narasi, sinkronisasi, dan campur |

**Temuan teknis yang harus dituntaskan sebelum memperluas katalog visual:**

1. `peristiwa.py::analisis_peristiwa` saat ini mengisi `aktor` dengan seluruh daftar peran pada beat. Ia belum mengidentifikasi pelaku spesifik dari struktur kalimat.
2. Pemilihan `sasaran` mengambil objek berikutnya atau objek terdekat dalam seluruh kalimat. Pada kalimat dengan beberapa aksi/objek, relasi dapat salah; setiap aksi perlu dihubungkan hanya ke sasaran yang didukung frasa sumber.
3. Perubahan keadaan baru dikenali untuk sebagian aksi dan sebagian objek. Belum ada relasi urutan/sebab-akibat eksplisit yang dapat ditelusuri.
4. `sutradara.py::_keadaan` masih menggunakan indeks/persentase beat untuk progres bahtera dan dinding Ya'juj. Ini tidak memenuhi aturan bahwa keadaan hanya berubah saat peristiwa menyatakannya.
5. `peristiwa_visual` ditempelkan ke setiap shot dari beat yang sama. Belum ada pemilik state lintas beat yang mengatur kapan visual mulai berubah, tetap terlihat, berubah lagi, atau selesai.
6. Renderer peristiwa saat ini baru memiliki visual khusus untuk beberapa aksi/objek (tanah terbelah, matahari didekatkan, kerumunan, keringat, jejak lari). Aksi lain tidak boleh dipaksa menjadi visual yang tidak didukung.

**Keputusan implementasi agar tidak ada duplikasi:**
- Tetap gunakan `analisis_peristiwa` sebagai satu pintu ekstraksi; tingkatkan hasilnya agar aktor, aksi, sasaran, bukti frasa, dan perubahan keadaan terhubung secara eksplisit.
- Tetap gunakan definisi `$defs.peristiwa` di skema rencana sebagai kontrak data resmi. Ubah hanya bila kebutuhan baru terbukti dan tambahkan tes skema.
- Tambahkan pengelolaan transisi/riwayat keadaan pada pemilik perencana Kisah Islami yang sudah ada, bukan membuat state manager terpisah. Renderer menerima keadaan hasil keputusan itu dan hanya menggambar.
- Pertahankan `visual/peristiwa.py` sebagai pemilik komponen SVG peristiwa. Komponen baru harus dapat dipakai ulang dan didaftarkan melalui jalur renderer yang sama.
- Pertahankan kamera, gerak, rig, timeline, dan audio yang sudah ada. Perencana hanya menyuplai keputusan ke antarmuka mereka.
- Untuk kalimat ambigu, simpan bukti dan tandai PERIKSA; jangan mengarang aktor, sasaran, atau perubahan keadaan.

**Urutan pekerjaan teknis yang disarankan:**
A. Tes relasi aktor–aksi–sasaran untuk kalimat sederhana, pasif, banyak aktor, banyak objek, negasi, dan dua peristiwa dalam satu kalimat.
B. Perbaiki ekstraksi pada pemilik `peristiwa.py` dan kontrak skema yang sama.
C. Ganti progres berbasis indeks beat dengan transisi keadaan eksplisit pada pemilik sutradara yang sama.
D. Pastikan keadaan dan visualnya konsisten antar-shot dan antar-beat.
E. Baru perluas komponen visual yang terbukti dibutuhkan naskah.
F. Render lintas cerita Nuh, Hud, dan Mahsyar 1; periksa apakah setiap perubahan layar punya bukti narasi.

Tidak ada fitur baru atau modul paralel yang dibuat dalam audit ini. PR #48 tetap tidak di-merge.

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

## Penyempurnaan setelah Tahap G

Poin berikut **ditunda atas keputusan pemilik pada 22 Nov 2026**. Jangan mengerjakannya pada Tahap B2 atau tahap lain sebelum seluruh tahap yang direncanakan selesai. Setelah itu, kerjakan hanya sebagai penyempurnaan visual; **jangan mengganti nama preset maupun antarmuka pemanggilannya** yang telah dibakukan di `docs/PANDUAN_GAYA.md` bagian 1b.

1. **Bedakan `senyum` dan `ejek` lebih tegas.**
   - Gejala pada bukti saat ini: lengkung mulut senyum dan garis mulut ejek masih berdekatan secara visual; bentuk alis menjadi pembeda utama, tetapi belum cukup jelas pada tampilan kecil.
   - Bukti JPG: `b2-shot-01.jpg`, `b2-shot-02.jpg`, dan `lembar-ekspresi-b2.jpg` (bandingkan baris/varian senyum dan ejek).
   - Sasaran nanti: perbedaan terbaca pada ukuran ponsel tanpa membuat ekspresi Kisah Islami menjadi komikal.

2. **Bedakan `takut` dari `kepergok_panik`.**
   - Gejala pada bukti saat ini: mata tegang dan alis cemas pada kedua preset masih memberi kesan yang mirip; kualitas "baru ketahuan" belum terbaca terpisah dari takut umum.
   - Bukti JPG: `lembar-ekspresi-b2.jpg` dan `lembar-kontak-b2.jpg`.
   - Sasaran nanti: `takut` tetap menyatakan ancaman/ketakutan umum, sedangkan `kepergok_panik` menyatakan reaksi spontan saat tertangkap basah. Nama preset tetap.

3. **Perjelas kerut hidung pada `jijik_ilfil`.**
   - Gejala pada bukti saat ini: kerut hidung sudah dikendalikan oleh parameter, tetapi kurang terbaca pada lembar kontak berukuran kecil.
   - Bukti JPG: `lembar-ekspresi-b2.jpg` dan `b2-shot-04.jpg`.
   - Sasaran nanti: kerut pangkal hidung terlihat jelas pada ukuran ponsel, tanpa mengubah nama preset atau menerapkannya ke wajah cahaya.

**Batas pekerjaan tertunda:** jangan mengubah gambar wajah untuk tiga catatan di atas sekarang. Ketiganya bukan penghalang penyelesaian Tahap B2 dan bukan alasan menahan tahap berikutnya. Ketika penyempurnaan nanti disetujui untuk dikerjakan, perubahan cukup pada bentuk/parameter gambar wajah; kontrak nama dan antarmuka tetap kompatibel.

Fase 7 (perluasan genre) **tidak dibuka** sebelum Fase 6 terbukti berjalan, pematangan (Tahap G) menunjukkan hasil dan pemilik menyetujuinya secara tertulis. Ini sesuai keputusan pemilik bahwa Kisah Islami harus
konsisten dulu. Jangan memulai Fase 7 atas inisiatif sendiri.


- 24 Nov 2026 — CI #529 pada SHA `76c068e` sukses: 320 tes Python, tes bot, render D2 14 shot/644 bingkai/53,7 detik, dan pemeriksaan enam contoh. Uji audio-cache run `45284285899` pada SHA yang sama sukses: 29 kata, selisih stream 0,01 detik, -16,89 LUFS, -1,75 dBTP; memakai cache, tanpa panggilan API berbayar. Workflow `suara.yml` kemudian diperketat dengan `set -euo pipefail` agar kegagalan narasi tidak tertutup oleh `tee`.
- 24 Nov 2026 — Verifikasi ulang setelah pipefail: CI PR run `45288621235` sukses pada SHA `4a6d061`. Uji audio-cache `uji_d2` run `45288876269` juga sukses pada SHA yang sama. Cache produksi ElevenLabs digunakan (29 kata terjajar); durasi MP3 13,52 detik, padding hening 0,43 detik, video 15,12 detik, stream audio-video 15,11 detik (selisih 0,01 detik), loudness -16,89 LUFS, true peak -1,75 dBTP. Tahap pembuatan narasi baru dan penyimpanan cabang suara dilewati; tidak ada panggilan API berbayar baru. Artefak `bukti-audio-elevenlabs-d2` tersedia. D2 tetap belum dicentang sampai pemilik meninjau MP4 untuk kelancaran gerak kontinu dan variasi komposisi. Catatan PERIKSA B2/Tirmidzi 3153 dipertahankan.



### Pembaruan penutupan D2 — 24 Nov 2026

Pemilik mengonfirmasi audit visual dan suara lulus. Perbaikan wajah dari PR #50 telah dipindahkan ke cabang D2/PR #48, disertai tes urutan SVG dan model rambut. Koreksi parser: aktor hanya diisi bila nama/peran disebut eksplisit; tujuan perpindahan dipisahkan dari sasaran aksi melalui field `tujuan` pada skema. Visual `tenggelam` tidak lagi memakai visual keringat. Perubahan-perubahan ini belum boleh dianggap lulus CI: run yang sempat berjalan pada revisi antara gagal pada dua assertion urutan lapisan wajah, lalu urutan SVG diperbaiki. Revisi paling akhir belum memiliki hasil CI karena workflow tidak terpicu oleh pembaruan API. Jalankan `python -m pytest -q`, render D2, dan workflow audio-cache pada HEAD final sebelum status D2 diubah menjadi selesai.