"""Kisah Setelah Dunia — reel builder.

Satu perintah: naskah JSON -> MP4 vertikal 1080x1920 dengan voice over Gemini, teks sinkron suara,
kartu dalil, ilustrasi animasi, musik ambient, plus cover.jpg dan caption.txt.

    python engine/reel.py scripts/ep001.json            # hasil di out/ep001/
    python engine/reel.py scripts/ep001.json --preview  # hanya contact sheet frame (tanpa render penuh)
"""
import sys, os, json, math, re, wave, subprocess, time, argparse
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base as R
import align as A
import gemini as G
from base import W, H, FPS, CX, CY, BG, STARS, YEL, WHITE, GOLD, ease, ease_back, paste_c, font, F_BOLD

LEAD, TAIL = 0.35, 0.45
TTS_MODELS = ["gemini-3.8-flash-lite-tts", "gemini-3.8-flash-tts", "gemini-3.1-flash-tts-preview", "gemini-2.5-pro-preview-tts"]
DEFAULT_STYLE = "[tenang, dalam, sedikit misterius, tempo sedang, jeda jelas antar kalimat]"

# ============================== VOICE OVER ==============================
def make_vo(S, work):
    os.makedirs(f"{work}/vo", exist_ok=True)
    raw = f"{work}/vo/full_raw.wav"
    if not os.path.exists(raw):
        text = "\n\n".join(sc["text"] for sc in S["scenes"])
        models = [S["tts_model"]] if S.get("tts_model") else TTS_MODELS
        last = None
        for m in models:
            for attempt in range(3):
                try:
                    print(f"[vo] TTS {m} (percobaan {attempt + 1})", flush=True)
                    G.tts(text, raw, voice=S.get("voice", "Charon"), model=m, style=S.get("style", DEFAULT_STYLE))
                    break
                except Exception as e:
                    last = e; code = getattr(e, "code", None)
                    body = e.read().decode()[:300] if hasattr(e, "read") else ""
                    print(f"[vo] gagal {code}: {body or e}", flush=True)
                    if code == 429 and "PerDay" in body: break      # kuota harian model ini habis -> model berikutnya
                    if code in (400, 404): break                      # model tidak tersedia
                    time.sleep(20)
            if os.path.exists(raw): break
        if not os.path.exists(raw):
            raise SystemExit(f"TTS gagal di semua model: {last}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-ar", "24000", "-ac", "1", f"{work}/vo/full.wav"], check=True)
    x, sr = load_wav(f"{work}/vo/full.wav")
    ivs = A.voiced_intervals(x, sr)
    words, spans = A.align_scenes([sc["text"] for sc in S["scenes"]], ivs)
    timing = []
    for k, ((a, b), ws) in enumerate(zip(spans, words)):
        a0 = max(0, a - 0.05); b0 = min(len(x) / sr, b + 0.10)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{work}/vo/full.wav", "-ss", f"{a0:.3f}", "-to", f"{b0:.3f}", f"{work}/vo/vo_{k}.wav"], check=True)
        timing.append([[wd, round(t - a0, 3)] for wd, t in ws])
    json.dump(timing, open(f"{work}/vo/timing.json", "w"), ensure_ascii=False)
    print(f"[vo] selesai, {len(x) / sr:.1f} detik", flush=True)

def check_vo(S, work):
    """Transkripsi ulang VO dan bandingkan dengan naskah (cek ada kalimat yang hilang/terpotong)."""
    try:
        heard = G.transcribe(f"{work}/vo/full.wav")
    except Exception as e:
        print(f"[cek] transkripsi dilewati: {e}", flush=True); return None
    norm = lambda s: re.findall(r"[a-z0-9]+", s.lower())
    want, got = norm(" ".join(sc["text"] for sc in S["scenes"])), set(norm(heard))
    missing = [w for w in want if w not in got and not w.isdigit()]
    ratio = 1 - len(missing) / max(1, len(want))
    open(f"{work}/vo/transcript.txt", "w").write(heard)
    print(f"[cek] kecocokan kata {ratio:.0%}", flush=True)
    if ratio < 0.85:
        raise SystemExit(f"VO tidak cocok dengan naskah ({ratio:.0%}). Kata hilang: {missing[:20]}")
    return ratio

def load_wav(p):
    w = wave.open(p); sr = w.getframerate()
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768, sr

