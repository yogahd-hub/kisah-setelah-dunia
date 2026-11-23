import re
import numpy as np

def voiced_intervals(x, sr, hop=0.02, min_gap=0.10):
    n = int(hop * sr)
    e = np.array([np.sqrt(np.mean(x[i:i + n] ** 2)) for i in range(0, len(x) - n, n)])
    db = 20 * np.log10(e + 1e-9)
    thr = max(-42, db.max() - 32)
    v = db > thr
    iv, s = [], None
    for k, on in enumerate(v):
        if on and s is None: s = k
        if not on and s is not None: iv.append([s, k]); s = None
    if s is not None: iv.append([s, len(v)])
    merged = []
    for a, b in iv:
        if merged and (a - merged[-1][1]) * hop < min_gap: merged[-1][1] = b
        else: merged.append([a, b])
    return [(a * hop, b * hop) for a, b in merged if (b - a) * hop >= 0.06]

def syl(w):
    w = re.sub(r"[^\w]", "", w)
    return max(1, len(re.findall(r"[aiueoAIUEO]+", w))) + 0.25

def prop(words, ivs):
    wts = [syl(w) for w in words]
    tot_v = sum(b - a for a, b in ivs)
    cum = np.cumsum([0] + wts) / sum(wts) * tot_v
    def v2t(v):
        acc = 0
        for a, b in ivs:
            if v <= acc + (b - a) + 1e-9: return a + (v - acc)
            acc += b - a
        return ivs[-1][1]
    return [v2t(cum[k] + 1e-4) for k in range(len(words))]

def _units(scene_texts, level):
    pat = {"comma": r"[,.?!;:]$", "sentence": r"[.?!]$", "scene": r"$^"}[level]
    units = []
    for si, txt in enumerate(scene_texts):
        cur = []
        for w in txt.split():
            cur.append(w)
            if re.search(pat, w): units.append((si, cur)); cur = []
        if cur: units.append((si, cur))
    return units

def _dp(units, ivs):
    P, I = len(units), len(ivs)
    pw = np.array([sum(syl(w) for w in u) for _, u in units]); pw = pw / pw.sum()
    idur = np.array([b - a for a, b in ivs]); tot = idur.sum()
    INF = 1e18
    dp = np.full((P + 1, I + 1), INF); dp[0][0] = 0; bk = {}
    for p in range(1, P + 1):
        for i in range(p, I - (P - p) + 1):
            for j in range(p - 1, i):
                if dp[p - 1][j] >= INF: continue
                c = dp[p - 1][j] + (idur[j:i].sum() / tot - pw[p - 1]) ** 2
                if c < dp[p][i]: dp[p][i] = c; bk[(p, i)] = j
    groups, i = [], I
    for p in range(P, 0, -1):
        j = bk[(p, i)]; groups.append((j, i)); i = j
    return groups[::-1]

def align_scenes(scene_texts, ivs):
    """Returns per scene: list of (word, start_time) and (span_start, span_end), in audio time."""
    for level in ("comma", "sentence", "scene"):
        units = _units(scene_texts, level)
        if len(units) <= len(ivs): break
    else:
        units = None
    out = [[] for _ in scene_texts]; spans = [[None, None] for _ in scene_texts]
    if units is None:  # very few pauses: pure proportional
        words = [(si, w) for si, t in enumerate(scene_texts) for w in t.split()]
        ts = prop([w for _, w in words], ivs)
        for (si, w), t in zip(words, ts): out[si].append((w, t))
        for si in range(len(scene_texts)):
            spans[si] = [out[si][0][1], (out[si + 1][0][1] if si + 1 < len(scene_texts) else ivs[-1][1])]
        return out, spans
    groups = _dp(units, ivs)
    for (si, u), (j, i) in zip(units, groups):
        sub = ivs[j:i]
        out[si] += list(zip(u, prop(u, sub)))
        if spans[si][0] is None: spans[si][0] = sub[0][0]
        spans[si][1] = sub[-1][1]
    return out, spans
