# Catatan untuk Claude

Repo ini mesin video akun **Kisah Setelah Dunia** (animasi alam akhirat & akhir zaman). Tugas Claude di sini biasanya hanya **menulis naskah** baru di `scripts/` — render dan voice over berjalan otomatis di GitHub Actions, jadi jangan render ulang di sesi Claude kecuali diminta.

- Format naskah, daftar ilustrasi, dan aturan isi: `PANDUAN_NASKAH.md` (wajib diikuti, terutama aturan dalil).
- Rencana seri dan episode berikutnya: `SERI.md`. Cek `scripts/` untuk part terakhir yang sudah ada.
- Validasi cepat sebelum commit: `python -c "import json,sys; [json.load(open(f)) for f in sys.argv[1:]]" scripts/*.json` dan pastikan setiap `il` ada di daftar ilustrasi.
- Tulis beberapa naskah sekaligus dalam satu sesi (batch mingguan) untuk menghemat kuota.
- Teks Arab di kartu harus disebut ke user untuk dicek ke mushaf sebelum diunggah.