# ============================== TIMING ==============================
def chunks(aligned, hl):
    hlset = {h.lower() for h in hl}
    out, cur = [], []
    for w, t in aligned:
        cur.append((w, t))
        txt = " ".join(x for x, _ in cur)
        if re.search(r"[,.?!]$", w) or len(cur) >= 3 or len(txt) >= 15:
            out.append(cur); cur = []
    if cur: out.append(cur)
    res = []
    for c in out:
        s = ""
        for w, _ in c:
            core = re.sub(r"[,.!?]+$", "", w); tail = w[len(core):]
            tail = tail.replace(",", "").replace(".", "") if tail in (",", ".") else tail
            s += (f"*{core}*" if core.lower().strip("\"'") in hlset else core) + tail + " "
        res.append((s.strip(), c[0][1]))
    return res

def scene_info(S, work, i):
    x, sr = load_wav(f"{work}/vo/vo_{i}.wav")
    dur = len(x) / sr
    al = [tuple(p) for p in json.load(open(f"{work}/vo/timing.json"))[i]]
    ch = chunks(al, S["scenes"][i].get("hl", []))
    T = LEAD + dur + TAIL
    if "card" in S["scenes"][i]: T = max(T, 4.2)
    n = int(round(T * FPS))
    return dict(dur=dur, T=n / FPS, n=n, chunks=[(c, t + LEAD) for c, t in ch])

