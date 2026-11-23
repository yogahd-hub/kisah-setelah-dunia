# Suara manual (opsional)

Kalau ingin membuat suara sendiri (misalnya di Google AI Studio), taruh filenya di folder ini
dengan nama **sama persis** dengan nama naskah:

| Naskah | Nama file suara |
|---|---|
| `scripts/s1-ep07.json` | `suara/s1-ep07.wav` (boleh .mp3 / .m4a / .ogg) |

Aturan:
1. Yang dibacakan harus **sama persis** dengan gabungan `text` semua adegan di naskah, berurutan, tanpa tambahan.
2. Satu file untuk satu video (semua adegan dalam satu rekaman).
3. Upload lewat GitHub: buka folder `suara` → **Add file → Upload files** → Commit.
   Render otomatis berjalan. Kalau file suara ada, mesin **tidak** membuat suara Gemini.
4. Waktu teks di layar diambil dari suara ini (whisper), jadi jeda bebas, asal kata-katanya sama.
