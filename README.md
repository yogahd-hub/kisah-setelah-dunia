# Kisah Setelah Dunia — mesin video otomatis

Naskah JSON masuk → video jadi. Voice over pakai Gemini TTS (gratis), render pakai GitHub Actions (gratis). Kuota Claude hanya dipakai untuk menulis naskah.

## Setup sekali
1. **Settings → Secrets and variables → Actions → New repository secret**
   Nama: `GEMINI_API_KEY` · Isi: API key dari aistudio.google.com.
2. Selesai. Workflow ada di `.github/workflows/render.yml`.

## Membuat video
1. Tambah file naskah di `scripts/` (lihat `PANDUAN_NASKAH.md`). Bisa lewat web GitHub: **Add file → Create new file**, nama `scripts/s1-ep02.json`, tempel isinya, **Commit**.
2. Buka tab **Actions** → run "Render video" yang sedang berjalan (±3–5 menit per video).
3. Setelah hijau ✅, klik run-nya → bagian **Artifacts** → unduh `video-…`. Isinya per episode:
   - `<nama>.mp4` — video siap upload
   - `cover.jpg` — cover/thumbnail
   - `caption.txt` — caption + hashtag
4. Render ulang: tab **Actions → Render video → Run workflow**, isi nama file naskah.

Video tersimpan 30 hari di Artifacts. File `done/<nama>.txt` menandai naskah yang sudah dirender.

## Isi repo
| Path | Isi |
|---|---|
| `engine/reel.py` | Perintah utama: VO, sinkron teks, render, audio, cover, caption |
| `engine/base.py` | Latar, teks, kartu dalil, header, ilustrasi dasar |
| `engine/align.py` | Menyamakan kata dengan jeda suara |
| `engine/gemini.py` | TTS dan transkripsi Gemini |
| `scripts/` | Naskah per episode |
| `fonts/` | Poppins + Amiri (lisensi SIL OFL) |
| `PANDUAN_NASKAH.md` | Format naskah, daftar ilustrasi, aturan isi |
| `SERI.md` | Rencana seri dan episode |

## Jalankan lokal (opsional)
```bash
pip install -r requirements.txt   # butuh ffmpeg dan libraqm
export GEMINI_API_KEY=...
python engine/reel.py scripts/s1-ep01.json            # hasil di out/s1-ep01/
python engine/reel.py scripts/s1-ep01.json --preview  # contact sheet saja
```
