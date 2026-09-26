#!/usr/bin/env python3
# onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
"""probe.py — read a composition's motion in numbers: what is on screen, how it moves, what carries across beats.

  python3 scripts/probe.py comp.html                          # continuity + curves summary
  python3 scripts/probe.py comp.html --fps 30 --out probe/    # also probe/tracks.json and probe/curves.png

No annotations needed. After every __seek(t) the probe lists what is visible and where:
  DOM     img / video / svg / canvas / text-bearing elements / painted boxes, by transformed rect and
          effective opacity (display, visibility, every ancestor's opacity);
  canvas  every drawImage / fillText / fill / stroke, located through the context transform (the hooks are
          installed before the page's own scripts run). Full-canvas fills count as ground. Clip paths are not
          tracked: a line still hidden by its mask counts as visible.
A page that defines window.__track(t) → {id: [x, y] | {x, y, w, h, op}} is read from that instead.

Identity: a DOM element is its path (image sources with frame numbers folded, so footage stays one element);
a canvas draw is its image source / text / fill style, numbered by draw order within the frame.

continuity  A boundary is a 0.4 s window in which most of the on-screen area changes identity (fades through
            the ground are bridged). It is CARRIED when something survives it and visibly moves or scales —
            the hand, the subject, a container becoming the next thing; ANCHORED when the only survivor is large
            and unchanged (a frame whose content swaps); BARE when nothing survives. Exempt: boundaries inside a
            burst of hard cuts (>= 3 cuts within 1.5 s — staccato hits), the last 1.2 s (end card), and times in
            window.__meta.cuts. score = (carried + anchored/2) / boundaries considered.
curves      Each element's track is cut into moves. Per move: path, t80 (share of the move's duration spent
            before 80 % of the path is covered), peak px/frame at --fps (normalised to 1920 wide), overshoot.
            Film: the peak, and the share of all travel made on soft curves (t80 >= .55).
framing     What the page says must stay in frame — window.__meta.inFrame = {id: [t0, t1] | [t0, t1, 'whole']} — read
            from its __track boxes, which a page with a camera reports on screen: the sampled times each id was
            entirely off frame, or for 'whole', not wholly inside.

verify_promo.py --comp runs this and turns the numbers into legs; gallery.py uses it for the speed graphs.
"""
import argparse, asyncio, json, math, os, sys
import numpy as np
from playwright.async_api import async_playwright

