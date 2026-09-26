#!/usr/bin/env python3
# onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
"""frame_diff.py — do two compositions draw the same frames? For a change that must leave one version untouched
(a new language behind ?lang=, a refactor): freeze a copy of the accepted comp, then compare it with the working one.

  python3 scripts/frame_diff.py frozen/comp.html "comp.html" --times 0.3,9.5,15.1,25.6,36.4 [--out diff/]

A frozen copy needs its neighbours (motion.js, data, images) beside it: symlink them into its folder. Paths may carry a
query (comp.html?lang=ja). Prints the max channel difference and the changed-pixel count per time; exits 1 on any
difference. --out writes both frames and an amplified difference image for the times that differ.
"""
import argparse, asyncio, io, os, sys
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright


async def frames(url, ts, w, h):
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": w, "height": h})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(url); await pg.evaluate("window.__ready"); out = []
        for t in ts:
            await pg.evaluate(f"window.__seek({t})"); out.append(np.asarray(Image.open(io.BytesIO(await pg.screenshot())).convert("RGB")))
        await b.close()
        if errs:
            print(url, "page errors:", errs[:3])
        return out


def url(p):
    path, _, q = p.partition("?"); return "file://" + os.path.abspath(path) + ("?" + q if q else "")


ap = argparse.ArgumentParser(); ap.add_argument("a"); ap.add_argument("b"); ap.add_argument("--times", required=True)
ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080); ap.add_argument("--out")
a = ap.parse_args(); ts = [float(x) for x in a.times.split(",")]
A = asyncio.run(frames(url(a.a), ts, a.width, a.height)); B = asyncio.run(frames(url(a.b), ts, a.width, a.height)); bad = 0
for t, x, y in zip(ts, A, B):
    d = np.abs(x.astype(int) - y.astype(int)); n = int((d.sum(2) > 0).sum()); bad += n > 0
    print(f"t={t:7.2f}  max {d.max():3d}  changed px {n}")
    if n and a.out:
        os.makedirs(a.out, exist_ok=True); Image.fromarray(x).save(f"{a.out}/{t:07.2f}_a.png"); Image.fromarray(y).save(f"{a.out}/{t:07.2f}_b.png")
        Image.fromarray(np.clip(d * 8, 0, 255).astype(np.uint8)).save(f"{a.out}/{t:07.2f}_diff.png")
print("identical" if not bad else f"{bad} of {len(ts)} times differ"); sys.exit(1 if bad else 0)
