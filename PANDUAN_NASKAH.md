# Panduan Naskah — Kisah Setelah Dunia

Setiap video = satu file JSON di folder `scripts/`. **Gaya default: anime 3D** (HyperFrames + three.js). Tambahkan `"engine": "vektor"` hanya kalau ingin gaya gambar datar lama. Begitu file di-push, GitHub Actions otomatis membuat voice over, merender video, lalu menyimpan hasilnya (MP4 + cover.jpg + caption.txt) di tab **Actions → run terbaru → Artifacts**.

## Penamaan file
`scripts/<seri>-ep<nomor>.json`, contoh `s1-ep02.json` (seri 1, part 2), `s2-ep01.json` (seri 2, part 1).

## Format
```json
{
  "no": 7,
  "series": "Setelah Napas Terakhir",
  "part": 2,
  "title": "Baris Pertama|Baris Kedua",
  "hook": "Kalimat penasaran untuk cover",
  "cover_scene": 1,
  "voice": "Charon",
  "chars": {
    "A": {"name": "ARYA", "hair": [40, 28, 22], "shirt": [176, 92, 64]},
    "B": {"name": "BIMA", "hair": [30, 26, 30], "shirt": [64, 110, 100]}
  },
  "scenes": [
    {"il": "duo", "text": "Narasi scene ini.", "hl": ["kata", "kunci"], "kw": "KATA BESAR"},
    {"il": "candle", "text": "Narasi.", "hl": ["kata"], "card": ["Arti ayat dalam bahasa Indonesia.", "QS. Nama: ayat"]},
    {"il": "cta", "text": "Part tiga besok. Tulis lanjut di komentar.", "hl": ["lanjut"], "kw": "PART 3", "kw2": "JUDUL PART 3"}
  ],
  "caption": "Caption untuk diunggah.",
  "cta": "Kalimat ajakan di caption.",
  "hashtags": ["#kisahsetelahdunia", "#..."]
}
```

| Field | Arti |
|---|---|
| `no` | Nomor urut tayang (jadi awalan nama file: `01 - S1P1 Judul.mp4`). |
| `title` | Judul di cover. `|` = pindah baris. Maks ±14 huruf per baris. |
| `hook` | Kalimat penasaran besar di bagian bawah cover (maks ±40 huruf). Cover juga tampil 0,7 detik di awal video. |
| `cover_scene` | Nomor scene (mulai 0) yang ilustrasinya dipakai di cover. |
| `chars` | Tokoh A dan B (nama, warna rambut, warna baju RGB). Ganti nama tokoh tiap seri. |
| `text` | Narasi yang dibacakan. Akhiri dengan `.` atau `?`. **Angka ditulis dengan huruf** ("dua puluh tiga") supaya teks layar = ucapan. |
| `hl` | Kata yang dikuningkan di teks layar (huruf besar/kecil bebas). |
| `kw` / `kw2` | Kata kunci besar kuning di atas teks (opsional). Maks ±18 huruf. |
| `card` | Kartu dalil: `[arti dalam bahasa Indonesia, sumber]` atau `[arti, sumber, label]`. Label default `AL-QUR'AN`; untuk hadits isi `"HADITS"`. Pakai **arti/potongan arti**, bukan teks Arab (teks Arab tidak dibacakan dan sulit dicek). Maks ±4 baris. |
| `il` | Ilustrasi scene (daftar di bawah). |
| `tts_model` | (opsional) paksa model TTS tertentu. |
| `engine` | (opsional) `anime` (default) atau `vektor`. |
| `env` | (opsional, il `solo`) `night` = di kamar malam; tanpa ini = ruang gelap. |
| `style` | **Jangan diisi.** Model TTS kadang ikut membacakan instruksi gaya. Mesin juga mengecek 7 detik pertama suara dan mengulang otomatis kalau ada ucapan tambahan. |

