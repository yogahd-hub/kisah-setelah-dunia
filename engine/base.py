"""Base drawing kit: background, glow, captions, dalil card, header, generic illustrations."""
import math, random, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W, H, FPS = 1080, 1920, 30
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
F_BOLD = os.path.join(FONTS, "Poppins-Bold.ttf")
F_SEMI = os.path.join(FONTS, "Poppins-SemiBold.ttf")
F_MED = os.path.join(FONTS, "Poppins-Medium.ttf")
if not os.path.exists(F_SEMI): F_SEMI = F_BOLD
if not os.path.exists(F_MED): F_MED = F_BOLD
F_AR = os.path.join(FONTS, "Amiri-Bold.ttf")

YEL = (245, 192, 74)
WHITE = (255, 255, 255)
GOLD = (222, 178, 96)
CREAM = (243, 234, 216)

def font(p, s): return ImageFont.truetype(p, s)
FCAP = font(F_BOLD, 88)
FHEAD = font(F_MED, 26)
FCARD_L = font(F_SEMI, 24)
FCARD_R = font(F_BOLD, 34)
FAR = font(F_AR, 54)

# ---------- static background ----------
def make_bg():
    y = np.linspace(0, 1, H)[:, None]
    top = np.array([16, 19, 38]); bot = np.array([5, 6, 12])
    arr = np.zeros((H, W, 3))
    for c in range(3):
        arr[:, :, c] = top[c] * (1 - y) + bot[c] * y
    img = Image.fromarray(arr.astype(np.uint8), "RGB")
    # diagonal light beam
    beam = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(beam)
    d.polygon([(380, -50), (700, -50), (1000, H), (420, H)], fill=26)
    beam = beam.filter(ImageFilter.GaussianBlur(90))
    img = Image.composite(Image.new("RGB", (W, H), (190, 200, 255)), img, beam)
    # vignette
    vx = np.linspace(-1, 1, W)[None, :]; vy = np.linspace(-1, 1, H)[:, None]
    v = np.clip(1 - 0.55 * (vx ** 2 + vy ** 2), 0.35, 1)
    a = np.asarray(img).astype(float) * v[:, :, None]
    return Image.fromarray(a.astype(np.uint8), "RGB")

BG = make_bg()
random.seed(7)
STARS = [(random.randint(0, W), random.randint(0, H), random.uniform(1, 3), random.uniform(0, 6.28), random.uniform(0.5, 1.5)) for _ in range(110)]

def glow_sprite(r, color, strength=255):
    s = r * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((s/2 - r, s/2 - r, s/2 + r, s/2 + r), fill=color + (strength,))
    return im.filter(ImageFilter.GaussianBlur(r * 0.8))

GLOW_GOLD = glow_sprite(260, (255, 205, 120), 120)
GLOW_SMALL = glow_sprite(90, (255, 214, 140), 200)
GLOW_BLUE = glow_sprite(300, (120, 150, 255), 70)

def paste_c(base, sp, cx, cy, alpha=1.0):
    if alpha < 1:
        sp = sp.copy(); a = sp.getchannel("A").point(lambda v: int(v * alpha)); sp.putalpha(a)
    base.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))