# ============================== CHARACTERS ==============================
SKIN = (246, 224, 200)
def person(img, x, y, sc=1.0, hair=(52, 36, 28), shirt=(70, 80, 120), expr="neutral", alpha=1.0, label=None, t=0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    r = 92 * sc; hy = y - 120 * sc
    d.rounded_rectangle((x - 120 * sc, hy + r * 0.85, x + 120 * sc, hy + r + 230 * sc), int(70 * sc), fill=tuple(shirt))
    d.rectangle((x - 28 * sc, hy + r * 0.7, x + 28 * sc, hy + r + 12 * sc), fill=(226, 200, 176))
    d.ellipse((x - r, hy - r, x + r, hy + r), fill=SKIN)
    hair = tuple(hair)
    d.pieslice((x - r - 4 * sc, hy - r - 10 * sc, x + r + 4 * sc, hy + r * 0.55), 180, 360, fill=hair)
    d.ellipse((x - r, hy - r * 0.75, x - r * 0.55, hy + r * 0.05), fill=hair)
    d.ellipse((x + r * 0.55, hy - r * 0.75, x + r, hy + r * 0.05), fill=hair)
    blink = (t % 3.3) < 0.12; ey = hy + 10 * sc
    for k in (-1, 1):
        ex = x + k * 34 * sc
        if expr == "cry" or blink:
            d.arc((ex - 12 * sc, ey - 8 * sc, ex + 12 * sc, ey + 10 * sc), 200, 340, fill=(40, 30, 25), width=max(2, int(5 * sc)))
        else:
            d.ellipse((ex - 9 * sc, ey - 12 * sc, ex + 9 * sc, ey + 12 * sc), fill=(40, 30, 25))
        if expr in ("worry", "cry"):
            d.line((ex - 16 * sc, ey - 30 * sc + (k * -6 * sc), ex + 16 * sc, ey - 30 * sc - (k * -6 * sc)), fill=(60, 40, 30), width=max(2, int(5 * sc)))
        if expr == "cry":
            ty = ey + 18 * sc + ((t * 60) % 40) * sc
            d.ellipse((ex - 6 * sc, ty, ex + 6 * sc, ty + 16 * sc), fill=(140, 190, 240))
    my = hy + 52 * sc
    if expr == "smile": d.arc((x - 28 * sc, my - 22 * sc, x + 28 * sc, my + 14 * sc), 20, 160, fill=(120, 50, 40), width=max(2, int(6 * sc)))
    elif expr in ("worry", "cry"): d.arc((x - 22 * sc, my - 2 * sc, x + 22 * sc, my + 26 * sc), 200, 340, fill=(120, 50, 40), width=max(2, int(6 * sc)))
    elif expr == "shock": d.ellipse((x - 12 * sc, my - 10 * sc, x + 12 * sc, my + 16 * sc), fill=(90, 40, 35))
    else: d.line((x - 18 * sc, my, x + 18 * sc, my), fill=(120, 50, 40), width=max(2, int(6 * sc)))
    if label:
        d.text((x, hy - r - 50 * sc), label, font=font(F_BOLD, max(8, int(40 * sc))), fill=(235, 235, 245), anchor="mm")
    if alpha < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(lay)

def crescent(img, mx, my, a=1.0):
    paste_c(img, R.GLOW_SMALL, mx, my, 0.9 * a)
    m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
    md.ellipse((mx - 70, my - 70, mx + 70, my + 70), fill=int(255 * a))
    md.ellipse((mx - 38, my - 92, mx + 102, my + 48), fill=0)
    img.paste(Image.new("RGBA", (W, H), (250, 236, 196, 255)), (0, 0), m)

# ============================== ILLUSTRATIONS ==============================
# Tiap ilustrasi: f(img, t, T, sc, S). sc = dict scene (bisa berisi "who", "expr", dll.)
def _char(S, key):
    c = S.get("chars", {}).get(key, {})
    return dict(hair=c.get("hair", [40, 28, 22] if key == "A" else [30, 26, 30]),
                shirt=c.get("shirt", [176, 92, 64] if key == "A" else [64, 110, 100])), c.get("name", key)

def il_duo(img, t, T, sc, S):
    """Dua tokoh berdampingan, muncul bergantian."""
    paste_c(img, R.GLOW_GOLD, CX, CY, 0.6)
    expr = sc.get("expr", "smile")
    for k, key in enumerate(("A", "B")):
        s = ease_back((t - 0.2 - k * 0.5) / 0.6)
        if s <= 0.05: continue
        look, nm = _char(S, key)
        person(img, CX + (-200 if k == 0 else 200), CY - 50 + math.sin(t * 1.6 + k) * 6, sc=0.95 * s, expr=expr, label=nm, t=t + k, **look)

def il_solo(img, t, T, sc, S):
    """Satu tokoh di tengah. sc: who=A/B, expr=awal, expr2=ekspresi setelah 'switch' (0-1, default 0.6)."""
    look, nm = _char(S, sc.get("who", "A"))
    p = t / T
    expr = sc.get("expr2", sc.get("expr", "neutral")) if p > sc.get("switch", 0.6) else sc.get("expr", "neutral")
    paste_c(img, R.GLOW_GOLD, CX, CY - 40, 0.55)
    person(img, CX, CY - 20 + math.sin(t * 1.4) * 6, sc=1.05 * ease_back(t / 0.5), expr=expr, label=nm, t=t, **look)

def icon_ring(d, x, y, s):
    d.ellipse((x - 40 * s, y - 40 * s, x + 40 * s, y + 40 * s), outline=GOLD, width=max(2, int(12 * s)))
    d.polygon([(x - 18 * s, y - 40 * s), (x + 18 * s, y - 40 * s), (x, y - 66 * s)], fill=(170, 220, 255))
def icon_house(d, x, y, s):
    d.polygon([(x - 60 * s, y), (x, y - 55 * s), (x + 60 * s, y)], fill=(196, 72, 64))
    d.rectangle((x - 45 * s, y, x + 45 * s, y + 55 * s), fill=(236, 226, 205))
    d.rectangle((x - 12 * s, y + 20 * s, x + 12 * s, y + 55 * s), fill=(110, 78, 48))
def icon_cal(d, x, y, s):
    d.rounded_rectangle((x - 45 * s, y - 40 * s, x + 45 * s, y + 45 * s), int(10 * s) + 1, fill=(236, 232, 222))
    d.rectangle((x - 45 * s, y - 40 * s, x + 45 * s, y - 15 * s), fill=(196, 72, 64))
def icon_coin(d, x, y, s):
    d.ellipse((x - 42 * s, y - 42 * s, x + 42 * s, y + 42 * s), fill=GOLD)
    d.ellipse((x - 28 * s, y - 28 * s, x + 28 * s, y + 28 * s), outline=(150, 110, 50), width=max(2, int(6 * s)))
def icon_phone(d, x, y, s):
    d.rounded_rectangle((x - 32 * s, y - 55 * s, x + 32 * s, y + 55 * s), int(12 * s) + 1, fill=(40, 44, 60))
    d.rounded_rectangle((x - 25 * s, y - 45 * s, x + 25 * s, y + 40 * s), int(6 * s) + 1, fill=(120, 170, 255))

def il_dreams(img, t, T, sc, S):
    """Tokoh dengan ikon rencana dunia yang melayang, lalu hilang di 'switch' (default 0.68)."""
    look, nm = _char(S, sc.get("who", "A"))
    p = t / T; sw = sc.get("switch", 0.68); gone = p > sw
    paste_c(img, R.GLOW_GOLD, CX, CY, 0.5)
    person(img, CX, CY - 20, sc=1.05, expr="shock" if gone else "smile", label=nm, t=t, **look)
    fade = 1 - ease((p - sw) / 0.15) if gone else 1
    if fade > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        icons = [icon_ring, icon_house, icon_cal, icon_coin, icon_phone]
        pick = [icons[(sc.get("seed", 0) + k) % len(icons)] for k in range(3)]
        for k, (fn, (ox, oy)) in enumerate(zip(pick, ((-290, 470), (0, 380), (290, 470)))):
            s = ease_back((t - 0.4 - k * 0.45) / 0.5)
            if s > 0: fn(ld, CX + ox, oy + math.sin(t * 2 + k) * 12, s)
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * fade)))
        img.alpha_composite(lay)