## Ilustrasi (`il`)
| Nama | Isi | Opsi tambahan |
|---|---|---|
| `duo` | Tokoh A dan B berdampingan | `expr` |
| `solo` | Satu tokoh | `who` (A/B), `expr`, `expr2`, `switch` (0–1) |
| `dreams` | Tokoh + ikon rencana dunia yang hilang | `who`, `seed`, `switch` |
| `night` | Tokoh merenung malam, bulan sabit, bubble | `who`, `expr`, `bubble` |
| `choice` | Sorotan bergantian A dan B | |
| `angel` | Sosok bercahaya bersayap (tanpa wajah) | |
| `grave` | Makam, nisan, hujan | `who` (tokoh menangis di samping makam), `expr` |
| `crowd` | Kerumunan siluet di padang luas | `move` (true/false) |
| `scale` | Timbangan amal | |
| `sun` | Matahari sangat dekat | |
| `gate` | Gerbang bercahaya | `dark` (true = gerbang gelap) |
| `wall` | Tembok besar yang retak | |
| `eye` | Satu mata besar yang mengintai | |
| `city` | Gedung-gedung tumbuh makin tinggi | |
| `sunwest` | Matahari terbit dari barat, tokoh kaget | `who` |
| `clock` | Jam berputar lalu berhenti | |
| `hourglass` | Jam pasir | |
| `calendar` | Kalender dengan tanda tanya | |
| `globe` | Bola dunia + pin | |
| `door` | Pintu bercahaya, figur berjalan | |
| `candle` | Lilin meleleh | |
| `mosque` | Masjid dan bulan sabit | |
| `cta` | Bubble komentar (scene terakhir) | |

Ekspresi (`expr`): `neutral`, `smile`, `worry`, `shock`, `cry`.

## Aturan isi (wajib)
Aturan khusus niche (sumber yang wajib, nada, larangan, tokoh) ada di **`NICHE.md`**. Aturan umum untuk semua niche:
1. **Klaim penting harus punya sumber jelas** sesuai `NICHE.md`. Kalau ragu, jangan pakai kartu.
2. **Misteri boleh di cara bercerita, bukan di klaim.** Tidak boleh teori konspirasi/ramalan sebagai fakta.
3. **Tiap video harus terasa beda** (aturan "konten berulang" YouTube/Facebook): cerita baru, tokoh/ekspresi/ilustrasi bervariasi, hook berbeda.
4. **Jangan meniru** judul/urutan akun lain.
5. Struktur: hook dramatis (scene 1–2) → cerita tokoh → kartu sumber → refleksi "kamu" → teaser part berikutnya + ajakan komen.
6. Panjang ideal 7–10 scene, total narasi 55–90 detik.

## Materi sumber (jurnal, berita, artikel)
Materi luar boleh dipakai sebagai **bahan cerita/hook** (mis. berita tentang banyaknya kematian mendadak, riset tentang rasa waktu makin cepat). Aturannya:
- Fakta dari materi ditulis sebagai fakta umum tanpa melebih-lebihkan, dan sumbernya dicatat di `caption`.
- **Dalil tetap hanya dari Al-Qur'an / hadits shahih-hasan**, bukan dari berita.
- Jangan menghubungkan berita dengan klaim "ini pasti tanda kiamat". Cukup ajak merenung.

## Suara manual (opsional)
Taruh `suara/<nama-naskah>.wav` (atau .mp3) untuk memakai suara buatan sendiri, mis. dari Google AI Studio. Lihat `suara/README.md`.

## Ukuran video
Semua hasil (MP4 dan cover) wajib **9:16, 1080x1920**. Workflow memeriksa ini otomatis; kalau ukurannya salah, run merah dan video tidak dirilis.

## Kuota
- Gemini TTS gratis: 10 suara/hari per model, otomatis pindah ke model berikutnya kalau habis (±40 video/hari).
- GitHub Actions (repo privat): 2.000 menit/bulan gratis. Satu video anime ±10 menit → ±200 video/bulan.
- Cek pemakaian: foto profil → Settings → Billing and licensing → Usage.
