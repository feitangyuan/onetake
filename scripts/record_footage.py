#!/usr/bin/env python3
# onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
"""record_footage.py — drive real pages in real time, record them, mark where the input starts.

  python3 scripts/record_footage.py footage.json --out footage/

footage.json:
{
  "viewport": [1920, 1200],          # record at the size you will show; frames are extracted 1:1
  "settle_ms": 1500,                 # after load, before anything
  "preroll_ms": 1400,                # idle time recorded before the input starts (the page breathing)
  "tail_ms": 2000,                   # recorded after the input ends (the settle)
  "cases": [
    {"name": "critter", "url": "file:///…/index.html",
     "prep":  [{"click_text": "Spring"}, {"wait": 300}],           # optional: clicks / waits / key presses before the marker
     "drive": [{"sweep": [[720,450],[380,300],[1060,620]], "dur": 3.2}]},   # after the marker; coords in 1440×900 space if "coord_space": [1440,900]
    {"name": "press-stack", "url": "…", "drive": [{"wheel": {"n": 10, "dy": 260, "gap_ms": 220}}]},
    {"name": "demo",       "url": "…", "drive": [{"wheel": {"n":1,"dy":600,"gap_ms":0}}, {"wait":1500}, {"wheel": {"n":1,"dy":600,"gap_ms":0}}]}
  ],
  "coord_space": [1440, 900]         # optional: sweep points are scaled from this to the viewport
}

Sweeps are wall-clock paced: each segment gets its share of `dur`, moves are batched so the Playwright
round trip does not slow the hand (a naive per-step await ran 4× slow). A 24 px magenta square is
injected for 140 ms at bottom-left when the drive starts; extraction finds it → `mark`.

Writes: <out>/<name>.webm, <out>/frames/<name>/NNNN.jpg (30 fps), <out>/info.json {name:{n,mark}},
<out>/paths.json {name:{"pts":[[x,y]…],"dur":…} | {"wheel":[n,dy,gap]}} in viewport coordinates.
"""
import argparse, asyncio, glob, json, os, re, shutil, subprocess, time
from PIL import Image
from playwright.async_api import async_playwright

MARK = """(()=>{const d=document.createElement('div');d.id='__mark';d.style.cssText='position:fixed;left:0;bottom:0;width:24px;height:24px;background:#ff00ff;z-index:99999;pointer-events:none';document.body.appendChild(d);setTimeout(()=>d.remove(),140);})()"""

async def sweep(pg, pts, dur):
    n = len(pts) - 1; per = dur / n
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]; t0 = time.time(); sub = 6
        for s in range(1, sub + 1):
            k = s / sub; k = k * k * (3 - 2 * k)
            await pg.mouse.move(x0 + (x1 - x0) * k, y0 + (y1 - y0) * k, steps=4)
            dt = t0 + per * s / sub - time.time()
            if dt > 0: await pg.wait_for_timeout(int(dt * 1000))

async def run_steps(pg, steps, sc, log, name):
    for st in steps:
        if "sweep" in st:
            pts = [(x * sc[0], y * sc[1]) for x, y in st["sweep"]]; log[name] = {"pts": pts, "dur": st["dur"]}
            await sweep(pg, pts, st["dur"])
        elif "wheel" in st:
            w = st["wheel"]; log.setdefault(name, {}).setdefault("wheel", []).append([w["n"], w["dy"], w.get("gap_ms", 200)])
            for _ in range(w["n"]): await pg.mouse.wheel(0, w["dy"]); await pg.wait_for_timeout(w.get("gap_ms", 200))
        elif "wait" in st: await pg.wait_for_timeout(st["wait"])
        elif "click_text" in st: await pg.get_by_role("button", name=re.compile(st["click_text"])).click()
        elif "click" in st: x, y = st["click"]; await pg.mouse.click(x * sc[0], y * sc[1])
        elif "key" in st: await pg.keyboard.press(st["key"])
        elif "eval" in st: await pg.evaluate(st["eval"])

async def main():
    ap = argparse.ArgumentParser(); ap.add_argument("config"); ap.add_argument("--out", default="footage"); a = ap.parse_args()
    cfg = json.load(open(a.config)); out = os.path.abspath(a.out); os.makedirs(out, exist_ok=True)
    W, H = cfg.get("viewport", [1920, 1200]); cs = cfg.get("coord_space", [W, H]); sc = (W / cs[0], H / cs[1])
    log = {}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for c in cfg["cases"]:
            name = c["name"]; d = f"{out}/raw_{name}"; shutil.rmtree(d, ignore_errors=True)
            ctx = await b.new_context(viewport={"width": W, "height": H}, record_video_dir=d, record_video_size={"width": W, "height": H})
            pg = await ctx.new_page(); await pg.goto(c["url"], wait_until="load"); await pg.wait_for_timeout(cfg.get("settle_ms", 1500))
            await run_steps(pg, c.get("prep", []), sc, {}, name)
            await pg.mouse.move(W / 2, H / 2); await pg.wait_for_timeout(cfg.get("preroll_ms", 1400))
            await pg.evaluate(MARK); t0 = time.time()
            await run_steps(pg, c["drive"], sc, log, name)
            print(f"recorded {name}  drive {time.time()-t0:.2f}s", flush=True)
            await pg.wait_for_timeout(cfg.get("tail_ms", 2000)); await ctx.close()
            v = [f for f in os.listdir(d) if f.endswith(".webm")][0]; os.replace(f"{d}/{v}", f"{out}/{name}.webm"); shutil.rmtree(d)
        await b.close()
    json.dump(log, open(f"{out}/paths.json", "w"), indent=1)
    info = {}
    for c in cfg["cases"]:
        name = c["name"]; d = f"{out}/frames/{name}"; os.makedirs(d, exist_ok=True)
        for f in glob.glob(f"{d}/*.jpg"): os.remove(f)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{out}/{name}.webm", "-vf", "fps=30", "-q:v", "2", f"{d}/%04d.jpg"], check=True)
        frames = sorted(glob.glob(f"{d}/*.jpg")); mark = None
        for i, f in enumerate(frames):
            px = Image.open(f).getpixel((6, H - 8))
            if px[0] > 180 and px[2] > 180 and px[1] < 90: mark = i; break
        info[name] = {"n": len(frames), "mark": mark}; print(f"{name}: {len(frames)} frames, mark {mark}")
        if mark is None: print(f"  !! no marker found for {name} — the page may cover the bottom-left corner; check frames")
    json.dump(info, open(f"{out}/info.json", "w"), indent=1)

if __name__ == "__main__":
    asyncio.run(main())
