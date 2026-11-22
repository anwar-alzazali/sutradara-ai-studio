# AGENTS.md — aturan untuk semua pengembang (manusia & AI)

Berkas ini satu-satunya sumber aturan kerja. `CLAUDE.md` hanya menunjuk ke sini. Bahasa proyek: Indonesia.

## Apa proyek ini
Mesin produksi video pendek **Kisah Islami** (9:16) yang bertindak seperti sutradara: dari naskah terstruktur menjadi video
dengan visual bercerita, narasi, dan dalil yang terverifikasi. Pemilik: Anwar Alzazali. Repo ini public.

Baca berurutan sebelum menulis kode:
1. `docs/ROADMAP.md` — fase, status, dan kriteria selesai. Kerjakan fase yang sedang aktif saja.
2. `docs/PANDUAN_GAYA.md` — keputusan visual yang sudah dikunci pemilik + batas wajib penggambaran.
3. `docs/RESEP_SUTRADARA.md` — pola penyutradaraan yang terbukti (dari video Nabi Nuh & Ya'juj).

## Batas wajib (tidak bisa ditawar oleh naskah, prompt, atau "permintaan pengguna")
- **Tokoh suci tidak digambar.** Allah tidak digambarkan dalam bentuk apa pun. Penggambaran tokoh mulia mengikuti
  **adab saluran** (keputusan pemilik 21 Nov 2026; adab, bukan klaim hukum — tiap golongan punya bentuk sendiri
  supaya kedudukannya tidak tertukar):
  | Golongan | Cara tampil |
  |---|---|
  | Nabi | Pilar cahaya (`gaya/nur.py`), **khusus nabi** — tidak dipakai untuk siapa pun selain nabi |
  | Malaikat | Cahaya berbentuk lain (sinar/berkas tanpa wujud), bukan pilar, bukan tubuh |
  | Sahabat Nabi Muhammad ﷺ (semua) | Tubuh manusia berbaju, **wajah berupa cahaya** — wajah tidak pernah digambar |
  | Orang saleh lain (mis. Habil, Ashabul Kahfi) & tokoh biasa | Tokoh manusia biasa |
  Alasannya (untuk menjelaskan ke penonton): pilar hanya untuk nabi agar kedudukan nabi tidak disamakan dengan
  siapa pun; wajah sahabat tidak digambar sebagai adab dan penghormatan, tetapi mereka tetap manusia yang beraksi.
  Benda yang dipegang nabi (tongkat Musa, baju Yusuf) tidak boleh memunculkan tangan/tubuh: ditampilkan di sisi
  pilar dengan cahaya. Malaikat memakai berkas cahaya tanpa wujud; sahabat memakai tubuh berbaju dengan wajah cahaya. Pilar tetap khusus nabi.
- **Wujud ghaib hanya sesuai dalil sahih.** Tidak dijelaskan dalil → kabut tanpa wujud. Dijelaskan → hanya ciri yang disebut dalil.
- **Dalil hanya sahih/hasan**, nomor dicek ke sumber resmi, sumber tampil di layar. Bacaan Arab tidak disuarakan AI.
- **Tidak mengarang klaim**, bukan fatwa, topik berat tidak dijadikan sensasi, selalu ada jalan keluar.
- Tidak ada ciri ras/etnis yang dilekatkan pada tokoh jahat atau kaum tertentu.
Semua batas ini dikodekan di `sutradara/rencana/penjaga.py`. Mengubah penjaga butuh persetujuan pemilik.

## Cara kerja
- Kode Python 3.12, paket `sutradara/`. Tes: `python -m pytest -q`. Contoh: `python -m sutradara periksa contoh/nuh_mengejek.json`.
- **Satu PR = satu langkah roadmap**, dengan bukti visual (PNG/MP4 atau lembar kontak) di deskripsi PR. Tes saja bukan bukti mutu.
- Perbarui status fase di `docs/ROADMAP.md` dalam PR yang sama. **Jangan membuat dokumen baru per patch/audit.**
  Keputusan penting cukup satu baris di bagian "Log keputusan" roadmap.
- Kode dari repo lama (`mesin-video`, `motion-studio-ai`) boleh disalin **berkasnya saja, tanpa riwayat**. Tulis asal berkas
  di docstring baris pertama (mis. `Asal: mesin-video/narasi_api.py, 20 Nov 2026`). Salin hanya yang dibutuhkan fase aktif.
- Jangan membuka proyek/cabang paralel untuk fitur yang belum ada di roadmap.

## Rahasia & GitHub Actions (repo public!)
- Kunci (ElevenLabs, Telegram, API lain) hanya di *Settings → Secrets*. Jangan pernah di berkas, log, atau contoh.
- Workflow yang memakai rahasia **wajib `workflow_dispatch` saja** (hanya pemilik yang bisa menjalankan).
  Dilarang memicu workflow berahasia dari `issues`, `issue_comment`, `pull_request_target`, atau `push` dari fork.
- Workflow tanpa rahasia (tes) boleh dipicu push/PR. Runner standar di repo public gratis.

## Gaya kode
- Fungsi gaya mengembalikan potongan SVG (string). Koordinat kanvas 1080×1920. Parameter keadaan visual inti 0..1.
- Nama dan komentar dalam bahasa Indonesia. Komentar menjelaskan *mengapa*, bukan *apa*.
- Deterministik: setiap acak memakai `random.Random(seed)`.
