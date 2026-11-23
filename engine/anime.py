"""Mesin gaya ANIME: naskah + voice over -> komposisi HyperFrames (three.js toon) -> MP4.
Dipanggil dari reel.py bila naskah berisi "engine": "anime"."""
import os, json, re, html, shutil, subprocess, glob

HERE = os.path.dirname(os.path.abspath(__file__))

def _cap_html(text):
    out = []
    for i, part in enumerate(text.split("*")):
        part = html.escape(part)
        out.append(f"<b>{part}</b>" if i % 2 else part)
    return "".join(out)

def timeline(S, work, RL, lead=0.4, tail=1.3, card_min=3.8):
    """VO utuh (tidak dipotong per adegan) -> jeda alami seperti orang bicara.
    Batas adegan diletakkan di jeda antar kalimat; waktu teks = waktu kata dari whisper.
    Hanya adegan kartu dalil yang boleh diberi jeda tambahan supaya kartu sempat terbaca."""
    import numpy as np
    wa = json.load(open(f"{work}/vo/words_abs.json"))
    x, sr = RL.load_wav(f"{work}/vo/full.wav")
    x = np.concatenate([np.zeros(int(lead * sr)), x])          # jeda awal supaya kata pertama tidak terpotong
    wa = [[(w, a + lead, b + lead) for w, a, b in ws] for ws in wa]
    L = len(x) / sr; n = len(wa)
    first = [ws[0][1] for ws in wa]; last = [ws[-1][2] for ws in wa]
    bnd = [max(0.0, first[0] - lead)]
    for k in range(1, n):
        mid = (last[k - 1] + first[k]) / 2
        bnd.append(max(last[k - 1], min(mid, first[k] - 0.08)))
    bnd.append(min(L, last[-1] + 0.35))
    pieces, scenes, pos = [], [], 0.0
    for k, sc in enumerate(S["scenes"]):
        a, b = bnd[k], bnd[k + 1]
        seg = x[int(a * sr):int(b * sr)]
        extra = max(0.0, card_min - (b - a)) if "card" in sc else 0.0
        if k == n - 1: extra = max(extra, tail)
        pieces += [seg, np.zeros(int(extra * sr))]
        T = len(seg) / sr + extra
        m = lambda t: round(pos + (t - a), 4)
        al = [(w, m(t0)) for w, t0, _ in wa[k]]
        d = {kk: v for kk, v in sc.items() if kk not in ("text", "hl")}
        d.update(start=round(pos, 4), T=round(T, 4), voEnd=m(last[k]),
                 chunks=[[_cap_html(c), t] for c, t in RL.chunks(al, sc.get("hl", []))])
        scenes.append(d); pos += T
    vo = np.concatenate(pieces)
    SR = 44100
    vo = np.interp(np.arange(int(len(vo) * SR / sr)) * sr / SR, np.arange(len(vo)), vo)
    vo = vo / (np.abs(vo).max() + 1e-9) * 0.9
    RL.finish_mix(vo, SR, [d["start"] for d in scenes], S, f"{work}/mix.wav")
    return scenes, pos

def build(S, work, outdir, pretty, RL):
    """RL = modul reel (load_wav, chunks, finish_mix)."""
    hf = f"{work}/hf"
    if os.path.exists(hf): shutil.rmtree(hf)
    os.makedirs(hf)
    scenes, pos = timeline(S, work, RL)
    data = {"head": f'{S["series"].upper()}  ·  PART {S["part"]}', "total": round(pos, 4),
            "chars": S.get("chars", {}), "scenes": scenes}
    shutil.copy(f"{work}/mix.wav", f"{hf}/mix.wav")
    tpl = open(f"{HERE}/anime_template.html", encoding="utf-8").read()
    open(f"{hf}/index.html", "w", encoding="utf-8").write(tpl.replace("/*DATA*/null", json.dumps(data, ensure_ascii=False)))
    print(f"[anime] komposisi siap: {len(scenes)} adegan, {pos:.1f} detik", flush=True)
    if os.environ.get("ANIME_NO_RENDER"):
        return None
    # proyek HyperFrames: scaffold resmi lalu ganti isinya dengan komposisi kita
    proj = f"{work}/hfproj"
    if os.path.exists(proj): shutil.rmtree(proj)
    subprocess.run("npx --yes hyperframes@latest init hfproj", shell=True, cwd=work)
    os.makedirs(proj, exist_ok=True)
    for f in os.listdir(hf): shutil.copy(f"{hf}/{f}", f"{proj}/{f}")
    before = set(glob.glob(f"{proj}/**/*.mp4", recursive=True))
    subprocess.run("npx --yes hyperframes@latest render --help", shell=True, cwd=proj)   # catat opsi render di log
    extra = os.environ.get("HF_RENDER_ARGS", "")
    r = subprocess.run(f"npx --yes hyperframes@latest render {extra}", shell=True, cwd=proj)
    if r.returncode != 0: raise SystemExit("HyperFrames render gagal")
    mp4s = [p for p in glob.glob(f"{proj}/**/*.mp4", recursive=True) if p not in before and "node_modules" not in p]
    if not mp4s: raise SystemExit("HyperFrames tidak menghasilkan MP4")
    src = max(mp4s, key=os.path.getmtime)
    final = f"{outdir}/{pretty}.mp4"
    # pastikan audio ikut (tempel ulang mix.wav kalau renderer tidak menyertakan audio)
    has_audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", src],
                               capture_output=True, text=True).stdout.strip()
    if has_audio:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-c", "copy", "-movflags", "+faststart", final], check=True)
    else:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-i", f"{work}/mix.wav", "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", final], check=True)
    return final
