# Bot Telegram Mesin KONTEN (Cloudflare Worker `mesin-konten`)

Pindahan dari `mesin-video/bot/` (21 Nov 2026). Bot, token, dan nama Worker **sama**; hanya kode sumbernya pindah ke sini.

Fitur:
- **Persetujuan video:** tombol ✅ Setujui / ❌ Tolak, lalu alasan cepat atau "Lainnya" + ketik. Keputusan dicommit
  ke `data/persetujuan/<id>.json` di repo ini. Pesan video dikirim workflow dengan `callback_data` `st:<id>` / `tl:<id>`.
- **Balas komentar:** kirim tangkapan layar komentar (tanpa keterangan, atau `k` + catatan).
- **Chat pribadi:** ketik pesan biasa; `/reset` menghapus riwayat.
- Hanya pemilik (`TELEGRAM_CHAT_ID`) yang dilayani.

Fitur lama yang sengaja ditinggalkan: saldo/QRIS, proyek pengguna, rakit, Studio, naskah NGOPAI/iklan. Datanya tetap di
Supabase (schema `konten`); riwayat chat dan catatan biaya masih memakai tabel `pengaturan` dan `biaya_log` di sana.

## Langkah pindah (pemilik, sekali saja, ±10 menit)
1. **Cloudflare** → Workers & Pages → `mesin-konten` → Settings → Build → ubah repositori Git ke
   `anwar-alzazali/sutradara-ai-studio`, cabang `main`, **root directory `bot`**. Simpan, lalu jalankan build/deploy.
2. **Token GitHub:** di GitHub → Settings → Developer settings → Fine-grained tokens, edit token yang dipakai Worker
   (atau buat baru) agar punya akses ke repo `sutradara-ai-studio` dengan *Contents: Read and write*. Bila token baru,
   simpan di Cloudflare sebagai Secret `GH_TOKEN`.
3. Secret lain di Cloudflare tidak berubah (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WEBHOOK_SECRET, ANTHROPIC_API_KEY,
   SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY).
4. Buka sekali di peramban: `https://<alamat-worker>/pasang?k=<WEBHOOK_SECRET>`. Hasil yang benar:
   `{"webhook":true,"perintah":true}` (memasang webhook + daftar perintah di tombol Menu Telegram).
5. **Uji:** GitHub → Actions → *tes telegram* → Run workflow. Tekan ✅ di Telegram → tombol berubah jadi "✅ Disetujui"
   dan berkas `data/persetujuan/uji-<nomor>.json` muncul di repo. Kirim tangkapan layar komentar → draf balasan datang.

Tampilan di Telegram: tombol, menu perintah, dan teks diatur dari kode ini. Nama bot, foto profil, deskripsi, dan
"About" diatur lewat @BotFather (`/mybots` → Edit Bot).