def il_night(img, t, T, sc, S):
    """Tokoh merenung di malam hari, bulan sabit, bubble tanda tanya."""
    look, nm = _char(S, sc.get("who", "B"))
    crescent(img, CX + 340, 360, ease(t / 0.8))
    p = t / T
    person(img, CX - 40, CY - 10, sc=1.05, expr=sc.get("expr", "worry") if p > 0.35 else "neutral", label=nm, t=t, **look)
    if p > 0.45:
        d = ImageDraw.Draw(img); s = ease_back((p - 0.45) / 0.08)
        bx, by = CX + 170, 520
        for rr, dx, dy in ((14, -95, 120), (22, -60, 80)):
            d.ellipse((bx + dx - rr * s, by + dy - rr * s, bx + dx + rr * s, by + dy + rr * s), fill=(236, 232, 222))
        d.ellipse((bx - 80 * s, by - 60 * s, bx + 80 * s, by + 60 * s), fill=(236, 232, 222))
        d.text((bx, by), sc.get("bubble", "?"), font=font(F_BOLD, max(10, int(90 * s))), fill=(40, 40, 55), anchor="mm")

def il_choice(img, t, T, sc, S):
    """Sorotan bergantian antara dua tokoh (pertanyaan 'kamu yang mana?')."""
    turn = int(t / 1.1) % 2
    for k, key in enumerate(("A", "B")):
        look, nm = _char(S, key)
        x = CX + (-200 if k == 0 else 200); on = (k == turn)
        paste_c(img, R.GLOW_SMALL, x, CY - 130, 1.0 if on else 0.25)
        person(img, x, CY - 50, sc=0.95, expr="neutral", label=nm, alpha=1.0 if on else 0.45, t=t + k, **look)

def il_angel(img, t, T, sc, S):
    """Sosok bercahaya bersayap (tanpa wajah) dengan aura dan cincin cahaya."""
    s = ease(t / 0.8); cy = CY - 40 + math.sin(t * 1.2) * 8
    paste_c(img, R.GLOW_GOLD, CX, cy, 0.9 * s)
    d = ImageDraw.Draw(img)
    for k in (-1, 1):
        for j in range(4):
            L = (300 - j * 45) * s; up = 120 - j * 55
            d.polygon([(CX + k * 50, cy - 40 + j * 10), (CX + k * (60 + L), cy - up - 60), (CX + k * (40 + L * 0.8), cy - up + 10), (CX + k * 50, cy + 40 + j * 20)],
                      fill=(236 - j * 8, 220 - j * 8, 180 - j * 8))
    d.rounded_rectangle((CX - 70 * s, cy - 80, CX + 70 * s, cy + 200), int(60 * s) + 1, fill=(245, 238, 222))
    d.ellipse((CX - 60, cy - 190, CX + 60, cy - 70), fill=(250, 246, 236))
    d.ellipse((CX - 70, cy - 236, CX + 70, cy - 206), outline=GOLD, width=8)

def il_grave(img, t, T, sc, S):
    """Makam dengan nisan, tanah, hujan rintik."""
    d = ImageDraw.Draw(img)
    s = ease(t / 0.6)
    d.rectangle((0, 1000, W, 1160), fill=(52, 40, 34))
    d.ellipse((CX - 260, 930, CX + 260, 1060), fill=(70, 54, 44))
    d.rounded_rectangle((CX - 70, 760 + (1 - s) * 200, CX + 70, 990), 40, fill=(150, 150, 160))
    d.line((CX - 40, 830 + (1 - s) * 200, CX + 40, 830 + (1 - s) * 200), fill=(110, 110, 120), width=6)
    rng = np.random.default_rng(int(t * 20))
    for _ in range(60):
        x = rng.uniform(0, W); y = (rng.uniform(0, H) + t * 900) % 1100
        d.line((x, y, x - 8, y + 34), fill=(150, 170, 220), width=2)