TRACKER_JS = r"""
(() => {
  if (window.__omTrack) return;
  const P = CanvasRenderingContext2D.prototype, draws = [], counts = new Map(), pb = new WeakMap();
  const fold = s => { s = String(s || ''); const q = s.indexOf('?'); if (q >= 0) s = s.slice(0, q); try { s = decodeURIComponent(s); } catch (e) {}
    return s.split('/').slice(-2).join('/').replace(/\d{2,}(?=\.[a-z0-9]+$)/i, '#'); };
  const idOf = base => { const n = counts.get(base) || 0; counts.set(base, n + 1); return n ? base + '#' + n : base; };
  const dev = (ctx, pts) => { const m = ctx.getTransform(); return pts.map(([x, y]) => [m.a * x + m.c * y + m.e, m.b * x + m.d * y + m.f]); };
  const bbox = pts => { let b = [Infinity, Infinity, -Infinity, -Infinity]; for (const [X, Y] of pts) { b = [Math.min(b[0], X), Math.min(b[1], Y), Math.max(b[2], X), Math.max(b[3], Y)]; } return b; };
  const rect = (x, y, w, h) => [[x, y], [x + w, y], [x, y + h], [x + w, y + h]];
  const push = (ctx, base, b, kind) => {
    const cv = ctx.canvas; if (!cv || !cv.isConnected || !b || !(b[2] > b[0]) || !(b[3] > b[1])) return;
    if (kind !== 'img' && b[2] - b[0] >= 0.9 * cv.width && b[3] - b[1] >= 0.9 * cv.height) return;   // full-canvas fills are ground; a full-frame image is content
    draws.push({ id: idOf(base), b, alpha: ctx.globalAlpha, cv, kind });
  };
  const extend = (ctx, pts) => { const b = pb.get(ctx), n = bbox(dev(ctx, pts));
    pb.set(ctx, b ? [Math.min(b[0], n[0]), Math.min(b[1], n[1]), Math.max(b[2], n[2]), Math.max(b[3], n[3])] : n); };
  const wrap = (name, fn) => { const orig = P[name]; if (!orig) return;
    P[name] = function (...a) { try { fn(this, a); } catch (e) {} return orig.apply(this, a); }; };
  wrap('drawImage', (ctx, a) => {
    const img = a[0], iw = img.naturalWidth || img.videoWidth || img.width || 0, ih = img.naturalHeight || img.videoHeight || img.height || 0;
    let r, key = '';
    if (a.length === 3) r = rect(a[1], a[2], iw, ih); else if (a.length === 5) r = rect(a[1], a[2], a[3], a[4]);
    else { r = rect(a[5], a[6], a[7], a[8]); key = '@' + Math.round(a[1]) + ',' + Math.round(a[2]); }
    const src = img.currentSrc || img.src;
    push(ctx, (src ? 'img:' + fold(src) : (img.tagName || 'bitmap').toLowerCase()) + key, bbox(dev(ctx, r)), 'img');
  });
  const textRect = (ctx, s, x, y) => {
    const w = ctx.measureText(s).width, m = /(\d+(?:\.\d+)?)px/.exec(ctx.font), size = m ? parseFloat(m[1]) : 16, al = ctx.textAlign, bl = ctx.textBaseline;
    const xl = al === 'center' ? x - w / 2 : (al === 'right' || al === 'end') ? x - w : x;
    const yt = bl === 'middle' ? y - size / 2 : (bl === 'top' || bl === 'hanging') ? y : (bl === 'bottom' || bl === 'ideographic') ? y - size : y - size * 0.8;
    return rect(xl, yt, w, size);
  };
  for (const name of ['fillText', 'strokeText']) wrap(name, (ctx, a) => push(ctx, 'text:' + String(a[0]).slice(0, 40), bbox(dev(ctx, textRect(ctx, String(a[0]), a[1], a[2]))), 'text'));
  wrap('beginPath', ctx => pb.delete(ctx));
  wrap('moveTo', (ctx, a) => extend(ctx, [[a[0], a[1]]]));
  wrap('lineTo', (ctx, a) => extend(ctx, [[a[0], a[1]]]));
  wrap('bezierCurveTo', (ctx, a) => extend(ctx, [[a[0], a[1]], [a[2], a[3]], [a[4], a[5]]]));
  wrap('quadraticCurveTo', (ctx, a) => extend(ctx, [[a[0], a[1]], [a[2], a[3]]]));
  wrap('arcTo', (ctx, a) => extend(ctx, [[a[0], a[1]], [a[2], a[3]]]));
  wrap('arc', (ctx, a) => extend(ctx, rect(a[0] - a[2], a[1] - a[2], 2 * a[2], 2 * a[2])));
  wrap('ellipse', (ctx, a) => extend(ctx, rect(a[0] - a[2], a[1] - a[3], 2 * a[2], 2 * a[3])));
  for (const name of ['rect', 'roundRect']) wrap(name, (ctx, a) => extend(ctx, rect(a[0], a[1], a[2], a[3])));
  wrap('fill', (ctx, a) => { if (!(a[0] instanceof Path2D)) push(ctx, 'shape:' + String(ctx.fillStyle), pb.get(ctx), 'shape'); });
  wrap('stroke', (ctx, a) => { if (!(a[0] instanceof Path2D)) push(ctx, 'line:' + String(ctx.strokeStyle), pb.get(ctx), 'shape'); });
  wrap('fillRect', (ctx, a) => push(ctx, 'shape:' + String(ctx.fillStyle), bbox(dev(ctx, rect(a[0], a[1], a[2], a[3]))), 'shape'));
  wrap('strokeRect', (ctx, a) => push(ctx, 'line:' + String(ctx.strokeStyle), bbox(dev(ctx, rect(a[0], a[1], a[2], a[3]))), 'shape'));

  const snapshot = () => {
    const VW = innerWidth, VH = innerHeight, out = [], memo = new Map();
    const opac = el => {
      if (!el || el.nodeType !== 1) return 1; if (memo.has(el)) return memo.get(el);
      const cs = getComputedStyle(el); let o = (cs.display === 'none' || cs.visibility === 'hidden') ? 0 : parseFloat(cs.opacity);
      if (o > 0) o *= opac(el.parentElement); memo.set(el, o); return o;
    };
    const pathOf = el => {
      const parts = [];
      for (let e = el; e && e.nodeType === 1 && e !== document.body && e !== document.documentElement; e = e.parentElement) {
        let p = e.tagName.toLowerCase(); if (e.id) { parts.unshift(p + '#' + e.id); break; }
        const par = e.parentElement; if (par) { const sib = [...par.children].filter(x => x.tagName === e.tagName); if (sib.length > 1) p += ':' + sib.indexOf(e); }
        if (e.classList.length) p += '.' + e.classList[0]; parts.unshift(p);
      }
      return parts.join('>');
    };
    const add = (id, key, x0, y0, x1, y1, op, kind) => {
      const cx0 = Math.max(0, x0), cy0 = Math.max(0, y0), cx1 = Math.min(VW, x1), cy1 = Math.min(VH, y1);
      if (cx1 <= cx0 || cy1 <= cy0 || op < 0.05) return;
      out.push({ id, key, x: (x0 + x1) / 2, y: (y0 + y1) / 2, w: x1 - x0, h: y1 - y0, vis: (cx1 - cx0) * (cy1 - cy0), op, kind });
    };
    for (const el of document.body.querySelectorAll('*')) {
      const tag = el.tagName.toLowerCase();
      if (tag === 'script' || tag === 'style' || tag === 'link' || tag === 'template' || (tag !== 'svg' && el.closest('svg'))) continue;
      let kind = null, key = '';
      if (tag === 'img' || tag === 'video') { kind = 'img'; key = fold(el.currentSrc || el.src); }
      else if (tag === 'canvas') kind = 'canvas';
      else if (tag === 'svg') kind = 'svg';
      else {
        let own = ''; for (const n of el.childNodes) if (n.nodeType === 3) own += n.textContent;
        own = own.trim();
        if (own) { kind = 'text'; key = own.slice(0, 40); }
        else { const cs = getComputedStyle(el), bg = cs.backgroundColor;
          if ((bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') || cs.backgroundImage !== 'none' || parseFloat(cs.borderTopWidth) > 0 || cs.boxShadow !== 'none') kind = 'box'; }
      }
      if (!kind) continue;
      const r = el.getBoundingClientRect(); if (r.width < 2 || r.height < 2) continue;
      if ((kind === 'box' || kind === 'canvas') && r.width * r.height >= 0.85 * VW * VH) continue;   // backgrounds and full-frame layers are ground
      add(kind + ':' + pathOf(el), key, r.left, r.top, r.right, r.bottom, opac(el), kind);
    }
    for (const d of draws) {
      const r = d.cv.getBoundingClientRect(), sx = r.width / d.cv.width, sy = r.height / d.cv.height;
      add('draw:' + d.id, '', r.left + d.b[0] * sx, r.top + d.b[1] * sy, r.left + d.b[2] * sx, r.top + d.b[3] * sy, d.alpha * opac(d.cv), d.kind);
    }
    return out;
  };
  window.__omTrack = { reset() { draws.length = 0; counts.clear(); }, snapshot };
})();
"""

