---
name: naskah-kisah-setelah-dunia
description: Menulis naskah video anime akun Kisah Setelah Dunia (akhirat/akhir zaman) dari topik atau materi user (jurnal, berita, link, catatan), cek dalil, validasi, lalu push ke GitHub supaya dirender otomatis.
---

# Naskah Kisah Setelah Dunia

Repo: `yogahd-hub/kisah-setelah-dunia`. Render, suara, dan sinkron teks berjalan otomatis di GitHub Actions setelah file naskah di-push. Tugas di sini: **menulis naskah JSON yang benar**, bukan merender.
Bahasa ke user: Indonesia sederhana. Jangan memanggil user "Mas".

## 1. Siapkan konteks
1. Pastikan repo tersedia (clone `yogahd-hub/kisah-setelah-dunia`; minta akses repo kalau belum).
2. Baca `PANDUAN_NASKAH.md` (format, daftar `il`, aturan isi) dan `SERI.md` (rencana part).
3. Lihat `scripts/`: cari part terakhir tiap seri dan `no` (nomor tayang) terbesar. Naskah baru melanjutkan dari situ.

## 2. Olah materi dari user (kalau ada)
- File (PDF/docx/gambar): baca isinya. Link: buka dengan WebFetch. Topik saja: cukup pakai SERI.md.
- Ambil dari materi hanya **fakta untuk cerita/hook** (angka, kejadian, temuan riset). Catat nama sumber + tahun untuk caption.
- Materi berita/jurnal **bukan dalil**. Jangan menulis "ini pasti tanda kiamat"; cukup ajak merenung.
- Kalau materi meragukan (hoaks, konspirasi, tidak ada sumber), katakan ke user dan jangan dipakai.

## 3. Cari dan cek dalil
- Hanya Al-Qur'an atau hadits shahih/hasan dengan sumber jelas (perawi + nomor).
- Kalau web tersedia, cek nomor ayat (mis. quran.com) dan hadits (mis. sunnah.com) sebelum dipakai. Kalau tidak bisa memastikan, **jangan pakai kartu**; cukup narasi umum tanpa nomor.
- Kartu (`card`) berisi **arti bahasa Indonesia**, bukan teks Arab, maks ±25 kata.

## 4. Tulis naskah
Ikuti format `PANDUAN_NASKAH.md`. Ringkasnya:
- Nama file `scripts/s<seri>-ep<part dua digit>.json`. Field wajib: `no`, `series`, `part`, `title`, `hook`, `cover_scene`, `voice: "Charon"`, `chars`, `scenes`, `caption`, `cta`, `hashtags`.
- Gaya anime = default (tidak perlu field `engine`).
- 7–10 scene, 90–130 kata narasi. Struktur: hook dramatis → cerita tokoh → dalil → refleksi "kamu" → scene terakhir `il: "cta"` dengan teaser part berikutnya + "Tulis lanjut di komentar".
- Angka di `text` ditulis huruf. Setiap `text` diakhiri `.` atau `?`. Tanpa instruksi gaya suara.
- `hl` = 1–3 kata yang persis ada di `text`. `kw` maks 18 huruf kapital.
- Variasikan `il` dan ekspresi antar video (aturan konten berulang YouTube/Facebook).
- Tokoh: Seri 1 ARYA & BIMA, Seri 2 RAKA & ILHAM (warna di naskah lama).
- Kalau materi dipakai, tulis sumbernya di akhir `caption`.

## 5. Validasi
```bash
python engine/check.py scripts/<file>.json
```
Harus `0 error`. Perbaiki peringatan yang masuk akal.
Opsional, pratinjau gambar 3D tanpa render penuh (butuh Chrome + playwright):
```bash
ANIME_NO_RENDER=1 python engine/reel.py scripts/<file>.json --no-check
python engine/preview_anime.py work/<nama>/hf 1
```

## 6. Commit + push (memicu render)
- Satu commit boleh berisi beberapa naskah (batch mingguan = hemat kuota).
- Pesan commit jelas, mis. `Naskah minggu 3: S1 ep07-08, S2 ep05`.
- Push. Render otomatis ±10 menit per video; hasil di tab Actions → run → Artifacts.

## 7. Laporan ke user + checkpoint
- Sebutkan file yang dibuat, judul, dan **daftar dalil** (sumber + arti) untuk dicek user ke mushaf/kitab sebelum upload.
- Perbarui `SERI.md` (tandai part yang sudah ditulis, tambah rencana baru kalau ada) supaya AI lain atau user bisa melanjutkan tanpa Claude.
- Kalau ada aturan baru dari user, tulis ke `PANDUAN_NASKAH.md` dan `PROMPT_AI.md` juga, jadi alur tanpa Claude (`MANDIRI.md`) tetap sama kualitasnya.
