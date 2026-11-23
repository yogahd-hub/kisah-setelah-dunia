"""Pratinjau cepat gaya anime: ambil beberapa frame dari komposisi (tanpa render penuh).
Pakai: ANIME_NO_RENDER=1 python engine/reel.py scripts/x.json --no-check   (buat komposisi)
       python engine/preview_anime.py work/x/hf [jumlah_per_adegan]
Hasil: work/x/hf/preview.jpg (lembar kontak)."""
import sys, os, json, re
from PIL import Image
from playwright.sync_api import sync_playwright

hf = sys.argv[1]; per = int(sys.argv[2]) if len(sys.argv) > 2 else 2
html = open(f"{hf}/index.html", encoding="utf-8").read()
data = json.loads(re.search(r"const DATA = (\{.*?\});\n", html).group(1))
times = []
for sc in data["scenes"]:
    for k in range(per):
        times.append(round(sc["start"] + sc["T"] * (0.35 + 0.5 * k / max(1, per - 1)), 3))
chrome = os.environ.get("CHROME", "/usr/bin/google-chrome")
shots = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=chrome, args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"])
    pg = b.new_page(viewport={"width": 540, "height": 960})
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("file://" + os.path.abspath(f"{hf}/index.html"), wait_until="domcontentloaded")
    import base64
    for i, t in enumerate(times):
        # hanya gambar 3D (canvas); teks HTML tidak ikut di pratinjau ini
        d = pg.evaluate(f"(window.__timelines['ksd-anime'].seek({t}, false), document.getElementById('scene').toDataURL('image/png'))")
        f = f"{hf}/_p{i}.png"; open(f, "wb").write(base64.b64decode(d.split(",")[1])); shots.append(f)
    b.close()
    if errs: print("JS error:", errs[:3])
ims = [Image.open(f).resize((270, 480)) for f in shots]
cols = min(6, len(ims)); rows = (len(ims) + cols - 1) // cols
sheet = Image.new("RGB", (cols * 270, rows * 480))
for i, im in enumerate(ims): sheet.paste(im, ((i % cols) * 270, (i // cols) * 480))
sheet.save(f"{hf}/preview.jpg", quality=85)
for f in shots: os.remove(f)
print(f"{hf}/preview.jpg", [f"{t:.1f}" for t in times])
