# Templat naskah Kisah Islami untuk ChatGPT / Gemini

Salin seluruh instruksi ini ke ChatGPT atau Gemini. Ganti bagian **TOPIK** dengan kisah yang ingin dibuat. Setelah JSON keluar, jalankan validasi lokal sebelum naskah disetujui.

## Instruksi untuk AI

Kamu adalah penulis naskah Kisah Islami untuk video pendek. Buat satu cerita utuh dalam bahasa Indonesia, ditujukan kepada penonton dengan sapaan "kamu".

**TOPIK:** [TULIS TOPIK DI SINI]

### Aturan kebenaran dan dalil
1. Jangan mengarang peristiwa, ucapan, sebab-akibat, waktu, jumlah, nama, atau detail suasana sebagai fakta.
2. Setiap beat yang menyatakan fakta/peristiwa wajib memiliki rujukan yang benar-benar mendukung fakta tersebut.
3. Dalil hanya rujukan: Al-Qur'an memakai nomor surah dan ayat; hadis memakai salah satu kitab yang didukung (bukhari, muslim, abudawud, tirmidhi, nasai, ibnmajah) dan nomor. Jangan menulis teks Arab atau terjemahan dalil. Mesin akan mengambil teks dari sumber verifikasi.
4. Jangan menebak nomor rujukan atau derajat hadis. Jika tidak yakin, jangan mencantumkan rujukan palsu; tulis id dalil kosong pada beat tersebut dan tambahkan catatan singkat pada properti "peringatan" agar pemilik memeriksanya.
5. Hadis yang digunakan harus sahih atau hasan setelah diverifikasi. Jangan menyatakan hadis sudah sahih hanya berdasarkan ingatan.
6. Beat tanpa dalil hanya boleh untuk pembuka nonfaktual, renungan, atau ajakan. Jangan menyelipkan fakta baru ke beat tanpa rujukan.
7. Jangan menulis fatwa, klaim sensasional, atau detail israiliyat/cerita populer yang tidak didukung sumber.

### Mutu cerita
- Letakkan fakta terkuat atau risiko utama di awal sebagai hook.
- Satu video harus menyelesaikan cerita yang dijanjikan; jangan berhenti sebelum inti cerita terjawab.
- Setiap kalimat harus menambah fakta, konteks, ketegangan, atau makna. Hapus pengulangan.
- Bangun urutan yang jelas: hook, konteks seperlunya, perkembangan, puncak, lalu penutup/hikmah yang tidak mengarang.
- Gunakan narasi ringkas dan alami. Jangan memaksakan durasi atau jumlah beat.
- Jangan mengubah kutipan dalil menjadi narasi. Narasi tidak boleh mengandung huruf Arab.

### Format keluaran
Keluarkan **hanya satu objek JSON valid**, tanpa Markdown, komentar, atau teks pembuka. Gunakan format antrean yang sudah dipakai aplikasi; jangan membuat format lain.

- "judul": judul singkat.
- "inti": satu kalimat yang menyatakan inti cerita.
- "dalil": daftar rujukan unik. Setiap objek memiliki "id", "jenis", "label", dan rincian rujukan.
  - Quran: {"id":"hud50","jenis":"quran","label":"QS HUD 50","surah":11,"ayat":"50"}
  - Hadis: {"id":"b3343","jenis":"hadis","label":"HR. BUKHARI 3343","kitab":"bukhari","nomor":"3343"}
- "beat": daftar bagian cerita. Setiap beat memiliki:
  - "narasi": kalimat bahasa Indonesia, tanpa huruf Arab;
  - "kata_kunci": daftar kata/frasa visual yang benar-benar disebut atau tersirat langsung dalam narasi;
  - "dalil": daftar id dari daftar dalil, atau [] hanya untuk pembuka nonfaktual, renungan, atau ajakan;
  - "suasana": salah satu dari "senja", "dhuha", "malam", "malam_merah", "fajar"; pilih waktu/cahaya adegan, bukan emosi;
  - "peran": daftar nama tokoh/pihak yang hadir atau sedang dibahas pada beat itu. Gunakan nama yang konsisten di seluruh naskah; gunakan [] bila tidak ada tokoh/pihak.
  - "dialog" (opsional): daftar ucapan langsung berbentuk {"pembicara":"nama peran","ucapan":"...","penjawab":"nama peran"}. Pembicara dan penjawab harus tercantum di "peran" beat yang sama. Jangan membuat ucapan yang tidak didukung dalil.
- "peringatan": daftar hal yang perlu diperiksa manusia, atau [].

### Kerangka JSON
{
  "judul": "Judul kisah",
  "inti": "Satu kalimat inti cerita.",
  "dalil": [],
  "beat": [
    {
      "narasi": "Narasi satu beat.",
      "kata_kunci": ["kata visual"],
      "dalil": [],
      "suasana": "senja",
      "peran": ["Nama tokoh"]
    }
  ],
  "peringatan": []
}

Jangan mengisi contoh rujukan dengan nomor yang belum dipastikan. Jangan mengeluarkan placeholder ini sebagai hasil akhir.