SAMPLE_AUTO = "async (t) => { window.__omTrack.reset(); await window.__seek(t); return window.__omTrack.snapshot(); }"
SAMPLE_ANNOTATED = """async (t) => { await window.__seek(t); const r = window.__track(t) || {};
  return Object.entries(r).map(([id, v]) => Array.isArray(v)
    ? { id, key: '', x: v[0], y: v[1], w: 0, h: 0, vis: 0, op: 1, kind: 'track' }
    : { id, key: v.key || '', x: v.x, y: v.y, w: v.w || 0, h: v.h || 0, vis: (v.w || 0) * (v.h || 0), op: v.op == null ? 1 : v.op, kind: 'track' }); }"""


def comp_url(comp):
    return comp if comp.startswith(("file://", "http://", "https://")) else "file://" + os.path.abspath(comp)


async def collect_page(pg, comp, fps=30, t0=0.0, t1=None, query=""):
    """Sample an already-open page (gallery.py reuses one browser across demos)."""
    await pg.goto(comp_url(comp) + query)
    await pg.evaluate("window.__ready")
    meta = await pg.evaluate("window.__meta || {}")
    annotated = await pg.evaluate("typeof window.__track === 'function'")
    dur = float(t1 if t1 is not None else meta.get("dur", 15))
    n = int(round((dur - t0) * fps))
    fn = SAMPLE_ANNOTATED if annotated else SAMPLE_AUTO
    samples, failed = [], []
    for i in range(n + 1):
        t = round(t0 + i / fps, 6)
        try:
            items = await pg.evaluate(fn, t)
        except Exception as e:                                   # a frame the renderer would choke on too: keep what was drawn, report it
            failed.append((t, str(e).splitlines()[0][:120]))
            items = [] if annotated else await pg.evaluate("window.__omTrack.snapshot()")
        samples.append((t, items))
    return {"comp": comp, "meta": meta, "fps": fps, "dur": dur, "annotated": annotated, "samples": samples, "failed": failed}