def il_crowd(img, t, T, sc, S):
    """Kerumunan siluet di padang luas, cahaya dari atas (mahsyar, antrian, kebangkitan)."""
    s = ease(t / 0.8)
    beam = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(beam)
    bd.polygon([(CX - 120, 0), (CX + 120, 0), (CX + 520, 1100), (CX - 520, 1100)], fill=(255, 230, 170, int(50 * s)))
    img.alpha_composite(beam.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 1040, W, 1180), fill=(70, 58, 44))
    rng = np.random.default_rng(5)
    for row in range(4):
        y = 860 + row * 55
        for k in range(16):
            x = k * 72 + rng.uniform(-20, 20) + (row % 2) * 36
            h = rng.uniform(110, 150) * (0.7 + 0.1 * row)
            bob = math.sin(t * 2 + k + row) * 4 if sc.get("move") else 0
            c = 18 + row * 6
            d.ellipse((x - 18, y - h + bob, x + 18, y - h + 36 + bob), fill=(c, c, c + 10))
            d.rounded_rectangle((x - 26, y - h + 30 + bob, x + 26, y + 40), 18, fill=(c, c, c + 10))

def il_scale(img, t, T, sc, S):
    """Timbangan amal yang berayun."""
    paste_c(img, R.GLOW_GOLD, CX, CY - 60, 0.7)
    d = ImageDraw.Draw(img); s = ease_back(t / 0.6)
    tilt = math.sin(t * 1.3) * 0.18 * (1 - min(1, t / T))
    d.rectangle((CX - 10, CY - 260, CX + 10, CY + 140), fill=GOLD)
    d.polygon([(CX - 120, CY + 180), (CX + 120, CY + 180), (CX, CY + 120)], fill=GOLD)
    L = 300 * s
    x1, y1 = CX - L * math.cos(tilt), CY - 250 - L * math.sin(tilt)
    x2, y2 = CX + L * math.cos(tilt), CY - 250 + L * math.sin(tilt)
    d.line((x1, y1, x2, y2), fill=GOLD, width=10)
    for x, y in ((x1, y1), (x2, y2)):
        d.line((x, y, x - 70, y + 170), fill=GOLD, width=4); d.line((x, y, x + 70, y + 170), fill=GOLD, width=4)
        d.chord((x - 100, y + 120, x + 100, y + 220), 0, 180, fill=GOLD)

def il_sun(img, t, T, sc, S):
    """Matahari sangat dekat dan panas, layar menghangat."""
    s = ease(t / 1.2)
    warm = Image.new("RGBA", (W, H), (255, 140, 40, int(30 * s))); img.alpha_composite(warm)
    dd = ImageDraw.Draw(img)
    for k in range(16):
        an = k * math.pi / 8 + t * 0.2
        dd.line((CX + math.cos(an) * 330, 520 + math.sin(an) * 330, CX + math.cos(an) * 470, 520 + math.sin(an) * 470), fill=(255, 200, 110), width=10)
    paste_c(img, R.GLOW_GOLD, CX, 520, 1.0)
    d = ImageDraw.Draw(img); r = 200 + 80 * s + math.sin(t * 4) * 6
    d.ellipse((CX - r, 520 - r, CX + r, 520 + r), fill=(255, 236, 190))

def il_gate(img, t, T, sc, S):
    """Gerbang bercahaya besar (surga) atau gelap (sc.dark=true)."""
    dark = sc.get("dark", False)
    s = ease(t / 0.8)
    col = (90, 40, 30) if dark else (255, 226, 160)
    paste_c(img, R.GLOW_SMALL if dark else R.GLOW_GOLD, CX, CY - 60, 0.9 * s)
    d = ImageDraw.Draw(img)
    gw, gh = 420, 560; x0, y0 = CX - gw / 2, CY - 360
    d.rectangle((x0 - 30, y0 + gw / 2, x0 + gw + 30, y0 + gh + 20), fill=(60, 50, 44))
    d.pieslice((x0 - 30, y0 - 30, x0 + gw + 30, y0 + gw + 30), 180, 360, fill=(60, 50, 44))
    d.rectangle((x0, y0 + gw / 2, x0 + gw, y0 + gh), fill=col)
    d.pieslice((x0, y0, x0 + gw, y0 + gw), 180, 360, fill=col)
    for k in range(1, 6):
        d.line((x0 + k * gw / 6, y0 + 60, x0 + k * gw / 6, y0 + gh), fill=(60, 50, 44), width=6)

def il_wall(img, t, T, sc, S):
    """Tembok besar menjulang (Yakjuj-Makjuj) dengan retakan yang menjalar."""
    d = ImageDraw.Draw(img); s = ease(t / 0.8)
    d.rectangle((60, 380 + (1 - s) * 300, W - 60, 1060), fill=(96, 88, 92))
    for row in range(9):
        y = 400 + row * 72
        for k in range(8):
            x = 60 + k * 120 + (row % 2) * 60
            if x + 116 > W - 60: continue
            d.rectangle((x + 4, y + 4, x + 116, y + 66), outline=(70, 64, 68), width=4)
    p = min(1, t / T)
    pts = [(CX, 380)]
    rng = np.random.default_rng(3)
    for k in range(int(12 * p)):
        pts.append((pts[-1][0] + rng.uniform(-60, 60), pts[-1][1] + 56))
    if len(pts) > 1: d.line(pts, fill=(20, 16, 18), width=8)

