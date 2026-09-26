#!/usr/bin/env python3
# onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
"""gallery.py — render the motion library's sheets: frames of each move above its speed graph.

  python3 scripts/gallery.py                        # every demo in gallery/gallery.html → gallery/sheets/<name>.png
  python3 scripts/gallery.py --only ribbon,iris     # some

A sheet is six frames of the demo (3×2) over the speed of every tracked element in px/frame at 60 fps, with each
move's t80 — the same numbers probe.py reports for a whole film. Look at the frames to pick a move; read the graph
for its curve: a tall spike at the start of a move is a snap (low t80), a symmetric hill is a soft S-curve.
The live demo is gallery/gallery.html?demo=<name>&play.
"""
import argparse, asyncio, io, os, sys
from PIL import Image, ImageDraw
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "gallery", "gallery.html")
OUT = os.path.join(ROOT, "gallery", "sheets")


async def run(only, fps):
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1920, "height": 1080})
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto("file://" + PAGE); await pg.evaluate("window.__ready")
        demos = await pg.evaluate("window.__demos")
        for d in demos:
            if only and d["name"] not in only:
                continue
            res = await probe.collect_page(pg, PAGE, fps=fps, query=f"?demo={d['name']}")
            res.update(W=1920, H=1080)
            cv = probe.curves(res)
            dur = d["dur"]; shots = d["shots"] or [round(dur * f, 3) for f in (0.08, 0.26, 0.42, 0.58, 0.76, 0.94)]
            tiles = []
            for t in shots:
                await pg.evaluate("t => window.__seek(t)", t)
                im = Image.open(io.BytesIO(await pg.screenshot())).convert("RGB").resize((640, 360), Image.LANCZOS)
                ImageDraw.Draw(im).text((12, 338), f"t={t:.2f}", fill=(180, 40, 40))
                tiles.append(im)
            graph = os.path.join(OUT, f"_{d['name']}.graph.png")
            if cv["tracks"] and cv["moves"]:
                probe.plot_speeds(res, cv, graph, title=f"OM.{d['name']} — speed of tracked elements (px/frame @{fps}), t80 per move", times=shots, size=(19.2, 3.0))
                gim = Image.open(graph).convert("RGB"); os.remove(graph)
            else:
                gim = Image.new("RGB", (1920, 300), (248, 248, 246))
                why = "moves in place (no tracked element travels 30 px)" if cv["tracks"] else "hard cuts: nothing travels"
                ImageDraw.Draw(gim).text((40, 140), f"OM.{d['name']} — {why}", fill=(90, 90, 90))
            sheet = Image.new("RGB", (1920, 720 + gim.height), (248, 248, 246))
            for i, im in enumerate(tiles):
                sheet.paste(im, ((i % 3) * 640, (i // 3) * 360))
            sheet.paste(gim, (0, 720))
            path = os.path.join(OUT, f"{d['name']}.png")
            sheet.quantize(colors=200, method=Image.FASTOCTREE, dither=Image.NONE).save(path, optimize=True)
            top = cv["moves"][0] if cv["moves"] else None
            print(f"  {d['name']:13} {d['group']:8} {os.path.getsize(path) // 1024:4d} KB   peak {cv['peak']:5.0f} px/frame"
                  + (f"   longest move t80 {top['t80']:.2f}" if top else ""))
        await b.close()
    print("page errors:", errs[:3] or "none")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=""); ap.add_argument("--fps", type=int, default=60)
    a = ap.parse_args()
    asyncio.run(run([x for x in a.only.split(",") if x], a.fps))


if __name__ == "__main__":
    main()