async def collect(comp, fps=30, t0=0.0, t1=None, width=1920, height=1080):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": width, "height": height})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.add_init_script(TRACKER_JS)
        res = await collect_page(pg, comp, fps, t0, t1)
        await b.close()
    res.update(W=width, H=height, errors=errs)
    return res


# ─────────────────────────────── continuity ───────────────────────────────
def _weight(it, area):
    return it["vis"] * it["op"] / area


def _jaccard(A, B, area):
    inter = union = 0.0
    for k in set(A) | set(B):
        wa = _weight(A[k], area) if k in A else 0.0
        wb = _weight(B[k], area) if k in B else 0.0
        if k in A and k in B and A[k]["key"] == B[k]["key"]:
            inter += min(wa, wb); union += max(wa, wb)
        else:
            union += wa + wb
    return inter / union if union > 0 else 1.0


def short(i):
    head, _, tail = i.partition(":")
    return head + ":" + tail.split(">")[-1][:34]


def continuity(res, dt=0.4, j_max=0.2, cut_j=0.3, min_content=0.004):
    W, H, fps, dur = res["W"], res["H"], res["fps"], res["dur"]
    area = float(W * H)
    S = [{it["id"]: it for it in items} for _, items in res["samples"]]
    content = [sum(_weight(it, area) for it in s.values()) for s in S]
    lag, bridge, n = max(1, int(round(dt * fps))), int(1.5 * fps), len(S)

    # hard cuts between consecutive samples → bursts
    cuts = [i for i in range(n - 1) if content[i] >= min_content and content[i + 1] >= min_content and _jaccard(S[i], S[i + 1], area) < cut_j]
    bursts, group = [], []
    for i in cuts:
        if group and (i - group[-1]) / fps > 0.6:              # gaps <= .6 s, so any 3 cuts in a group fall inside 1.5 s
            if len(group) >= 3:
                bursts.append((group[0] / fps - 0.25, group[-1] / fps + 0.25))
            group = []
        group.append(i)
    if len(group) >= 3: bursts.append((group[0] / fps - 0.25, group[-1] / fps + 0.25))

    # replacement windows, merged into boundaries
    events = []
    for i in range(n - lag):
        if content[i] < min_content:
            continue
        j = i + lag
        while j < n - 1 and content[j] < min_content and j - i < bridge:
            j += 1
        if content[j] < min_content:
            continue
        J = _jaccard(S[i], S[j], area)
        if J >= j_max:
            continue
        if events and i <= events[-1]["span"][1]:
            ev = events[-1]; ev["span"][1] = j
            if J < ev["J"]:
                ev.update(i=i, j=j, J=J)
        else:
            events.append({"i": i, "j": j, "J": J, "span": [i, j]})

    declared = [float(c) for c in (res["meta"].get("cuts") or [])]
    diag = math.hypot(W, H)
    for ev in events:
        A, B = S[ev["i"]], S[ev["j"]]
        ev["t"] = round((ev["i"] + ev["j"]) / 2 / fps, 2)
        strong, weak = [], []
        for k in set(A) & set(B):
            a, b = A[k], B[k]
            if min(a["op"], b["op"]) < 0.15:
                continue
            move = math.hypot(b["x"] - a["x"], b["y"] - a["y"]) / diag
            scale = abs(math.log(math.sqrt(max(b["w"] * b["h"], 1.0)) / math.sqrt(max(a["w"] * a["h"], 1.0))))
            big = min(a["vis"], b["vis"]) / area
            if move >= 0.02 or scale >= 0.1:
                strong.append((max(move, scale), k))
            elif big >= 0.03 and a["key"] == b["key"]:
                weak.append((big, k))
        ev["carriers"] = [short(k) for _, k in sorted(strong, reverse=True)[:3]]
        ev["anchors"] = [short(k) for _, k in sorted(weak, reverse=True)[:2]]
        ev["kind"] = "carried" if strong else "anchored" if weak else "bare"
        tb = ev["t"]
        ev["exempt"] = ("burst" if any(a0 <= tb <= a1 for a0, a1 in bursts) else
                        "end" if tb >= dur - 1.2 else
                        "declared" if any(abs(tb - c) <= 0.25 for c in declared) else "")
        top = lambda s: [short(k) for k, _ in sorted(s.items(), key=lambda kv: -_weight(kv[1], area))[:2]]
        ev["before"], ev["after"] = top(A), top(B)
    considered = [e for e in events if not e["exempt"]]
    score = 1.0 if not considered else sum(1.0 if e["kind"] == "carried" else 0.5 if e["kind"] == "anchored" else 0.0 for e in considered) / len(considered)
    return {"score": round(score, 2), "events": events, "considered": len(considered),
            "bare": sum(e["kind"] == "bare" for e in considered), "cuts": len(cuts), "bursts": [(round(a, 2), round(b, 2)) for a, b in bursts]}