def il_eye(img, t, T, sc, S):
    """Satu mata besar yang mengintai (sosok misterius/Dajjal) - simbolik, tanpa wajah utuh."""
    s = ease(t / 0.8)
    paste_c(img, R.GLOW_BLUE, CX, CY - 40, 0.8 * s)
    d = ImageDraw.Draw(img)
    open_ = 0.15 + 0.85 * ease((t - 0.3) / 0.8)
    w, h = 300, 150 * open_
    d.ellipse((CX - w, CY - 40 - h, CX + w, CY - 40 + h), fill=(230, 228, 236))
    look = math.sin(t * 0.9) * 60
    d.ellipse((CX - 85 + look, CY - 40 - min(h, 85), CX + 85 + look, CY - 40 + min(h, 85)), fill=(150, 30, 30))
    d.ellipse((CX - 35 + look, CY - 40 - min(h, 35), CX + 35 + look, CY - 40 + min(h, 35)), fill=(10, 10, 14))

def il_sunwest(img, t, T, sc, S):
    """Matahari terbit dari barat: horizon, panah arah, matahari naik di sisi kiri."""
    d = ImageDraw.Draw(img); p = ease(t / T)
    d.rectangle((0, 1000, W, 1180), fill=(30, 34, 50))
    sy = 1000 - 360 * p
    paste_c(img, R.GLOW_GOLD, 260, sy, 0.9)
    d = ImageDraw.Draw(img)
    d.ellipse((260 - 110, sy - 110, 260 + 110, sy + 110), fill=(255, 210, 120))
    d.text((150, 1080), "BARAT", font=font(F_BOLD, 44), fill=(235, 235, 245), anchor="mm")
    d.text((W - 150, 1080), "TIMUR", font=font(F_BOLD, 44), fill=(120, 120, 140), anchor="mm")

def il_city(img, t, T, sc, S):
    """Gedung-gedung yang tumbuh makin tinggi dengan jendela menyala."""
    d = ImageDraw.Draw(img); p = ease(t / max(T, 0.1))
    d.rectangle((0, 1060, W, 1180), fill=(24, 26, 40))
    rng = np.random.default_rng(11)
    xs = [40, 170, 300, 430, 560, 690, 820, 950]
    for k, x in enumerate(xs):
        base_h = rng.uniform(160, 260); grow = rng.uniform(120, 240)
        h = base_h + grow * p
        w = rng.uniform(90, 120)
        col = (34 + k % 3 * 6, 38 + k % 2 * 6, 58)
        d.rectangle((x, 1060 - h, x + w, 1060), fill=col)
        for wy in range(int(1060 - h + 20), 1040, 46):
            for wx in range(int(x + 14), int(x + w - 20), 34):
                if (wx * 7 + wy * 13 + k * 5) % 9 < 5:
                    d.rectangle((wx, wy, wx + 16, wy + 22), fill=(255, 210, 120))

def il_cta(img, t, T, sc, S):
    d = ImageDraw.Draw(img); s = ease_back(t / 0.5)
    cy = CY - 170 + math.sin(t * 2.4) * 12; w, h = 400 * s, 280 * s
    paste_c(img, R.GLOW_GOLD, CX, cy, 0.6)
    d.rounded_rectangle((CX - w / 2, cy - h / 2, CX + w / 2, cy + h / 2), int(60 * s) + 1, fill=YEL)
    d.polygon([(CX - 60 * s, cy + h / 2 - 5), (CX + 20 * s, cy + h / 2 - 5), (CX - 90 * s, cy + h / 2 + 80 * s)], fill=YEL)
    for k in (-1, 0, 1):
        bob = math.sin(t * 6 - k) * 10 * s
        d.ellipse((CX + k * 105 * s - 26 * s, cy - 26 * s + bob, CX + k * 105 * s + 26 * s, cy + 26 * s + bob), fill=(40, 30, 10))

from PIL import ImageFilter  # used by il_crowd
ILS = {n[3:]: f for n, f in globals().items() if n.startswith("il_") and callable(f)}
for _n in ("globe", "clock", "door", "candle", "mosque", "hourglass", "calendar"):
    _f = getattr(R, "il_" + _n)
    ILS[_n] = (lambda f: (lambda img, t, T, sc, S: f(img, t, T)))(_f)

