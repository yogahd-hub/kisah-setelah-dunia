# Panduan Produksi Naskah — Claude, ChatGPT, Gemini

Tujuan: naskah tetap bisa dibuat setiap minggu, apa pun AI yang tersedia. Render tetap otomatis di GitHub.

## Pilihan A — Claude yang terhubung ke GitHub (paling praktis)
Claude menulis, mengecek, dan **langsung push** ke repo.
1. Buka percakapan baru Claude (fitur kode/GitHub harus tersedia di paket akunmu).
2. Pastikan repo `yogahd-hub/kisah-setelah-dunia` sudah terhubung/diizinkan.
3. Pasang skill `naskah-kisah-setelah-dunia` (salinannya ada di `skill/naskah-kisah-setelah-dunia/SKILL.md`).
4. Kirim isi kotak di `MASTER_PROMPT.md`, ganti bagian "TUGAS SEKARANG" sesuai batch.
5. Claude push → tunggu render di tab **Actions** → unduh di **Releases**.

Catatan: anggota tim lain boleh memakai akun Claude **milik mereka sendiri**. Undang akun GitHub mereka sebagai collaborator (Settings → Collaborators). Jangan berbagi login.

## Pilihan B — ChatGPT (kalau Claude tidak tersedia)
ChatGPT menulis JSON; **kamu yang menempel ke GitHub** (±2 menit per naskah).

### Sekali di awal (supaya tidak perlu tempel checkpoint setiap kali)
1. Di ChatGPT buat **Project** baru, nama: `Kisah Setelah Dunia`.
2. Unggah file `CHECKPOINT.md` terbaru (unduh dari repo: buka file → tombol **Download raw file**).
3. Di **Instructions** project, tempel:
   ```
   Ikuti CHECKPOINT.md. Keluarkan hanya JSON naskah di code block (satu code block per naskah),
   lalu tabel singkat: no | judul | dalil (sumber + arti). Jangan menambah field baru.
   Kalau tidak yakin nomor ayat/hadits, jangan buat kartu.
   ```
   (Tanpa fitur Project: tempel saja seluruh isi `CHECKPOINT.md` di awal chat baru.)

### Setiap batch
1. Chat di project itu: `Buat naskah Seri 1 part 7 dan Seri 2 part 5. no mulai 11.` + tempel materi berita/jurnal kalau ada.
2. Klik **Copy** di code block JSON pertama.
3. GitHub → repo → folder `scripts` → **Add file → Create new file**.
4. Nama file: `s1-ep07.json` (pola: `s<seri>-ep<part dua digit>.json`). Tempel → **Commit changes**.
5. Ulangi untuk naskah lain. Render otomatis berjalan per commit.
6. Tab **Actions**:
   - Hijau ✅ → unduh di **Releases**.
   - Merah ❌ → buka run → salin baris `::error::` → tempel ke ChatGPT: "Perbaiki JSON ini, errornya: ..." → edit file di GitHub (ikon pensil) → tempel versi baru → Commit.
7. **Cek dalil** tiap kartu ke quran.com / sunnah.com sebelum upload (AI gratis lebih sering salah nomor).
8. Selesai batch: edit `CHECKPOINT.md` di GitHub (ikon pensil) → perbarui baris **Status seri** dan `no` terakhir → Commit → unggah ulang ke Project ChatGPT.

## Pilihan C — Gemini
Sama dengan Pilihan B. Di Gemini buat **Gem** (gemini.google.com → Gems → New Gem), tempel isi `CHECKPOINT.md` + instruksi di atas sebagai instruksi Gem.

## Urutan yang disarankan
| Kondisi | Pakai |
|---|---|
| Langganan Claude aktif | Pilihan A (batch 5–7 naskah seminggu sekali) |
| Tidak berlangganan | Pilihan B (ChatGPT) atau C (Gemini), gratis |
| Ragu dengan dalil dari AI gratis | Pakai hanya dalil yang sudah pernah dicek di naskah lama, atau tanpa kartu |

## Kesalahan umum JSON dari AI lain
- Angka ditulis digit di `text` ("3 hari") → harus huruf ("tiga hari").
- `hl` berisi kata yang tidak ada di `text`.
- `il` tidak ada di daftar (mis. "hospital") → ganti dengan adegan yang ada.
- Tanda kutip miring (“ ”) di luar teks → JSON rusak. Minta AI "pakai tanda kutip lurus".
- Scene terakhir bukan `il: "cta"`.
`engine/check.py` di GitHub Actions akan menyebutkan kesalahan ini dalam bahasa Indonesia.