# ─────────────────────────────── curves ───────────────────────────────
def moves_of(track, fps, W, vmin=0.8, min_path=30.0, min_steps=4, gap=2):
    """track: {sample_index: item}. Returns the moves along this element's centre (px normalised to 1920 wide)."""
    runs, cur = [], []
    for i in sorted(track):
        if track[i]["op"] < 0.15 or (cur and i != cur[-1] + 1):
            if cur:
                runs.append(cur)
            cur = [] if track[i]["op"] < 0.15 else [i]
            continue
        cur.append(i)
    if cur:
        runs.append(cur)
    norm, out = 1920.0 / W, []
    for run in runs:
        if len(run) < min_steps + 1:
            continue
        xs = np.array([track[i]["x"] for i in run], float)
        ys = np.array([track[i]["y"] for i in run], float)
        ds = np.array([math.sqrt(max(track[i]["w"] * track[i]["h"], 1.0)) for i in run], float)
        step = (np.hypot(np.diff(xs), np.diff(ys)) + 0.5 * np.abs(np.diff(ds))) * norm
        for k in range(len(step)):                              # a lone jump between calm neighbours is a teleport, not travel
            prev = step[k - 1] if k > 0 else 0.0
            nxt = step[k + 1] if k + 1 < len(step) else 0.0
            if step[k] > 60 and prev < 0.1 * step[k] and nxt < 0.1 * step[k]:
                step[k] = 0.0
        active = step >= vmin
        k = 0
        while k < len(step):
            if not active[k]:
                k += 1; continue
            a = b = k
            while b < len(step):
                if active[b]:
                    b += 1; continue
                nxt = b
                while nxt < len(step) and not active[nxt] and nxt - b < gap:
                    nxt += 1
                if nxt < len(step) and active[nxt]:
                    b = nxt; continue
                break
            k = b
            path = step[a:b]; L = float(path.sum())
            if b - a < min_steps or L < min_path:
                continue
            k80 = int(np.searchsorted(np.cumsum(path), 0.8 * L)) + 1
            net = np.array([xs[b] - xs[a], ys[b] - ys[a]]); nl = float(np.hypot(*net)); over = 0.0
            if nl > 20:
                u = net / nl
                proj = (xs[a:b + 1] - xs[a]) * u[0] + (ys[a:b + 1] - ys[a]) * u[1]
                over = max(0.0, float(proj.max() - proj[-1]) / nl)
            out.append({"t0": round(run[a] / fps, 3), "t1": round(run[b] / fps, 3), "path": round(L, 1), "t80": round(k80 / (b - a), 3),
                        "peak": round(float(path.max()), 1), "overshoot": round(over, 3)})
    return out


