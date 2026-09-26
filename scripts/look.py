#!/usr/bin/env python3
"""look.py — the starting looks: eight colours and three OFL faces, subset and inlined for a file:// comp.

A look is a choice made in the concept round (SKILL.md §2), not a default. Six are measured from accepted films
(looks/looks.json); `from-shot` makes one from the product's own screenshots; either way it is named.

  python3 scripts/look.py list                                    # the looks and the film each came from
  python3 scripts/look.py sheet                                   # → gallery/sheets/looks.png, one tile per look
  python3 scripts/look.py check [mine.json]                       # ink / mute / accent contrast on the ground
  python3 scripts/look.py apply ember cases/my-film/comp.html     # → cases/my-film/look.js
  python3 scripts/look.py apply cases/my-film/look.json cases/my-film/comp.html --text-from strings.json --cjk NotoSansSC.ttf
  python3 scripts/look.py from-shot shot1.png shot2.png --faces paper --out cases/my-film/look.json

In the comp, before its own script:   <script src="look.js"></script>
  DOM      var(--ground) … var(--accent2), font-family: var(--display) / var(--text) / var(--mono),
           var(--display-weight), letter-spacing: var(--display-tracking)
  canvas   ctx.font = LOOK.font('display', 96); ctx.letterSpacing = LOOK.track('display', 96); LOOK.color.ink
  render   window.__ready = LOOK.ready.then(() => { measure(); seek(0); })

Why inlined: render.py loads the comp over file://, where a remote @font-face never arrives and canvas silently
falls back to a system face. apply subsets each face to the glyphs the comp sets (plus printable ASCII, so copy
edits rarely need a re-run) and embeds them as base64 woff2 — tens of KB, not megabytes. Re-run it after copy
changes that add characters; it reports any character a face lacks (CJK needs --cjk).

Faces are SIL OFL 1.1 (looks/fonts/LICENSES.txt). Pinned axes (Archivo Condensed's wdth 62) are instanced at
build time, so canvas and DOM see the same face without font-variation-settings.
"""
import argparse, base64, colorsys, io, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOOKS = ROOT / "looks" / "looks.json"
FONTS = ROOT / "looks" / "fonts"
ROLES = ("display", "text", "mono")
COLORS = ("ground", "deep", "card", "line", "mute", "ink", "accent", "accent2")
TYPO = "“”‘’–—…·×→←↑↓✓•°±%€£"          # common punctuation a comp may set from JS strings built at runtime


def load_db():
    return json.loads(LOOKS.read_text())


def resolve(spec, db):
    """A look by name, or a JSON file holding one look (from-shot's output, or hand-written)."""
    if spec in db["looks"]:
        return dict(db["looks"][spec], name=spec)
    p = pathlib.Path(spec)
    if p.suffix == ".json" and p.exists():
        look = json.loads(p.read_text())
        look.setdefault("name", p.stem)
        missing = [c for c in COLORS if c not in look.get("color", {})] + [r for r in ROLES if r not in look.get("type", {})]
        if missing:
            sys.exit(f"look.py: {p} lacks {', '.join(missing)}")
        return look
    sys.exit(f"look.py: no look '{spec}' — one of {', '.join(db['looks'])}, or a .json file")


