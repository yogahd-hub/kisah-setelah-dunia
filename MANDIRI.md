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
1. Buka `PROMPT_AI.md`, salin prompt di kotak, tempel ke **gemini.google.com** atau **ChatGPT**.
   Isi bagian *PERMINTAAN SAYA* (seri, part, nomor tayang, topik) dan *Materi sumber* kalau ada berita/jurnal.
2. Salin JSON hasilnya. Di GitHub: folder `scripts` → **Add file → Create new file** → nama mis. `s1-ep07.json` → tempel → **Commit changes**.
3. Tab **Actions** → tunggu run "Render video" hijau (±10 menit). Kalau merah, buka run-nya: pesan berbahasa Indonesia menunjukkan bagian naskah yang salah. Perbaiki file lalu commit lagi.
4. Klik run → **Artifacts** → unduh. Isi: video MP4, `cover.jpg`, `caption.txt`.
5. **Cek dalil** (arti + nomor ayat/hadits) ke quran.com / sunnah.com sebelum diunggah.

## Yang perlu dijaga supaya jalan bertahun-tahun
- **Secret `GEMINI_API_KEY`** di Settings → Secrets and variables → Actions. Kalau suatu saat key dihapus/kedaluwarsa, buat baru di aistudio.google.com dan ganti isinya.
- **Kalau Gemini TTS gratis berhenti/berubah**: pakai suara manual (`suara/README.md`). Render tetap jalan.
- **Jatah GitHub**: 2.000 menit/bulan (repo privat). Cek di Settings → Billing and licensing → Usage. Kalau kurang, ubah repo jadi public (render tanpa batas menit).
- **Versi alat dikunci**: HyperFrames `0.9.85` (di `engine/anime.py`), three.js `0.158.0` dan GSAP `3.12.5` disimpan di `engine/vendor/`. Jangan diubah kecuali sengaja upgrade.
- **Artifacts hilang setelah 30 hari** → selalu unduh video setelah render.
- Catat part yang sudah dibuat di `SERI.md` (kolom status) supaya AI mana pun tahu lanjutannya.

## Kalau suatu hari ada yang rusak
1. Buka run merah di tab Actions → baca baris `::error::` atau baris terakhir log.
2. Tempel pesan error itu + isi file yang bermasalah ke Gemini/ChatGPT/Claude, minta perbaikan.
3. Render ulang: Actions → Render video → **Run workflow** → isi `scripts/nama.json`.

## Checkpoint terakhir dari Claude
- Mesin: gaya anime default, 23 adegan (lihat `PANDUAN_NASKAH.md`), VO utuh + whisper, suara manual opsional.
- Naskah selesai: lihat folder `scripts/` dan `done/`.
- Instruksi lengkap untuk Claude ada di `skill/naskah-kisah-setelah-dunia/SKILL.md`. File itu juga bisa ditempel ke AI lain sebagai "aturan kerja".