def curves(res, soft_t80=0.55):
    tracks = {}
    for i, (_, items) in enumerate(res["samples"]):
        for it in items:
            tracks.setdefault(it["id"], {})[i] = it
    moves = []
    for k, tr in tracks.items():
        for m in moves_of(tr, res["fps"], res["W"]):
            m["id"] = k
            moves.append(m)
    moves.sort(key=lambda m: -m["path"])
    total = sum(m["path"] for m in moves)
    soft = sum(m["path"] for m in moves if m["t80"] >= soft_t80) / total if total else 0.0
    order = sorted(moves, key=lambda m: m["t80"])
    acc, med = 0.0, None
    for m in order:
        acc += m["path"]
        if med is None and acc >= total / 2:
            med = m["t80"]
    top = max(moves, key=lambda m: m["peak"]) if moves else None
    return {"moves": moves, "tracks": tracks, "peak": top["peak"] if top else 0.0, "peak_at": (short(top["id"]), top["t0"]) if top else None,
            "soft_share": round(soft, 2), "t80_median": med, "count": len(moves)}


def plot_speeds(res, cv, path, title="", times=None, top=8, size=(19.2, 3.2)):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fps, norm = res["fps"], 1920.0 / res["W"]
    ranked, seen = [], set()
    for m in cv["moves"]:
        if m["id"] not in seen:
            seen.add(m["id"]); ranked.append(m["id"])
        if len(ranked) >= top:
            break
    fig, ax = plt.subplots(figsize=size, dpi=100)
    fig.patch.set_facecolor("#f8f8f6"); ax.set_facecolor("#f8f8f6")
    for idx, k in enumerate(ranked):
        tr = cv["tracks"][k]; ii = sorted(tr); ts, vs = [], []
        for a, b in zip(ii, ii[1:]):
            if b != a + 1 or min(tr[a]["op"], tr[b]["op"]) < 0.15:
                ts.append(np.nan); vs.append(np.nan); continue
            d = math.hypot(tr[b]["x"] - tr[a]["x"], tr[b]["y"] - tr[a]["y"]) + 0.5 * abs(math.sqrt(max(tr[b]["w"] * tr[b]["h"], 1)) - math.sqrt(max(tr[a]["w"] * tr[a]["h"], 1)))
            ts.append(b / fps); vs.append(d * norm)
        ax.plot(ts, vs, lw=1.6, label=short(k))
    for m in cv["moves"][:6]:
        ax.annotate(f"t80 {m['t80']:.2f}", (m["t0"], m["peak"]), fontsize=8, color="#555", xytext=(2, 2), textcoords="offset points")
    for t in (times or []):
        ax.axvline(t, color="#c9c9c4", lw=0.8, zorder=0)
    ax.set_xlim(0, res["dur"]); ax.set_ylabel(f"px / frame @{fps}"); ax.set_xlabel("s")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper right", fontsize=7, frameon=False, ncol=2)
    if title:
        ax.set_title(title, loc="left", fontsize=10)
    fig.tight_layout(); fig.savefig(path, facecolor=fig.get_facecolor()); plt.close(fig)