# ── colour ────────────────────────────────────────────────────────────────────────────────────────────────────────
def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexc(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in c)


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def mix(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def check(look):
    g = rgb(look["color"]["ground"])
    rows, ok = [], True
    for tok, floor in (("ink", 4.5), ("mute", 3.0), ("accent", 1.8), ("accent2", 1.5)):
        c = contrast(rgb(look["color"][tok]), g)
        flag = "ok" if c >= floor else "LOW"
        ok &= c >= floor or tok.startswith("accent")      # accents are advisory: a yellow on white can be the point
        rows.append(f"    {tok:8s} {look['color'][tok]}  {c:5.2f}:1  (≥ {floor}) {flag}")
    return ok, rows


# ── faces ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def family_of(face):
    return "Look" + re.sub(r"[^A-Za-z0-9]", "", face)


def need_fonttools():
    try:
        import fontTools  # noqa: F401
        import brotli  # noqa: F401
    except ImportError:
        sys.exit("look.py: needs fontTools and brotli — `python3 -m pip install fonttools brotli`")
    import logging
    logging.getLogger("fontTools").setLevel(logging.ERROR)   # "meta NOT subset" and friends


def subset_face(path, pin, chars):
    """→ (woff2 bytes, cmap set). Pins axes first (partial instancing keeps the others variable)."""
    from fontTools.ttLib import TTFont
    from fontTools.subset import Subsetter, Options
    f = TTFont(str(path))
    cmap = set(f.getBestCmap())
    if pin and "fvar" in f:
        from fontTools.varLib import instancer
        axes = {a.axisTag for a in f["fvar"].axes}
        f = instancer.instantiateVariableFont(f, {k: v for k, v in pin.items() if k in axes})
    o = Options()
    o.flavor = "woff2"
    o.layout_features = ["*"]            # tnum for counters, case, ss/cv sets — cheap at this glyph count
    o.name_IDs = ["*"]
    o.notdef_outline = True
    o.drop_tables += ["DSIG"]
    s = Subsetter(options=o)
    s.populate(unicodes=sorted(ord(c) for c in chars))
    s.subset(f)
    buf = io.BytesIO()
    f.flavor = "woff2"
    f.save(buf)
    return buf.getvalue(), cmap


def build_faces(look, db, chars, cjk=None, prefix=""):
    """→ ([(family, weight, b64)], {role: {family, stack, weight, tracking}}, missing{face: chars})."""
    need_fonttools()
    faces, types, missing, done = [], {}, {}, {}
    cjk_fam = None
    if cjk:
        cjk_fam = prefix + "LookCJK"
        data, cjk_cmap = subset_face(pathlib.Path(cjk), None, [c for c in chars if ord(c) > 0x2e7f])
        faces.append((cjk_fam, "100 900", base64.b64encode(data).decode()))
    for role in ROLES:
        t = look["type"][role]
        face = t["face"]
        spec = db["faces"].get(face)
        if not spec:
            sys.exit(f"look.py: unknown face '{face}' — one of {', '.join(db['faces'])}")
        fam = prefix + family_of(face)
        if face not in done:
            data, cmap = subset_face(FONTS / spec["file"], spec.get("pin"), chars)
            faces.append((fam, spec["weight"], base64.b64encode(data).decode()))
            done[face] = cmap
            lack = sorted({c for c in chars if not c.isspace() and ord(c) not in cmap
                           and not (cjk and ord(c) in cjk_cmap)})
            if lack:
                missing[face] = "".join(lack)
        stack = ", ".join([f"'{fam}'"] + ([f"'{cjk_fam}'"] if cjk_fam else []) + [spec["fallback"]])
        types[role] = {"face": face, "family": fam, "stack": stack, "weight": t["weight"], "tracking": t["tracking"]}
    return faces, types, missing


def comp_chars(paths):
    text = ""
    for p in paths:
        s = pathlib.Path(p).read_text(errors="ignore")
        text += re.sub(r"base64,[A-Za-z0-9+/=]+", "", s)
    used = {c for c in text if ord(c) >= 0x20}
    return used, used | {chr(c) for c in range(0x20, 0x7F)} | set(TYPO)


# ── commands ──────────────────────────────────────────────────────────────────────────────────────────────────────
def cmd_list(a):
    db = load_db()
    for name, lk in db["looks"].items():
        ty = lk["type"]
        print(f"{name:12s} {lk['from']:26s} {ty['display']['face']} / {ty['text']['face']} / {ty['mono']['face']}")
        print(f"{'':12s} {lk['mood']}")
        print(f"{'':12s} " + "  ".join(f"{k} {lk['color'][k]}" for k in COLORS))


def cmd_check(a):
    db = load_db()
    specs = [a.look] if a.look else list(db["looks"])
    bad = 0
    for spec in specs:
        look = resolve(spec, db)
        ok, rows = check(look)
        print(f"{look['name']}: {'PASS' if ok else 'FAIL'}")
        print("\n".join(rows))
        bad += not ok
    sys.exit(1 if bad else 0)


JS = """/* look.js — generated by ohmymotion scripts/look.py; re-run `look.py apply` after copy changes, never edit by hand.
 * look: {name} ({origin}) · faces: {facelist} · subset to {nchars} characters · SIL OFL 1.1 (looks/fonts/LICENSES.txt)
 * DOM: var(--ink), font-family: var(--display) · canvas: ctx.font = LOOK.font('display', 96) · render: LOOK.ready
 */
(function (root) {{
  'use strict';
  const LOOK = {meta};
  const FACES = {faces};
  const bytes = b64 => Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  // canvas helpers: the role's weight unless one is passed; tracking is stored in em, canvas wants px
  LOOK.font = (role, px, weight) => `${{weight || LOOK.type[role].weight}} ${{px}}px ${{LOOK.type[role].stack}}`;
  LOOK.track = (role, px) => `${{(LOOK.type[role].tracking * px).toFixed(2)}}px`;
  const el = root.document.documentElement;
  for (const [k, v] of Object.entries(LOOK.color)) el.style.setProperty('--' + k, v);
  for (const [r, t] of Object.entries(LOOK.type)) {{
    el.style.setProperty('--' + r, t.stack);
    el.style.setProperty(`--${{r}}-weight`, String(t.weight));
    el.style.setProperty(`--${{r}}-tracking`, t.tracking + 'em');
  }}
  // FontFace from bytes: loaded and parsed before __ready resolves, no network, same result every render
  LOOK.ready = Promise.all(FACES.map(([family, weight, b64]) => {{
    const f = new FontFace(family, bytes(b64), {{ weight }});
    root.document.fonts.add(f);
    return f.load();
  }}));
  root.LOOK = LOOK;
}})(window);
"""


def render_js(look, faces, types, nchars):
    meta = {"name": look["name"], "from": look.get("from", ""), "color": {k: look["color"][k] for k in COLORS},
            "type": types}
    facelist = ", ".join(dict.fromkeys(t["face"] for t in types.values()))
    face_js = "[\n" + ",\n".join(f"    [{json.dumps(f)}, {json.dumps(w)}, '{b}']" for f, w, b in faces) + "\n  ]"
    return JS.format(name=look["name"], origin=look.get("from", "custom"), facelist=facelist, nchars=nchars,
                     meta=json.dumps(meta, ensure_ascii=False), faces=face_js)


def cmd_apply(a):
    db = load_db()
    look = resolve(a.look, db)
    comp = pathlib.Path(a.comp)
    used, chars = comp_chars([comp] + list(a.text_from or []))
    faces, types, missing = build_faces(look, db, sorted(chars), a.cjk)
    out = pathlib.Path(a.out) if a.out else comp.with_name("look.js")
    js = render_js(look, faces, types, len(chars))
    out.write_text(js)
    ok, rows = check(look)
    print(f"{out}  ·  look {look['name']}  ·  {len(js) / 1024:.0f} KB  ·  {len(chars)} characters")
    for role, t in types.items():
        print(f"    {role:8s} {t['face']:18s} {t['weight']}  tracking {t['tracking']}em")
    print("\n".join(rows))
    groups = {}
    for face, lack in missing.items():
        groups.setdefault("".join(c for c in lack if c in used), []).append(face)
    for shown, faces_ in groups.items():
        if shown:
            print(f"  ! {' / '.join(faces_)} lack{'s' if len(faces_) == 1 else ''} {len(shown)} character(s) the comp sets: {shown[:40]}"
                  f"{'…' if len(shown) > 40 else ''} — they fall back to the system face"
                  + ("; pass --cjk <font file>" if any(ord(c) > 0x2e7f for c in shown) else ""))
    if "look.js" not in comp.read_text(errors="ignore"):
        print(f"  → add <script src=\"{out.name}\"></script> to {comp.name} and chain __ready on LOOK.ready")


SHEET = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;background:#000}} .g{{display:grid;grid-template-columns:960px 960px;gap:0}}
.t{{position:relative;width:960px;height:540px;overflow:hidden}}
.lab{{position:absolute;left:44px;top:36px;font-size:17px;letter-spacing:.02em}}
.big{{position:absolute;left:40px;top:92px;font-size:112px;line-height:1;white-space:nowrap}}
.mood{{position:absolute;left:44px;top:232px;width:520px;font-size:23px;line-height:1.35}}
.card{{position:absolute;right:44px;top:92px;width:300px;height:212px;border-radius:16px;box-sizing:border-box;padding:24px 26px}}
.card .m{{font-size:15px;line-height:30px;white-space:nowrap}} .pill{{display:inline-block;margin-top:18px;padding:0 18px;
  height:40px;line-height:40px;border-radius:999px;font-size:17px}}
.sw{{position:absolute;left:44px;right:44px;bottom:40px;display:flex;gap:14px}}
.sw div{{flex:1;font-size:12px;line-height:1.5}} .sw i{{display:block;height:44px;border-radius:10px;margin-bottom:8px}}
</style></head><body><div class="g">{tiles}</div><script>{scripts}
window.__ready = Promise.all([{readies}]).then(() => document.querySelectorAll('.big').forEach(e => {{
  let px = 112; while (e.offsetWidth > 530 && px > 40) e.style.fontSize = (px -= 2) + 'px'; }}));</script></body></html>"""


def cmd_sheet(a):
    db = load_db()
    tiles, scripts, readies = [], [], []
    phrase = "Make it move."
    for i, (name, lk) in enumerate(db["looks"].items()):
        look = dict(lk, name=name)
        chars = sorted(set(phrase + name + lk["from"] + lk["mood"] + "".join(lk["color"].values())
                           + "".join(COLORS) + "verify → PASS  Render" + TYPO + "0123456789·"))
        faces, types, _ = build_faces(look, db, chars, prefix=f"s{i}")
        c = lk["color"]
        ty = {r: f"font-family:{t['stack']};font-weight:{t['weight']};letter-spacing:{t['tracking']}em" for r, t in types.items()}
        sw = "".join(f"<div style=\"{ty['mono']};color:{c['mute']}\"><i style=\"background:{c[k]};"
                     f"box-shadow:inset 0 0 0 1px {c['line']}\"></i>{k}<br>{c[k]}</div>" for k in COLORS)
        tiles.append(
            f"<div class=\"t\" style=\"background:radial-gradient(120% 90% at 30% 35%,{c['ground']} 55%,{c['deep']})\">"
            f"<div class=\"lab\" style=\"{ty['mono']};color:{c['mute']}\">{name} · {lk['from']}</div>"
            f"<div class=\"big\" style=\"{ty['display']};color:{c['ink']}\">{phrase}</div>"
            f"<div class=\"mood\" style=\"{ty['text']};color:{c['ink']}\">{lk['mood']}</div>"
            f"<div class=\"card\" style=\"background:{c['card']};border:1px solid {c['line']}\">"
            f"<div class=\"m\" style=\"{ty['mono']};color:{c['mute']}\">$ verify</div>"
            f"<div class=\"m\" style=\"{ty['mono']};color:{c['ink']}\">continuity · 0.83</div>"
            f"<div class=\"m\" style=\"{ty['mono']};color:{c['ink']}\">→ <b style=\"color:{c['accent']};font-weight:inherit\">PASS</b></div>"
            f"<div class=\"pill\" style=\"{ty['text']};background:{c['accent']};color:{c['ground'] if contrast(rgb(c['ground']), rgb(c['accent'])) > contrast(rgb(c['ink']), rgb(c['accent'])) else c['ink']}\">Render</div>"
            f"<span style=\"display:inline-block;width:14px;height:14px;border-radius:50%;margin-left:14px;vertical-align:-1px;background:{c['accent2']}\"></span>"
            f"</div><div class=\"sw\">{sw}</div></div>")
        for fam, w, b in faces:
            scripts.append(f"const f_{fam}=new FontFace('{fam}',Uint8Array.from(atob('{b}'),c=>c.charCodeAt(0)),{{weight:'{w}'}});"
                           f"document.fonts.add(f_{fam});")
            readies.append(f"f_{fam}.load()")
    html = SHEET.format(tiles="".join(tiles), scripts="\n".join(scripts), readies=",".join(readies))
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".html")
    tmp.write_text(html)
    from playwright.sync_api import sync_playwright
    rows = -(-len(tiles) // 2)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 540 * rows})
        pg.goto(tmp.resolve().as_uri())
        pg.evaluate("window.__ready")
        pg.screenshot(path=str(out))
        b.close()
    if not a.keep_html:
        tmp.unlink()
    print(f"{out}  ·  {len(tiles)} looks")


def cmd_from_shot(a):
    """Palette from the product's own screenshots. Pixels are counted in a coarse RGB histogram, not quantized: a
    median cut spends its palette on the near-whites of a UI and merges the text and the brand colour into greys.
    Core colours concentrate in one bin while anti-aliasing smears across many, so "most frequent bin that meets
    the role's contrast" finds them: ground = commonest; ink = commonest neutral at ≥ 4.5:1; accent = the hue
    family (12 buckets) with the most chromatic pixels (≥ 0.03 % of the frame); accent2 = the next family at least 60° away."""
    import numpy as np
    from PIL import Image
    db = load_db()
    base = resolve(a.faces, db)
    counts = {}
    for p in a.shots:
        im = Image.open(p).convert("RGB")
        k = max(1, max(im.size) // 900)
        px = np.asarray(im.resize((im.width // k, im.height // k), Image.NEAREST)).reshape(-1, 3).astype(int) // 8
        keys, n = np.unique(px, axis=0, return_counts=True)
        for c, m in zip(map(tuple, keys), n):
            c = tuple(int(v) for v in c)
            counts[c] = counts.get(c, 0) + int(m)
    total = sum(counts.values())
    bins = sorted(((m / total, tuple(v * 8 + 4 for v in c)) for c, m in counts.items()), reverse=True)
    ground = bins[0][1]
    light = lum(ground) > 0.4

    def hls(c):
        return colorsys.rgb_to_hls(*(v / 255 for v in c))

    def chroma(c):
        h, l, s = hls(c)
        return s * (1 - abs(2 * l - 1))

    def first(pred, floor=0.0005):
        return next((c for s, c in bins if s >= floor and pred(c)), None)

    neutral = lambda c: chroma(c) < 0.12
    ink = first(lambda c: neutral(c) and contrast(c, ground) >= 7) or first(lambda c: neutral(c) and contrast(c, ground) >= 4.5)
    ink = ink or ((22, 22, 22) if light else (240, 238, 232))
    fam = {}
    for s, c in bins:
        if s >= 0.00002 and chroma(c) > 0.3 and contrast(c, ground) >= 1.3:   # a UI's accent is ~0.1 % of it
            fam.setdefault(int(hls(c)[0] * 12) % 12, []).append((s, c))
    ranked = sorted(((h, v) for h, v in fam.items() if sum(s for s, _ in v) >= 0.0003),
                    key=lambda kv: -sum(s for s, _ in kv[1]))
    accent = ranked[0][1][0][1] if ranked else mix(ink, ground, 0.35)
    far = [v for h, v in ranked[1:] if min(abs(h - ranked[0][0]), 12 - abs(h - ranked[0][0])) >= 2]
    accent2 = far[0][0][1] if far else mix(accent, ground, 0.45)
    mute = first(lambda c: neutral(c) and 3 <= contrast(c, ground) < 6) or mix(ground, ink, 0.55)
    line = first(lambda c: neutral(c) and 1.1 <= contrast(c, ground) < 1.6, 0.002) or mix(ground, ink, 0.12)
    card = first(lambda c: c != ground and contrast(c, ground) < 1.1, 0.01) or \
        (mix(ground, (255, 255, 255), 0.6) if light else mix(ground, ink, 0.06))
    deep = mix(ground, (0, 0, 0), 0.06 if light else 0.45)
    look = {"name": pathlib.Path(a.out).stem if a.out else "product",
            "from": ", ".join(str(p) for p in a.shots),
            "mood": "the product's own colours, measured from its screenshots",
            "color": {k: hexc(v) for k, v in dict(ground=ground, deep=deep, card=card, line=line, mute=mute, ink=ink,
                                                   accent=accent, accent2=accent2).items()},
            "type": base["type"]}
    txt = json.dumps(look, indent=2, ensure_ascii=False)
    if a.out:
        pathlib.Path(a.out).write_text(txt + "\n")
        print(f"{a.out}  ·  faces from '{base['name']}' — edit the file to change them")
    else:
        print(txt)
    ok, rows = check(look)
    print("\n".join(rows))
    print("  hue families: " + "  ".join(f"{hexc(v[0][1])} {sum(s for s, _ in v):.2%}" for h, v in ranked[:5]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    c = sub.add_parser("check"); c.add_argument("look", nargs="?"); c.set_defaults(fn=cmd_check)
    s = sub.add_parser("sheet"); s.add_argument("--out", default=str(ROOT / "gallery" / "sheets" / "looks.png"))
    s.add_argument("--keep-html", action="store_true"); s.set_defaults(fn=cmd_sheet)
    p = sub.add_parser("apply"); p.add_argument("look"); p.add_argument("comp")
    p.add_argument("--out", help="default: look.js next to the comp")
    p.add_argument("--text-from", nargs="*", help="more files whose characters the film sets (string tables, other languages)")
    p.add_argument("--cjk", help="a CJK font file (e.g. Noto Sans SC) appended to every stack, subset to the CJK the comp sets")
    p.set_defaults(fn=cmd_apply)
    f = sub.add_parser("from-shot"); f.add_argument("shots", nargs="+")
    f.add_argument("--faces", default="paper", help="the look whose three faces to keep (default paper)")
    f.add_argument("--out", help="write the look here (.json); prints it otherwise"); f.set_defaults(fn=cmd_from_shot)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
