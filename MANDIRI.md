# Panduan Mandiri — tetap produksi tanpa langganan Claude

Repo ini sengaja dibuat supaya **tidak bergantung pada Claude**. Claude hanya mempercepat penulisan naskah.
Semua bagian lain berjalan sendiri di GitHub.

| Bagian | Siapa yang mengerjakan | Butuh Claude? |
|---|---|---|
| Menulis naskah | Claude **atau** Gemini/ChatGPT gratis (pakai `PROMPT_AI.md`) **atau** kamu sendiri (`TEMPLATE_NASKAH.json`) | Tidak wajib |
| Suara (VO) | Gemini API otomatis, **atau** rekaman sendiri dari Google AI Studio (`suara/`) | Tidak |
| Sinkron teks | faster-whisper di GitHub Actions | Tidak |
| Render video anime | GitHub Actions + HyperFrames + three.js | Tidak |
| Cover + caption | Otomatis | Tidak |

## Alur kerja tanpa Claude (5 langkah)
1. Salin seluruh **`CHECKPOINT.md`**, tempel ke chat baru di **gemini.google.com**, **ChatGPT**, atau Claude akun lain.
   Di bawahnya tulis permintaan (mis. "Buat naskah S1 part 7") dan tempel materi berita/jurnal kalau ada.
2. Salin JSON hasilnya. Di GitHub: folder `scripts` → **Add file → Create new file** → nama mis. `s1-ep07.json` → tempel → **Commit changes**.
3. Tab **Actions** → tunggu run "Render video" hijau (±10 menit). Kalau merah, buka run-nya: pesan berbahasa Indonesia menunjukkan bagian naskah yang salah. Perbaiki file lalu commit lagi.
4. Buka tab **Releases** (kanan halaman repo) → unduh MP4, cover, caption langsung. Cadangan: run → **Artifacts** (zip, 30 hari).
5. **Cek dalil** (arti + nomor ayat/hadits) ke quran.com / sunnah.com sebelum diunggah.

## Risiko & opsi gratis
| Risiko | Opsi gratis 1 (sudah terpasang) | Opsi gratis 2 |
|---|---|---|
| Jatah menit GitHub | Repo **public** → render tanpa batas menit (runner standar) | Render di laptop sendiri: `python engine/reel.py scripts/x.json` |
| Gemini TTS gratis dikurangi/dihentikan (sekarang ±10 suara/hari per model) | **Suara manual**: rekam/unduh dari Google AI Studio atau rekam suara sendiri di HP → `suara/<nama>.wav` | **Edge TTS** (suara Ardi/Gadis, tanpa API key): tambahkan `"tts": "edge"` di naskah. Layanan tidak resmi Microsoft, bisa berhenti sewaktu-waktu; cek aturan monetisasi sebelum dipakai rutin |
| Gemini API key hilang | Render tetap jalan dengan suara manual / Edge TTS | Buat key baru gratis di aistudio.google.com |
| Tidak ada Claude untuk menulis naskah | `CHECKPOINT.md` → tempel ke Gemini / ChatGPT gratis | `TEMPLATE_NASKAH.json` diisi manual |
| AI gratis salah menyebut dalil/sumber | Cek manual ke quran.com / sunnah.com (wajib) | Pakai kartu hanya dari daftar dalil yang sudah pernah dicek di naskah lama |
| Alat render berubah versi | HyperFrames dikunci `0.9.85`, three.js & GSAP disimpan di `engine/vendor/` | Gaya lama tanpa browser: `"engine": "vektor"` di naskah |
| Model whisper tidak bisa diunduh | Otomatis pindah ke perkiraan waktu kata (cara lama) | — |
| Video hilang setelah 30 hari | **Releases** (permanen, unduh langsung tanpa zip) | Simpan ke Google Drive/HP setelah unduh |

Catatan: suara rekaman sendiri adalah pilihan paling aman untuk monetisasi jangka panjang (orisinal, tidak bergantung layanan mana pun).

## Yang perlu dijaga
- Secret `GEMINI_API_KEY` (opsional sejak ada suara manual/Edge). Ganti di Settings → Secrets and variables → Actions kalau key baru.
- Untuk cadangan otomatis Edge TTS saat Gemini habis: Settings → Secrets and variables → Actions → tab **Variables** → `TTS_CADANGAN` = `edge`.
- Jangan pernah menulis API key di file naskah atau file lain di repo (repo ini public).
- Perbarui "Status seri" di `CHECKPOINT.md` dan `SERI.md` setiap selesai batch.

## Kalau suatu hari ada yang rusak
1. Buka run merah di tab Actions → baca baris `::error::` atau baris terakhir log.
2. Tempel pesan error itu + isi file yang bermasalah ke Gemini/ChatGPT/Claude, minta perbaikan.
3. Render ulang: Actions → Render video → **Run workflow** → isi `scripts/nama.json`.

## Checkpoint terakhir dari Claude
- Mesin: gaya anime default, 23 adegan (lihat `PANDUAN_NASKAH.md`), VO utuh + whisper, suara manual opsional.
- Naskah selesai: lihat folder `scripts/` dan `done/`.
- Instruksi lengkap untuk Claude ada di `skill/naskah-kisah-setelah-dunia/SKILL.md`. File itu juga bisa ditempel ke AI lain sebagai "aturan kerja".