def report(res, ct, cv):
    print(f"\n{os.path.basename(res['comp'])} — {len(res['samples'])} samples at {res['fps']} fps, {len(cv['tracks'])} tracked elements"
          f" ({'__track' if res['annotated'] else 'auto'}){'; page errors: ' + '; '.join(res['errors'][:2]) if res.get('errors') else ''}")
    if res.get("failed"):
        print(f"  !! __seek threw at {len(res['failed'])} samples, first at t={res['failed'][0][0]}: {res['failed'][0][1]}")
    kinds = [e["kind"] for e in ct["events"] if not e["exempt"]]
    print(f"continuity  score {ct['score']:.2f}  — {ct['considered']} boundaries: {kinds.count('carried')} carried, {kinds.count('anchored')} anchored, "
          f"{kinds.count('bare')} bare; {len(ct['events']) - ct['considered']} exempt; hard cuts {ct['cuts']}, bursts {ct['bursts']}")
    for e in ct["events"]:
        why = e["exempt"] or e["kind"]
        via = ", ".join(e["carriers"] or e["anchors"]) or "—"
        print(f"  t={e['t']:6.2f}  J {e['J']:.2f}  {why:9} via {via:48.48}  before {', '.join(e['before'])} | after {', '.join(e['after'])}")
    if cv["peak_at"]:
        print(f"curves      peak {cv['peak']:.0f} px/frame ({cv['peak_at'][0]} at {cv['peak_at'][1]:.2f} s) · travel on soft curves {cv['soft_share'] * 100:.0f} %"
              f" · median t80 {cv['t80_median']:.2f} · {cv['count']} moves")
        for m in cv["moves"][:8]:
            print(f"  {short(m['id']):40.40} {m['t0']:6.2f}–{m['t1']:5.2f} s  path {m['path']:6.0f}  t80 {m['t80']:.2f}  peak {m['peak']:5.0f}  overshoot {m['overshoot']:.2f}")
    else:
        print("curves      nothing moved")


def framing(res):
    """Per id in window.__meta.inFrame ({id: [t0, t1] | [t0, t1, 'whole']}): the sampled times inside its window when its
    box was entirely off frame — or, for 'whole', not wholly inside. Samples where the id isn't drawn don't count."""
    spec = (res.get("meta") or {}).get("inFrame") or {}
    W, H, out = res.get("W", 1920), res.get("H", 1080), {}
    for name, win in spec.items():
        t0, t1, whole = float(win[0]), float(win[1]), len(win) > 2 and win[2] == "whole"
        bad, seen = [], 0
        for t, items in res["samples"]:
            if not t0 <= t <= t1:
                continue
            b = next((it for it in items if it["id"] == name and it.get("op", 1) > 0), None)
            if b is None:
                continue
            seen += 1; x0, y0, x1, y1 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]
            off = (x0 < -0.5 or y0 < -0.5 or x1 > W + 0.5 or y1 > H + 0.5) if whole else (x1 < 0 or y1 < 0 or x0 > W or y0 > H)
            if off:
                bad.append(round(t, 3))
        out[name] = {"whole": whole, "window": [t0, t1], "samples": seen, "bad": bad}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comp"); ap.add_argument("--fps", type=int, default=30); ap.add_argument("--out", default=None)
    ap.add_argument("--from", dest="t0", type=float, default=0.0); ap.add_argument("--to", dest="t1", type=float, default=None)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    a = ap.parse_args()
    res = asyncio.run(collect(a.comp, a.fps, a.t0, a.t1, a.width, a.height))
    ct, cv = continuity(res), curves(res)
    report(res, ct, cv)
    for k, v in framing(res).items():
        print(f"framing  {k}: {'wholly ' if v['whole'] else ''}in frame {v['window'][0]:g}–{v['window'][1]:g} s — off at {len(v['bad'])} of {v['samples']} samples{' ' + str(v['bad'][:8]) if v['bad'] else ''}")
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        slim = {k: [[i / res["fps"], round(v["x"], 1), round(v["y"], 1), round(v["w"], 1), round(v["h"], 1), round(v["op"], 3)] for i, v in sorted(tr.items())] for k, tr in cv["tracks"].items()}
        json.dump({"fps": res["fps"], "dur": res["dur"], "continuity": {k: v for k, v in ct.items()}, "moves": cv["moves"], "tracks": slim},
                  open(os.path.join(a.out, "tracks.json"), "w"))
        plot_speeds(res, cv, os.path.join(a.out, "curves.png"), title=os.path.basename(a.comp))
        print(f"\nwrote {a.out}/tracks.json and {a.out}/curves.png")


if __name__ == "__main__":
    main()
