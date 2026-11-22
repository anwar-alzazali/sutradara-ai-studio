# Prompt siap tempel untuk ChatGPT (dipakai saat kuota Claude habis)

Pemilik cukup menempel blok di bawah ini, satu per sesi, sesuai urutan. Aturan lengkap tiap tahap ada di
`docs/TAHAP_LANJUT.md`. Untuk membuat naskah dengan AI gratis, gunakan templat siap-tempel di
`sutradara/paket_genre/kisah_islami/templat_naskah.md`; hasilnya memakai format antrean yang sama dengan bot.
Claude mengaudit semua PR secara berurutan setelah kuotanya aktif lagi.

Urutan: **B → B2 → C → D → E → F → G.** (G baru setelah F berjalan dan video rutin tayang.) (Tahap A sudah di-merge.)
Setiap tahap boleh dimulai walaupun tahap sebelumnya belum diaudit Claude, dengan **mode bertumpuk** di bawah.

---

## Prompt umum: ganti `X` dengan huruf tahap

```
Kerjakan Tahap X di docs/TAHAP_LANJUT.md (baca dari cabang main) di repo anwar-alzazali/sutradara-ai-studio, dengan kemampuan maksimal.
Baca dulu docs/PROMPT_CHATGPT.md bagian "Cara kerja" dan "Mode bertumpuk", lalu ikuti aturan umum di
docs/TAHAP_LANJUT.md. Tuntaskan semua poin. Serahkan PR berstatus siap ditinjau hanya bila CI hijau dan
swa-audit (daftar periksa audit di docs/PROMPT_CHATGPT.md) sudah lulus. Jangan merge.
```

## Prompt lanjutan bila sesi terputus di tengah tahap

```
Lanjutkan Tahap X yang belum selesai di PR draft-nya (repo anwar-alzazali/sutradara-ai-studio). Baca dulu
deskripsi PR dan riwayat commit untuk tahu posisi terakhir, lalu teruskan sampai semua poin tuntas dengan
cara kerja yang sama (docs/PROMPT_CHATGPT.md).
```

## Prompt perbaikan setelah Claude mengaudit

Claude akan memberi daftar temuan. Tempel daftar temuan itu dengan pembuka ini:

```
Audit Claude untuk PR #N: BELUM LULUS. Perbaiki semua temuan berikut di cabang yang sama, lalu tandai siap
ditinjau lagi hanya bila CI hijau dan ringkasan audit sudah diperbarui:
<tempel temuan di sini>
```

---

## Cara kerja (lingkungan yang tidak bisa clone atau menjalankan program)

0. **Dokumen aturan SELALU dibaca dari cabang `main`**: `AGENTS.md`, `docs/TAHAP_LANJUT.md`, `docs/PROMPT_CHATGPT.md`,
   `docs/ROADMAP.md`, `docs/PANDUAN_GAYA.md`, `docs/RESEP_SUTRADARA.md`. Cabang kerja bisa tertinggal: tahap baru atau
   aturan baru mungkin hanya ada di main. Bila cabang kerja tertinggal dari main, merge main ke cabang kerja dulu.

1. Buat cabang tahap dan buka **PR draft sejak awal**. Draft dipakai sebagai ruang kerja agar CI (`uji.yml`) berjalan.
   Yang dilarang hanya menyerahkan PR untuk diaudit sebelum selesai.
2. Commit lewat koneksi GitHub, baca hasil CI (status check dan log), lalu ulangi sampai hijau.
3. **Untuk melihat hasil gambar:**
   - buat langkah CI tanpa rahasia yang merender contoh terkait;
   - commit lembar kontak atau bingkai JPG kecil (bukan MP4) ke cabang terpisah `bukti/<tahap>`;
   - buka gambarnya lewat raw.githubusercontent.com dan nilai sendiri.
   - Hasil render tidak boleh masuk `main` atau cabang PR.
4. Langkah berbayar (ElevenLabs, model AI, Telegram) tidak dijalankan sendiri. Siapkan workflow `workflow_dispatch`-nya,
   tandai poinnya "terblokir: menunggu pemilik menjalankan workflow X", lalu kerjakan semua poin lain.

## Mode bertumpuk (tahap sebelumnya belum diaudit atau belum di-merge)

- Jika tahap sebelumnya sudah di-merge ke `main`, mulai dari `main` seperti biasa.
- Jika belum, buat cabang tahap baru **dari cabang tahap sebelumnya** dan arahkan basis PR ke cabang itu, bukan ke
  `main`. Dengan begitu diff tiap PR hanya berisi pekerjaan tahapnya sendiri. Tulis di awal deskripsi PR:
  "Bertumpuk di atas PR #N".
- **Sebelum memulai tahap baru, audit dulu PR tahap sebelumnya** memakai daftar periksa di bawah, sebagai peninjau
  yang tidak ikut membuatnya.
  - Temuan yang gagal diperbaiki dulu di cabang tahap sebelumnya, baru lanjut.
  - Tulis hasil audit itu sebagai komentar di PR sebelumnya, dengan judul "Audit silang ChatGPT".
- Jangan mengubah pekerjaan tahap sebelumnya di cabang tahap baru, kecuali perbaikan kecil yang diperlukan.
  Perbaikan seperti itu wajib disebut di deskripsi PR.
