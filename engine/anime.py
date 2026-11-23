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

def build(S, work, outdir, pretty, RL):
    """RL = modul reel (scene_info, build_audio)."""
    hf = f"{work}/hf"
    if os.path.exists(hf): shutil.rmtree(hf)
    os.makedirs(hf)
    scenes, pos = [], 0.0
    for i, sc in enumerate(S["scenes"]):
        info = RL.scene_info(S, work, i)
        d = {k: v for k, v in sc.items() if k not in ("text", "hl")}
        d.update(start=round(pos, 4), T=round(info["T"], 4), voEnd=round(pos + RL.LEAD + info["dur"], 4),
                 chunks=[[_cap_html(c), round(pos + t, 4)] for c, t in info["chunks"]])
        scenes.append(d); pos += info["T"]
    data = {"head": f'{S["series"].upper()}  ·  PART {S["part"]}', "total": round(pos, 4),
            "chars": S.get("chars", {}), "scenes": scenes}
    RL.build_audio(S, work, intro=0)
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
    r = subprocess.run("npx --yes hyperframes@latest render", shell=True, cwd=proj)
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