# ============================== FRAMES ==============================
def draw_kw(img, kw, kw2, t):
    a = ease(t / 0.3)
    if a <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    s = 0.85 + 0.15 * ease_back(t / 0.35)
    size = 100 if len(kw) <= 16 else 80
    f = font(F_BOLD, int(size * s)); y = 1110 if not kw2 else 1060
    d.text((CX + 4, y + 6), kw, font=f, fill=(0, 0, 0, 140), anchor="mm")
    d.text((CX, y), kw, font=f, fill=YEL + (255,), anchor="mm")
    if kw2: d.text((CX, y + 90), kw2, font=font(F_BOLD, int(52 * s)), fill=WHITE + (255,), anchor="mm")
    lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(lay)

def frames(S, work, i):
    sc = S["scenes"][i]; info = scene_info(S, work, i)
    il = ILS[sc["il"]]; T = info["T"]; ch = info["chunks"]; has_kw = "kw" in sc
    head = f'{S["series"].upper()}  ·  PART {S["part"]}'
    for f in range(info["n"]):
        t = f / FPS
        img = BG.convert("RGBA"); d = ImageDraw.Draw(img)
        for (x, y, r, ph, sp) in STARS:
            a = int(70 + 70 * math.sin(t * sp * 2 + ph))
            d.ellipse((x - r, y - r, x + r, y + r), fill=(220, 225, 255, max(0, a)))
        il(img, t, T, sc, S)
        if "card" in sc: R.draw_card(img, sc["card"][0], sc["card"][1], t - 0.15, *(sc["card"][2:3]))
        if has_kw: draw_kw(img, sc["kw"], sc.get("kw2"), t - 0.3)
        cur = None
        for c, st in ch:
            if t >= st: cur = (c, st)
        if cur and t < LEAD + info["dur"] + 0.25:
            R.draw_caption(img, cur[0], t - cur[1], y=1300 if has_kw else 1240)
        R.draw_header(img, i, len(S["scenes"]), head)
        fade = min(1, f / 5, (info["n"] - 1 - f) / 5)
        out = img.convert("RGB")
        if fade < 1: out = Image.blend(Image.new("RGB", (W, H)), out, max(0, fade))
        yield out

def render_scene(args):
    S, work, i = args
    path = f"{work}/scenes/s{i}.mp4"; tmp = path.replace(".mp4", ".tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for fr in frames(S, work, i): p.stdin.write(fr.tobytes())
    p.stdin.close()
    if p.wait() != 0: raise RuntimeError(f"ffmpeg gagal di scene {i}")
    os.replace(tmp, path)
    return i

# ============================== AUDIO ==============================
def build_audio(S, work):
    SR = 44100; parts, starts, pos = [], [], 0.0
    for i in range(len(S["scenes"])):
        info = scene_info(S, work, i); x, sr = load_wav(f"{work}/vo/vo_{i}.wav")
        x = np.interp(np.arange(int(len(x) * SR / sr)) * sr / SR, np.arange(len(x)), x)
        seg = np.zeros(int(round(info["n"] / FPS * SR)))
        s0 = int(LEAD * SR); seg[s0:s0 + len(x)] = x[:len(seg) - s0]
        parts.append(seg); starts.append(pos); pos += info["n"] / FPS
    vo = np.concatenate(parts); vo = vo / (np.abs(vo).max() + 1e-9) * 0.9
    n = len(vo); t = np.arange(n) / SR; rng = np.random.default_rng(S["part"]); total = n / SR
    def tone(f, amp, det=0.3): return amp * (np.sin(2 * np.pi * f * t) + 0.6 * np.sin(2 * np.pi * (f + det) * t + 1.3) + 0.25 * np.sin(2 * np.pi * 2 * f * t + 0.7))
    progs = [[[110, 164.81, 220, 261.63], [87.31, 130.81, 174.61, 220], [130.81, 196, 261.63, 329.63], [98, 146.83, 196, 246.94]],
             [[73.42, 110, 146.83, 174.61], [65.41, 98, 130.81, 164.81], [87.31, 130.81, 174.61, 220], [82.41, 123.47, 164.81, 207.65]]]
    chords = progs[S["part"] % len(progs)]
    pad = np.zeros(n); seg = total / 4
    for k, chd in enumerate(chords):
        env = np.clip(1 - np.abs((t - (k + 0.5) * seg) / (seg * 0.75)), 0, 1) ** 1.2
        for fq in chd: pad += tone(fq, 0.05) * env
    pad += 0.06 * np.sin(2 * np.pi * 55 * t)
    pad += np.convolve(rng.standard_normal(n), np.ones(400) / 400, mode="same") * 0.5
    fx = np.zeros(n)
    for st in starts:
        s = int(st * SR); L = int(1.4 * SR); tt = np.arange(L) / SR
        boom = np.sin(2 * np.pi * (48 + 30 * np.exp(-tt * 6)) * tt) * np.exp(-tt * 2.6)
        e = min(n, s + L); fx[s:e] += boom[:e - s]
    mix = vo + pad / (np.abs(pad).max() + 1e-9) * 0.16 + fx * 0.25
    mix *= np.minimum(1, np.minimum(t / 0.6, (total - t) / 1.2))
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
    with wave.open(f"{work}/mix.wav", "w") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())