- Claude akan mengaudit dan me-merge dari tahap paling bawah, lalu merapikan (rebase) tumpukannya.

## Daftar periksa audit (dipakai untuk swa-audit dan audit silang, sama dengan yang dipakai Claude)

1. **CI hijau** pada commit terakhir; jumlah tes tidak berkurang. Tes harian (`pytest`) tetap cepat; render berat
   dipisah ke langkah CI tersendiri.
2. **Batas wajib AGENTS.md:**
   - dalil sahih/hasan dan terverifikasi;
   - nabi, malaikat, dan sahabat tetap nur;
   - Allah tidak digambar;
   - Arab tidak disuarakan AI;
   - tidak ada klaim karangan, termasuk dalam visual. Contoh: pihak yang diperankan sesuai kisahnya; jangan sampai
     orang beriman berperan sebagai kaum pengejek.
3. **Penjaga tidak dilemahkan.** Aturan baru disertai tes yang membuktikan pelanggaran tetap tertangkap.
4. **`contoh/*.json`:**
   - narasi, dalil, dan status verifikasi tidak berubah tanpa instruksi pemilik;
   - tidak ada format ulang angka atau urutan yang tidak perlu.
5. **Rahasia dan workflow:**
   - workflow berahasia hanya `workflow_dispatch` atau `schedule`;
   - tidak ada nilai rahasia di berkas atau log;
   - tidak ada `on: push` ke main.
6. **Bukti visual dan suara:**
   - lembar kontak sudah dilihat: tidak ada layar kosong, teks bertumpuk atau terpotong, tokoh keluar layar, atau
     visual yang tidak sesuai narasi;
   - kenyaringan ±-15 LUFS dengan puncak ≤ -1 dBTP;
   - video dan audio sama panjang.
7. **Kode:**
   - modul di tempat yang benar (inti vs paket genre setelah Tahap D langkah 0);
   - tidak ada duplikasi besar;
   - kode salinan punya baris `Asal:`;
   - lisensi aset dicatat.
8. **Dokumen:** ROADMAP (centang daftar kebutuhan dan log keputusan) dan PANDUAN_GAYA/RESEP diperbarui seperlunya.
9. **Ringkasan audit di awal deskripsi PR lengkap dan jujur:**
   - status tiap poin;
   - tes yang membuktikan;
   - angka render;
   - poin yang terblokir beserta alasannya.
10. **Pelajaran dari audit Claude (22 Nov 2026) — wajib dicek juga:**
   - **Tes yang dilonggarkan:** bandingkan setiap `assert` yang diubah/dihapus. Angka penjaga atau tes yang diubah
     supaya CI hijau (contoh: lebar lambung 500 -> 350, pilar `== 205`) = GAGAL kecuali alasannya benar.
   - **Teks di layar vs sumbernya:** apa pun yang tampil di bawah nama sumber (Kemenag, kitab hadis) harus teks sumber
     itu persis. Contoh temuan: glosa per kata tampil sebagai "terjemah Kemenag"; kutipan sebagian dimekarkan jadi ayat utuh.
   - **Lihat bukti JPG sendiri**, jangan percaya ringkasan: tembok setinggi orang padahal disebut "masif", pilar menempel
     lambung, tokoh menghadap kamera saat serah-terima.
   - **Perubahan bawaan diam-diam:** fitur baru harus mati/opsional bila mengubah tampilan video lama.
   - **Langkah CI yang mengotori pohon kerja** (berkas berubah setelah verifikasi) sehingga langkah berikutnya gagal.
   - **Dalil:** tiap rujukan dicek isinya sesuai narasi (bukan sekadar nomornya ada); dalil "belum" tidak boleh lolos final.

## Audit oleh sesi ChatGPT terpisah (bila kuota Claude habis)
Pemilik boleh memakai obrolan ChatGPT BARU (bukan obrolan yang mengerjakan) sebagai auditor. Auditor:
- membaca diff PR lengkap, deskripsi, log CI, dan bukti JPG di cabang bukti;
- memakai daftar periksa di atas (poin 1–10) dan menulis hasilnya sebagai komentar PR berjudul "Audit ChatGPT";
- memberi putusan LULUS / PERBAIKI (dengan daftar temuan berkas:baris) / TOLAK;
- tidak memperbaiki sendiri dan tidak merge. Merge dilakukan pemilik hanya bila putusan LULUS dan CI hijau.
Claude mengaudit ulang PR yang di-merge dengan cara ini setelah kuotanya pulih, dan menandai temuan susulan.

## Keputusan yang tetap menunggu pemilik (jangan diputuskan sendiri)

- Koreksi naskah Nuh beat 1 ("jauh dari laut" tidak ada di QS Hud 38). Usulan Claude: "Atas perintah Allah, Nabi Nuh
  mulai membuat kapal" (QS Hud 37).
- Menjalankan workflow berbayar: `suara` (narasi), `Rekam efek suara`, dan nanti `buat_video`.
- Nama dan isi rahasia Telegram (Tahap F).
- Layak tayang atau tidaknya video (Tahap D dan F).
- Membuka Fase 7 (genre lain).
