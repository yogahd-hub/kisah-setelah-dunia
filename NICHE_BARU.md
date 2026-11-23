# Membuat akun/niche baru dari mesin ini

Mesin video ini bisa dipakai untuk niche apa pun (sejarah, kesehatan ringan, psikologi, motivasi, dll.).
Yang diganti hanya **isi**, mesinnya sama.

## Sekali di awal (repo ini)
Settings → General → centang **Template repository**. (Cukup sekali.)

## Setiap niche baru
1. Di halaman repo ini klik **Use this template → Create a new repository**. Nama mis. `sejarah-nusantara`, pilih **Public** (render gratis tanpa batas).
2. Di repo baru, hapus isi folder `scripts/` dan `done/` (biarkan foldernya; boleh sisakan satu contoh naskah untuk referensi lalu hapus belakangan).
3. Edit **`NICHE.md`**: nama akun, tema, penonton, nada, suara, **sumber wajib untuk kartu**, label kartu, larangan, tokoh, hashtag.
4. Edit **`SERI.md`**: rencana seri dan part.
5. Edit **`CHECKPOINT.md`** bagian *Proyek saat ini* dan *Aturan niche* (salin dari NICHE.md versi singkat). Bagian format & adegan biarkan.
6. Settings → Secrets and variables → Actions → **New repository secret** `GEMINI_API_KEY` (opsional; tanpa key pakai suara manual atau `"tts": "edge"`).
7. Buat naskah pertama: tempel `CHECKPOINT.md` ke Claude/ChatGPT/Gemini → minta "Buat naskah part 1" → commit ke `scripts/`.

## Batasan yang perlu diketahui
- Adegan 3D yang tersedia bertema umum + akhirat (lihat daftar `il`). Untuk niche lain pilih yang paling cocok (`city`, `globe`, `clock`, `door`, `calendar`, `hourglass`, `duo`, `solo`, `night`, `choice` netral dipakai di mana saja).
- Adegan baru (mis. candi, rumah sakit) perlu ditambah di `engine/anime_template.html` — minta bantuan AI dengan menyebut file itu dan contoh adegan `mosque`.
- Tokoh selalu dua orang (A dan B); nama dan warna bebas diganti lewat `chars`.