def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def ease_back(t):
    t = max(0, min(1, t)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

# ---------- caption with *highlight* ----------
def parse(chunk):
    out = []
    for i, part in enumerate(chunk.split("*")):
        for j, w in enumerate(part.split(" ")):
            if not w: continue
            if j == 0 and out and not part.startswith(" ") and not any(ch.isalnum() for ch in w):
                out[-1] = (out[-1][0] + "\x00" + w, out[-1][1]); continue
            out.append((w, i % 2 == 1))
    return out

def draw_caption(img, chunk, t_in, y=1240):
    words = parse(chunk)
    sc = 0.82 + 0.18 * ease_back(t_in / 0.25)
    al = ease(t_in / 0.15)
    f = font(F_BOLD, max(10, int(88 * sc)))
    space = f.getlength(" ")
    widths = [f.getlength(w.replace("\x00", "")) for w, _ in words]
    # wrap at 900
    lines, cur, cw = [], [], 0
    for (w, hl), wd in zip(words, widths):
        if cur and cw + space + wd > 920:
            lines.append((cur, cw)); cur, cw = [], 0
        cw = cw + (space if cur else 0) + wd; cur.append((w, hl, wd))
    if cur: lines.append((cur, cw))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    lh = int(110 * sc)
    y0 = y - lh * len(lines) / 2
    for li, (ws, lw) in enumerate(lines):
        x = (W - lw) / 2
        for w, hl, wd in ws:
            a_, _, b_ = w.partition("\x00")
            d.text((x + 3, y0 + li * lh + 5), a_ + b_, font=f, fill=(0, 0, 0, 150))
            d.text((x, y0 + li * lh), a_, font=f, fill=(YEL if hl else WHITE) + (255,))
            if b_: d.text((x + f.getlength(a_), y0 + li * lh), b_, font=f, fill=WHITE + (255,))
            x += wd + space
    if al < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * al)))
    img.alpha_composite(layer)

def draw_header(img, scene_i, n, text):
    d = ImageDraw.Draw(img)
    d.text((70, 92), text, font=FHEAD, fill=(200, 200, 215, 170))
    x0, w = 640, 370
    seg = w / n
    for i in range(n):
        col = (235, 235, 240, 230) if i <= scene_i else (120, 120, 140, 110)
        d.rounded_rectangle((x0 + i * seg + 3, 104, x0 + (i + 1) * seg - 3, 110), 3, fill=col)