# ============================== COVER + CAPTION ==============================
PART_COLORS = [(255, 92, 140), (245, 192, 74), (90, 160, 255), (110, 220, 140), (170, 130, 255), (255, 140, 70)]
def make_cover(S, work, out):
    img = BG.convert("RGBA")
    sc0 = S["scenes"][S.get("cover_scene", 0)]
    ILS[sc0["il"]](img, 3.0, 6.0, sc0, S)
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 110)); img.alpha_composite(shade)
    d = ImageDraw.Draw(img)
    d.text((80, 300), S["series"].upper(), font=font(R.F_MED, 30), fill=(210, 210, 225))
    col = PART_COLORS[(S["part"] - 1) % len(PART_COLORS)]
    d.text((80, 360), "PART", font=font(F_BOLD, 120), fill=WHITE)
    d.text((80 + font(F_BOLD, 120).getlength("PART "), 300), str(S["part"]), font=font(F_BOLD, 220), fill=col)
    d.rectangle((80, 520, 200, 530), fill=col)
    y = 570
    for line in S["title"].upper().split("|"):
        d.text((80, y), line.strip(), font=font(F_BOLD, 96), fill=WHITE); y += 110
    img.convert("RGB").save(out, quality=92)

def make_caption(S, out):
    cap = S.get("caption") or f'{S["title"].replace("|", " ")}. Part {S["part"]} dari seri {S["series"]}.'
    tags = S.get("hashtags", ["#kisahsetelahdunia", "#akhirat", "#pengingatdiri", "#ceritaislami", "#animasi"])
    open(out, "w").write(cap.strip() + "\n\n" + S.get("cta", "Mau lanjut part berikutnya? Tulis LANJUT di komentar.") + "\n\n" + " ".join(tags) + "\n")

# ============================== MAIN ==============================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script"); ap.add_argument("--preview", action="store_true"); ap.add_argument("--no-check", action="store_true")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    S = json.load(open(a.script))
    name = os.path.splitext(os.path.basename(a.script))[0]
    work = f"work/{name}"; outdir = f"{a.out}/{name}"
    os.makedirs(f"{work}/scenes", exist_ok=True); os.makedirs(outdir, exist_ok=True)
    for i, sc in enumerate(S["scenes"]):
        if sc["il"] not in ILS: raise SystemExit(f"scene {i}: ilustrasi '{sc['il']}' tidak ada. Pilihan: {sorted(ILS)}")
    make_vo(S, work)
    if not a.no_check: check_vo(S, work)
    if a.preview:
        sheet = Image.new("RGB", (360 * len(S["scenes"]), 640))
        for i in range(len(S["scenes"])):
            info = scene_info(S, work, i); target = int(info["n"] * 0.6)
            for k, fr in enumerate(frames(S, work, i)):
                if k == target: sheet.paste(fr.resize((360, 640)), (i * 360, 0)); break
        sheet.save(f"{outdir}/preview.jpg", quality=85); print(f"[ok] {outdir}/preview.jpg"); return
    jobs = [(S, work, i) for i in range(len(S["scenes"]))]
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        for i in ex.map(render_scene, jobs): print(f"[render] scene {i} selesai", flush=True)
    build_audio(S, work)
    with open(f"{work}/list.txt", "w") as f:
        for i in range(len(S["scenes"])): f.write(f"file 'scenes/s{i}.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{work}/list.txt", "-c", "copy", f"{work}/video.mp4"], check=True)
    final = f"{outdir}/{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{work}/video.mp4", "-i", f"{work}/mix.wav", "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", final], check=True)
    make_cover(S, work, f"{outdir}/cover.jpg")
    make_caption(S, f"{outdir}/caption.txt")
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", final], capture_output=True, text=True).stdout.strip()
    print(f"[ok] {final} ({float(dur):.1f} detik)")

if __name__ == "__main__":
    main()
