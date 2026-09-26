#!/usr/bin/env python3
# onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
"""stills.py — a contact sheet of chosen moments, to look before rendering.

  python3 scripts/stills.py comp.html --times 0.7,2.4,3.8,6.2,9.9,12.7 --out stills.png
"""
import argparse, asyncio, io, os
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright

async def main():
    ap = argparse.ArgumentParser(); ap.add_argument("comp"); ap.add_argument("--times", required=True); ap.add_argument("--out", default="stills.png")
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080); ap.add_argument("--cols", type=int, default=3)
    a = ap.parse_args(); ts = [float(x) for x in a.times.split(",")]
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": a.width, "height": a.height})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("file://" + os.path.abspath(a.comp) + "?hud=1"); await pg.evaluate("window.__ready")
        tiles = []
        for t in ts:
            await pg.evaluate(f"window.__seek({t})"); await pg.wait_for_timeout(30)
            im = Image.open(io.BytesIO(await pg.screenshot())).resize((640, 360)); ImageDraw.Draw(im).text((6, 6), f"t={t}", fill=(200, 0, 0)); tiles.append(im)
        await b.close()
    rows = (len(tiles) + a.cols - 1) // a.cols; sheet = Image.new("RGB", (640 * a.cols, 360 * rows), (0, 0, 0))
    for i, im in enumerate(tiles): sheet.paste(im, ((i % a.cols) * 640, (i // a.cols) * 360))
    sheet.save(a.out); print("wrote", a.out, "| page errors:", errs[:3] or "none")

if __name__ == "__main__":
    asyncio.run(main())