def _wrap(text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if f.getlength(t) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def draw_card(img, text, ref, t, label="AL-QUR'AN"):
    """Kartu dalil. Teks Indonesia (arti ayat/hadits) atau teks Arab (otomatis terdeteksi)."""
    a = ease(t / 0.4)
    if a <= 0: return
    cw = 900
    is_ar = any("\u0600" <= c <= "\u06ff" for c in text)
    if is_ar:
        lines, fq, lh = [text], FAR, 70
    else:
        fq = font(F_MED, 38); lh = 52
        lines = _wrap("\u201c" + text.strip().strip('"\u201c\u201d') + "\u201d", fq, cw - 100)[:4]
    chh = 96 + lh * len(lines) + 70
    layer = Image.new("RGBA", (cw + 40, chh + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((24, 28, cw + 24, chh + 28), 26, fill=(0, 0, 0, 120))
    d.rounded_rectangle((20, 20, cw + 20, chh + 20), 26, fill=CREAM + (255,))
    d.text((60, 46), label, font=FCARD_L, fill=(140, 125, 100))
    y = 96
    for ln in lines:
        if is_ar: d.text((cw - 20, y), ln, font=fq, fill=(40, 34, 28), anchor="ra", direction="rtl", language="ar")
        else: d.text((60, y), ln, font=fq, fill=(40, 34, 28))
        y += lh
    d.text((60, y + 14), ref, font=FCARD_R, fill=(150, 90, 40))
    layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    img.alpha_composite(layer, (int((W - cw) / 2 - 20), int(230 + 40 * (1 - a))))

# ---------- illustrations ----------
CX, CY = W // 2, 800

def il_hourglass(img, t, T):
    paste_c(img, GLOW_GOLD, CX, CY, 0.8)
    d = ImageDraw.Draw(img)
    s = ease_back(t / 0.6)
    fy = math.sin(t * 1.5) * 10
    w, h = 300 * s, 420 * s
    cy = CY + fy
    top, bot = cy - h / 2, cy + h / 2
    d.rounded_rectangle((CX - w/2 - 30, top - 34, CX + w/2 + 30, top), 10, fill=(110, 78, 48))
    d.rounded_rectangle((CX - w/2 - 30, bot, CX + w/2 + 30, bot + 34), 10, fill=(110, 78, 48))
    glass = (45, 55, 90)
    d.polygon([(CX - w/2, top), (CX + w/2, top), (CX + 12*s, cy), (CX - 12*s, cy)], fill=glass)
    d.polygon([(CX - 12*s, cy), (CX + 12*s, cy), (CX + w/2, bot), (CX - w/2, bot)], fill=glass)
    p = min(1, t / max(T, 0.1)) * 0.6 + 0.2  # sand fraction moved
    # top sand (remaining)
    rem = 1 - p
    ys = cy - (h/2) * rem
    hw = 12*s + (w/2 - 12*s) * rem
    d.polygon([(CX - hw, ys), (CX + hw, ys), (CX + 12*s, cy), (CX - 12*s, cy)], fill=GOLD)
    # bottom pile
    yb = bot - (h/2) * p * 0.75
    d.polygon([(CX - w/2, bot), (CX + w/2, bot), (CX, yb)], fill=GOLD)
    d.line((CX, cy, CX, yb), fill=GOLD, width=max(1, int(6*s)))

def il_calendar(img, t, T):
    paste_c(img, GLOW_BLUE, CX, CY, 0.9)
    d = ImageDraw.Draw(img)
    s = ease_back(t / 0.6); cy = CY + math.sin(t * 1.4) * 10
    w, h = 460 * s, 440 * s
    x0, y0 = CX - w/2, cy - h/2
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), 30, fill=(236, 232, 222))
    d.rounded_rectangle((x0, y0, x0 + w, y0 + 110*s), 30, fill=(196, 72, 64))
    d.rectangle((x0, y0 + 80*s, x0 + w, y0 + 110*s), fill=(196, 72, 64))
    for k in (-1, 1):
        d.rounded_rectangle((CX + k*120*s - 12*s, y0 - 30*s, CX + k*120*s + 12*s, y0 + 40*s), 10, fill=(80, 80, 95))
    # flipping question marks
    q = ["?", "??", "???"][int(t * 2.2) % 3]
    fq = font(F_BOLD, max(10, int(190 * s)))
    d.text((CX, y0 + 280*s), q, font=fq, fill=(40, 40, 55), anchor="mm")

def il_globe(img, t, T):
    paste_c(img, GLOW_BLUE, CX, CY, 1)
    d = ImageDraw.Draw(img)
    s = ease_back(t / 0.6); r = 210 * s; cy = CY + 110
    d.ellipse((CX - r, cy - r, CX + r, cy + r), fill=(38, 70, 130))
    rot = t * 40
    for k in range(-3, 4):  # meridians
        off = ((k * 60 + rot) % 360) - 180
        ew = abs(math.cos(math.radians(off))) * r
        if abs(off) < 90:
            d.ellipse((CX - ew, cy - r, CX + ew, cy + r), outline=(90, 130, 200), width=3)
    for k in (-2, -1, 0, 1, 2):
        yy = cy + k * r / 3; hw = math.sqrt(max(0, r*r - (yy - cy)**2))
        d.line((CX - hw, yy, CX + hw, yy), fill=(90, 130, 200), width=3)
    d.ellipse((CX - r, cy - r, CX + r, cy + r), outline=(150, 180, 240), width=5)
    # pin
    bounce = abs(math.sin(t * 3)) * 20
    px, py = CX + 40, cy - r - 30 - bounce
    paste_c(img, GLOW_SMALL, px, py, 0.6)
    d.ellipse((px - 55, py - 55, px + 55, py + 55), fill=YEL)
    d.polygon([(px - 40, py + 35), (px + 40, py + 35), (px, py + 120)], fill=YEL)
    d.text((px, py - 4), "?", font=font(F_BOLD, 80), fill=(40, 30, 10), anchor="mm")

def il_clock(img, t, T):
    paste_c(img, GLOW_GOLD, CX, CY, 0.7)
    d = ImageDraw.Draw(img)
    s = ease_back(t / 0.6); r = 240 * s; cy = CY
    d.ellipse((CX - r - 18, cy - r - 18, CX + r + 18, cy + r + 18), fill=(110, 78, 48))
    d.ellipse((CX - r, cy - r, CX + r, cy + r), fill=(240, 232, 214))
    for k in range(12):
        a = math.radians(k * 30)
        r1 = r * (0.82 if k % 3 else 0.74)
        d.line((CX + math.sin(a) * r1, cy - math.cos(a) * r1, CX + math.sin(a) * r * 0.92, cy - math.cos(a) * r * 0.92), fill=(60, 50, 40), width=8 if k % 3 == 0 else 4)
    # hands spin then stop abruptly with shake at stop
    stop = 1.8
    tt = min(t, stop)
    mang = tt * 900
    hang = tt * 75 + 300
    shake = math.sin(t * 60) * 3 * max(0, 1 - (t - stop) * 3) if t > stop else 0
    for ang, ln, wd, col in ((hang, 0.5, 14, (40, 34, 28)), (mang + shake, 0.75, 9, (40, 34, 28))):
        a = math.radians(ang)
        d.line((CX, cy, CX + math.sin(a) * r * ln, cy - math.cos(a) * r * ln), fill=col, width=wd)
    d.ellipse((CX - 16, cy - 16, CX + 16, cy + 16), fill=(196, 72, 64))

def il_door(img, t, T):
    d = ImageDraw.Draw(img)
    s = ease(t / 0.6); cy = CY + 70
    dw, dh = 260, 420
    x0, y0 = CX - dw/2, cy - dh/2 - 40
    paste_c(img, GLOW_GOLD, CX, cy - 40, 0.9 * s)
    d.rectangle((x0 - 24, y0 + dw/2, x0 + dw + 24, y0 + dh + 10), fill=(70, 55, 45))
    d.pieslice((x0 - 24, y0 - 24, x0 + dw + 24, y0 + dw + 24), 180, 360, fill=(70, 55, 45))
    d.rectangle((x0, y0 + dw/2, x0 + dw, y0 + dh), fill=(255, 226, 160))
    d.pieslice((x0, y0, x0 + dw, y0 + dw), 180, 360, fill=(255, 226, 160))
    # light on floor
    floor = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(floor)
    fd.polygon([(x0, y0 + dh), (x0 + dw, y0 + dh), (x0 + dw + 260, y0 + dh + 300), (x0 - 260, y0 + dh + 300)], fill=(255, 220, 150, 60))
    img.alpha_composite(floor.filter(ImageFilter.GaussianBlur(20)))
    d = ImageDraw.Draw(img)
    # silhouette walking toward the door (getting smaller)
    p = min(1, t / max(T, 0.1))
    fx = CX + 30 * math.sin(p * 3)
    fy = y0 + dh + 270 - 230 * p
    sc = 1.3 - 0.75 * p
    step = math.sin(t * 7) * 14 * sc
    col = (12, 12, 22)
    d.ellipse((fx - 26*sc, fy - 200*sc, fx + 26*sc, fy - 148*sc), fill=col)
    d.rounded_rectangle((fx - 34*sc, fy - 150*sc, fx + 34*sc, fy - 50*sc), int(18*sc), fill=col)
    d.line((fx - 14*sc, fy - 55*sc, fx - 14*sc - step, fy), fill=col, width=max(2, int(22*sc)))
    d.line((fx + 14*sc, fy - 55*sc, fx + 14*sc + step, fy), fill=col, width=max(2, int(22*sc)))

def il_candle(img, t, T):
    d = ImageDraw.Draw(img)
    s = ease_back(t / 0.6); cy = CY + 60
    p = min(1, t / max(T, 0.1))
    fl = 1 + 0.08 * math.sin(t * 13) + 0.05 * math.sin(t * 29)
    hgt = 300 * s * (1 - 0.35 * p)  # candle melts
    top = cy + 150 - hgt
    paste_c(img, GLOW_GOLD, CX, top - 60, 0.85 * fl)
    d.rounded_rectangle((CX - 70*s, top, CX + 70*s, cy + 150), 18, fill=(236, 226, 205))
    d.ellipse((CX - 70*s, top - 16, CX + 70*s, top + 16), fill=(250, 242, 225))
    d.line((CX, top, CX, top - 26), fill=(40, 30, 20), width=5)
    fh = 110 * fl * s
    d.polygon([(CX - 26*s, top - 30), (CX, top - 30 - fh), (CX + 26*s, top - 30)], fill=(255, 200, 90))
    d.ellipse((CX - 26*s, top - 58, CX + 26*s, top - 4), fill=(255, 200, 90))
    d.ellipse((CX - 12*s, top - 46, CX + 12*s, top - 12), fill=(255, 245, 210))
    d.rounded_rectangle((CX - 130*s, cy + 150, CX + 130*s, cy + 180), 12, fill=(110, 78, 48))

def il_mosque(img, t, T):
    d = ImageDraw.Draw(img)
    s = ease(t / 0.8)
    mx, my = CX + 200, 470 - 40 * s
    paste_c(img, GLOW_SMALL, mx, my, 0.9 * s)
    m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
    md.ellipse((mx - 80, my - 80, mx + 80, my + 80), fill=255)
    md.ellipse((mx - 45, my - 105, mx + 115, my + 55), fill=0)
    img.paste(Image.new("RGBA", (W, H), (250, 236, 196, 255)), (0, 0), m)
    d = ImageDraw.Draw(img)
    col = (26, 28, 52)
    base = 900
    up = (1 - s) * 200
    d.rectangle((CX - 300, base - 200 + up, CX + 300, base + 130), fill=col)
    d.pieslice((CX - 170, base - 380 + up, CX + 170, base - 40 + up), 180, 360, fill=col)
    d.rectangle((CX - 170, base - 212 + up, CX + 170, base - 190 + up), fill=col)
    d.polygon([(CX - 14, base - 380 + up), (CX + 14, base - 380 + up), (CX, base - 440 + up)], fill=col)
    for k in (-1, 1):
        x = CX + k * 360
        d.rectangle((x - 26, base - 420 + up, x + 26, base + 130), fill=col)
        d.polygon([(x - 34, base - 420 + up), (x + 34, base - 420 + up), (x, base - 520 + up)], fill=col)
    for k in (-2, -1, 1, 2):  # lit windows
        x = CX + k * 110
        d.rounded_rectangle((x - 22, base - 120 + up, x + 22, base - 30 + up), 20, fill=(255, 205, 110))
    d.rounded_rectangle((CX - 40, min(base + 10 + up, base + 100), CX + 40, base + 130), 30, fill=(255, 215, 130))

def il_cta(img, t, T):
    d = ImageDraw.Draw(img)
    s = ease_back(t / 0.5)
    cy = CY + math.sin(t * 2.4) * 12
    w, h = 420 * s, 300 * s
    paste_c(img, GLOW_GOLD, CX, cy, 0.6)
    d.rounded_rectangle((CX - w/2, cy - h/2, CX + w/2, cy + h/2), int(60*s) + 1, fill=YEL)
    d.polygon([(CX - 60*s, cy + h/2 - 5), (CX + 20*s, cy + h/2 - 5), (CX - 90*s, cy + h/2 + 90*s)], fill=YEL)
    for k in (-1, 0, 1):
        bob = math.sin(t * 6 - k) * 10 * s
        d.ellipse((CX + k*110*s - 28*s, cy - 28*s + bob, CX + k*110*s + 28*s, cy + 28*s + bob), fill=(40, 30, 10))

