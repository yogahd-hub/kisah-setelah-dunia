---
name: naskah-video-animasi
description: Menulis naskah video animasi pendek (Reels/TikTok/Shorts) untuk niche apa pun di mesin video GitHub (template kisah-setelah-dunia), dari topik atau materi user, cek sumber, validasi, push, dan perbarui checkpoint.
---

# Naskah Video Animasi (semua niche)

Mesin: repo GitHub yang dibuat dari template `yogahd-hub/kisah-setelah-dunia`. Naskah JSON di `scripts/` → GitHub Actions membuat suara, sinkron teks, video anime 3D, cover, caption → hasil di **Releases**.
Bahasa ke user: Indonesia sederhana, satu langkah per perintah. Jangan memanggil user "Mas".

## 0. Tentukan repo + niche
- Tanyakan/temukan repo niche yang dimaksud (mis. `yogahd-hub/kisah-setelah-dunia`). Clone atau minta akses.
- **Niche baru?** Ikuti `NICHE_BARU.md` di repo template: buat repo dari template, isi `NICHE.md`, `SERI.md`, `CHECKPOINT.md`, kosongkan `scripts/` dan `done/`.

## 1. Baca konteks (urut, hemat token)
1. `CHECKPOINT.md` — ringkasan proyek, status seri, format, daftar adegan. Sering cukup ini saja.
2. `NICHE.md` — nada, sumber wajib untuk kartu, larangan, tokoh, hashtag.
3. `PANDUAN_NASKAH.md` hanya kalau perlu detail field. `SERI.md` untuk rencana part.
4. `ls scripts/` → part terakhir dan `no` terbesar.

## 2. Olah materi user (opsional)
- File dibaca, link dibuka (WebFetch). Ambil fakta untuk cerita/hook; catat sumber + tahun untuk caption.
- Materi bukan pengganti "sumber wajib" di `NICHE.md`. Materi meragukan/hoaks → beri tahu user, jangan dipakai.

## 3. Sumber untuk kartu (`card`)
- Ikuti "Sumber wajib" di `NICHE.md` (mis. Al-Qur'an/hadits, jurnal, buku sejarah, WHO).
- Cek di web bila bisa. Tidak yakin → jangan buat kartu.
- `card` = `[isi ringkas ≤25 kata, sumber, LABEL]`; LABEL sesuai `NICHE.md`.

## 4. Tulis naskah
- File `scripts/<kode-seri>-ep<NN>.json`. Field: `no`, `series`, `part`, `title`, `hook`, `cover_scene`, `voice`, `chars`, `scenes`, `caption`, `cta`, `hashtags`.
- 7–10 scene, 90–130 kata. Hook dramatis → cerita tokoh → kartu sumber → refleksi "kamu" → scene terakhir `il: "cta"` + teaser.
- Angka ditulis huruf di `text`; tiap `text` diakhiri `.`/`?`; `hl` 1–3 kata persis dari `text`; `kw` kapital ≤18 huruf.
- Pakai hanya `il` yang ada di daftar `CHECKPOINT.md`/`PANDUAN_NASKAH.md`. Variasikan adegan & ekspresi antar video.
- Opsi suara: default Gemini (`voice`); `"tts": "edge"` untuk Edge TTS gratis; atau user upload `suara/<nama>.wav`.

## 5. Validasi
`python engine/check.py scripts/<file>.json` → harus 0 error.

## 6. Commit + push
Batch beberapa naskah per commit. Push memicu render (±10–13 menit/video, gratis tanpa batas di repo public).

## 7. Laporan + checkpoint (wajib)
- Ke user: daftar file, judul, dan sumber/dalil tiap kartu untuk dicek sebelum upload.
- Perbarui **"Status seri"** + `no` terakhir di `CHECKPOINT.md`, dan kolom Status di `SERI.md`. Commit.
- Aturan baru dari user → tulis ke `NICHE.md` (khusus niche) atau `CHECKPOINT.md` (umum), supaya chat baru/AI lain langsung tahu.
- Tawarkan user menyalin `CHECKPOINT.md` terbaru untuk chat berikutnya (Claude akun lain, ChatGPT, atau Gemini).
