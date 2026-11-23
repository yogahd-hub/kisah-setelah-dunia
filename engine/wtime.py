"""Waktu per kata yang akurat dengan faster-whisper (alat yang sama dengan tools/transkrip.py di lab-video).

Whisper mendengar VO dan memberi waktu mulai/selesai tiap kata. Kata hasil dengar lalu dicocokkan
dengan kata naskah (difflib), jadi teks di layar tetap persis naskah, hanya waktunya diambil dari suara.
Kalau faster-whisper tidak terpasang atau gagal, kembalikan None (reel.py memakai perkiraan lama).
"""
import os, re, difflib
LAST_RATIO = 0.0

def _norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())

def listen(wav):
    from faster_whisper import WhisperModel
    name = os.environ.get("WHISPER_MODEL", "small")
    m = WhisperModel(name, device="cpu", compute_type="int8")
    # baca wav sendiri (numpy 16 kHz) -> tidak bergantung pada PyAV yang sering beda versi
    import wave, numpy as np
    w = wave.open(wav); sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if w.getnchannels() > 1: x = x.reshape(-1, w.getnchannels()).mean(1)
    x = np.interp(np.arange(int(len(x) * 16000 / sr)) * sr / 16000, np.arange(len(x)), x).astype(np.float32)
    segs, _ = m.transcribe(x, language="id", word_timestamps=True, vad_filter=False, beam_size=5)
    out = []
    for s in segs:
        for w in (s.words or []):
            n = _norm(w.word)
            if n: out.append((n, float(w.start), float(w.end)))
    return out

def align(scene_texts, wav):
    """Per adegan: [(kata_naskah, mulai, selesai)], waktu absolut di wav. None bila gagal."""
    try:
        heard = listen(wav)
    except Exception as e:
        print(f"[whisper] dilewati: {e}", flush=True); return None
    if len(heard) < 3: return None
    script = [(si, w) for si, t in enumerate(scene_texts) for w in t.split()]
    a = [_norm(w) for _, w in script]; b = [h[0] for h in heard]
    st = [None] * len(a); en = [None] * len(a)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                st[i1 + k], en[i1 + k] = heard[j1 + k][1], heard[j1 + k][2]
        elif op == "replace" and j2 > j1:
            # kata dieja beda (mis. angka/serapan): bagi rata rentang waktu yang terdengar
            t0, t1 = heard[j1][1], heard[j2 - 1][2]; n = i2 - i1
            for k in range(n):
                st[i1 + k] = t0 + (t1 - t0) * k / n; en[i1 + k] = t0 + (t1 - t0) * (k + 1) / n
    matched = sum(1 for x in st if x is not None)
    print(f"[whisper] {len(heard)} kata terdengar, {matched}/{len(a)} kata naskah dapat waktu", flush=True)
    global LAST_RATIO; LAST_RATIO = matched / max(1, len(a))
    if matched < 0.6 * len(a): return None
    # isi yang kosong dengan interpolasi di antara tetangga
    idx = [k for k, x in enumerate(st) if x is not None]
    for k in range(len(a)):
        if st[k] is not None: continue
        p = max([j for j in idx if j < k], default=None); q = min([j for j in idx if j > k], default=None)
        if p is None: st[k] = max(0.0, st[q] - 0.3 * (q - k)); en[k] = st[k] + 0.25
        elif q is None: st[k] = en[p] + 0.3 * (k - p - 1); en[k] = st[k] + 0.25
        else:
            f = (k - p) / (q - p); st[k] = en[p] + (st[q] - en[p]) * f; en[k] = st[k] + 0.2
    # jaga urutan naik
    for k in range(1, len(a)):
        if st[k] < st[k - 1]: st[k] = st[k - 1] + 0.01
        if en[k] < st[k]: en[k] = st[k] + 0.05
    out = [[] for _ in scene_texts]
    for k, (si, w) in enumerate(script): out[si].append((w, round(st[k], 3), round(en[k], 3)))
    return out
