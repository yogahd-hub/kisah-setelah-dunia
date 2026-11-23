"""Periksa naskah sebelum render. Pesan error dibuat mudah dipahami.
    python engine/check.py scripts/s1-ep05.json [file lain...]"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ILS = ["duo", "solo", "dreams", "night", "choice", "angel", "grave", "crowd", "scale", "sun", "gate", "wall", "eye",
       "sunwest", "city", "clock", "hourglass", "calendar", "globe", "door", "candle", "mosque", "cta"]
EXPR = ["neutral", "smile", "worry", "shock", "cry"]

def check(path):
    errs, warns = [], []
    try:
        S = json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"Format JSON rusak di baris {e.lineno}, kolom {e.colno}: {e.msg}. "
                "Biasanya karena koma atau tanda kutip yang kurang/lebih."], []
    for k in ("series", "part", "title", "scenes"):
        if k not in S: errs.append(f"Field '{k}' belum ada.")
    if errs: return errs, warns
    if "no" not in S: warns.append("Field 'no' (nomor urut tayang) belum ada; nama file tidak akan bernomor.")
    if "hook" not in S: warns.append("Field 'hook' belum ada; cover tanpa kalimat hook.")
    sc_list = S["scenes"]
    if not 3 <= len(sc_list) <= 14: warns.append(f"Jumlah scene {len(sc_list)} (ideal 7-9).")
    words = 0
    for i, sc in enumerate(sc_list):
        n = f"Scene {i + 1}"
        if sc.get("il") not in ILS: errs.append(f"{n}: ilustrasi '{sc.get('il')}' tidak dikenal. Pilihan: {', '.join(ILS)}.")
        t = sc.get("text", "")
        if not t.strip(): errs.append(f"{n}: 'text' kosong.")
        words += len(t.split())
        if re.search(r"\d", t): errs.append(f"{n}: ada angka di text ('{t[:40]}...'). Tulis angka dengan huruf.")
        if t.strip() and t.strip()[-1] not in ".?!": warns.append(f"{n}: text sebaiknya diakhiri titik atau tanda tanya.")
        if "[" in t or "]" in t: errs.append(f"{n}: jangan ada instruksi dalam kurung siku di text.")
        for h in sc.get("hl", []):
            if h.lower() not in t.lower(): warns.append(f"{n}: kata hl '{h}' tidak ada di text, tidak akan dikuningkan.")
        for k in ("expr", "expr2"):
            if k in sc and sc[k] not in EXPR: errs.append(f"{n}: {k} '{sc[k]}' tidak dikenal. Pilihan: {', '.join(EXPR)}.")
        if sc.get("who") not in (None, "A", "B"): errs.append(f"{n}: who harus 'A' atau 'B'.")
        if "card" in sc:
            c = sc["card"]
            if not isinstance(c, list) or len(c) < 2: errs.append(f"{n}: card harus [arti, sumber] atau [arti, sumber, \"HADITS\"].")
            elif len(c[0].split()) > 30: warns.append(f"{n}: arti di card terlalu panjang ({len(c[0].split())} kata), maks ±25.")
        if len(sc.get("kw", "")) > 22: warns.append(f"{n}: kw terlalu panjang, maks ±18 huruf.")
    if sc_list and sc_list[-1].get("il") != "cta": warns.append("Scene terakhir sebaiknya memakai il 'cta'.")
    if words > 170: warns.append(f"Narasi {words} kata, kemungkinan lebih dari 80 detik.")
    return errs, warns

if __name__ == "__main__":
    bad = False
    for p in sys.argv[1:]:
        errs, warns = check(p)
        for w in warns: print(f"::warning file={p}::{w}")
        for e in errs: print(f"::error file={p}::{e}")
        print(f"{p}: {'GAGAL' if errs else 'OK'} ({len(errs)} error, {len(warns)} peringatan)")
        bad |= bool(errs)
    sys.exit(1 if bad else 0)
