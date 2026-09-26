#!/usr/bin/env python3
# onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
"""render.py — seek a composition frame by frame, screenshot, encode, mux the SFX.

  python3 scripts/render.py comp.html --out draft.mp4 --sfx sfx.wav           # review draft: 1920×1080, 30 fps, shutter 180°
  python3 scripts/render.py comp.html --out film.mp4 --final --sfx sfx.wav    # only after the cut is accepted: 3840×2160, 60 fps
  python3 scripts/render.py comp.html --out raw.mp4 --shutter 0               # no motion blur (to compare)

Drafts are the default: every round before acceptance is a draft, and a 4K60 render of a rejected cut is
wasted minutes. The composition is authored at --width×--height CSS px; --scale 2 captures it at 3840×2160.
Duration comes from window.__meta.dur if the page defines it, else --dur. Every capture awaits `__seek(t)`,
which must resolve only after that frame's images are decoded.

Workers. A capture is a Chrome screenshot, ~150 ms, of which the page's own drawing is under a millisecond. So
--workers browsers (default: cores − 2, at most 8) run in separate processes, each taking every n-th frame.

Motion blur (--shutter, degrees; 0 = off). A film camera integrates light while its shutter is open; a
screenshot is an instant, so a fast move strobes into separate copies. For each frame the renderer seeks
several times across the open shutter (centred on the frame time) and averages the captures in linear
light. It captures the two ends of the shutter first: if they are identical nothing moved, the frame is
written as is and the other samples are skipped, so holds cost nothing. __seek(t) is pure, so this is the
real integral, not a blur filter.

How many captures. A fixed count strobes fast moves anyway: 8 captures of the one-dot film's 633 px/frame
opening left 40 px between copies and its edges stepped. A page that defines window.__motion(t0, t1) → the
farthest anything travels on screen between two times (its elements and its camera, CSS px) gets enough
captures per frame to keep neighbours --gap px apart, between --samples-min and --samples-max. A page without
it gets --samples per moving frame.

A camera never exposes across an edit. When one step between neighbouring captures holds the change (>= 3x
any other step) — a hard cut, a word popping in, a typed character, a footage frame flipping — only the
captures on the frame time's side of it are averaged, so a cut stays a cut instead of a one-frame dissolve.

Writes <out>.render.json next to the film (fps, scale, shutter, samples, workers, frames, captures, cut frames,
seconds); verify_promo.py reads it to know whether fast moves were rendered with blur.
"""
import argparse, asyncio, io, json, math, multiprocessing, os, shutil, subprocess, time
from concurrent.futures import ProcessPoolExecutor, wait
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright

_u = np.arange(256) / 255.0
SRGB_TO_LIN = np.where(_u <= 0.04045, _u / 12.92, ((_u + 0.055) / 1.055) ** 2.4).astype(np.float32)
_l = np.arange(65536) / 65535.0
LIN_TO_SRGB = np.clip(np.rint(np.where(_l <= 0.0031308, _l * 12.92, 1.055 * np.power(_l, 1 / 2.4) - 0.055) * 255.0), 0, 255).astype(np.uint8)


def decode(png):
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGB"))


def cut_side(small):
    """Indices of the captures to integrate, given each one box-filtered to greyscale: all of them, unless one step
    between neighbours carries the change (a discontinuity, not motion) — then the side holding the frame time, the
    later side if the step straddles it."""
    n = len(small)
    if n < 4:
        return list(range(n))
    d = np.array([np.abs(small[k + 1] - small[k]).mean() for k in range(n - 1)])
    j = int(d.argmax())
    if d[j] <= 0 or d[j] < 3 * np.delete(d, j).max():
        return list(range(n))
    return list(range(j + 1, n)) if j < n // 2 else list(range(j + 1))


def uncut(shots):
    """cut_side for decoded captures."""
    if len(shots) < 4:
        return list(range(len(shots)))
    return cut_side([np.asarray(Image.fromarray(s).convert("L").reduce(8), np.int16) for s in shots])   # box-filtered, so motion changes every step


def integrate(shots):
    """Average decoded captures in linear light, leaving out the far side of a cut. Returns (image, cut)."""
    keep = uncut(shots)
    acc = np.zeros(shots[0].shape, np.float32)
    for k in keep:
        acc += SRGB_TO_LIN[shots[k]]
    idx = np.clip(np.rint(acc * (65535.0 / len(keep))), 0, 65535).astype(np.uint16)
    return LIN_TO_SRGB[idx], len(keep) < len(shots)


def integrate_png(pngs):
    """integrate() over PNG bytes, decoding one capture at a time, so 48 captures of a 4K frame never sit in memory at once."""
    keep = cut_side([np.asarray(Image.open(io.BytesIO(p)).convert("L").reduce(8), np.int16) for p in pngs]) if len(pngs) >= 4 else list(range(len(pngs)))
    acc = None
    for k in keep:
        lin = SRGB_TO_LIN[decode(pngs[k])]
        if acc is None:
            acc = lin
        else:
            acc += lin
    idx = np.clip(np.rint(acc * (65535.0 / len(keep))), 0, 65535).astype(np.uint16)
    return LIN_TO_SRGB[idx], len(keep) < len(pngs)


def work(job):
    """One browser in its own process, rendering the frames f ≡ job['k'] (mod job['n']). Returns its counters."""
    return asyncio.run(_work(job))


async def _work(j):
    fps, dur, fr, sh = j["fps"], j["dur"], j["fr"], j["shutter"]
    st = {"captures": 0, "still": 0, "cuts": 0, "errors": [], "hist": {}}
    async with async_playwright() as p:
        B = {}                                   # the live browser; relaunched every j["recycle"] frames

        async def launch():
            if B:
                await B["br"].close()
            B["br"] = br = await p.chromium.launch()
            B["pg"] = pg = await (await br.new_context(viewport={"width": j["width"], "height": j["height"]}, device_scale_factor=j["scale"])).new_page()
            pg.on("pageerror", lambda e: st["errors"].append(str(e))); pg.on("console", lambda m: st["errors"].append(m.text) if m.type == "error" else None)
            await pg.goto("file://" + j["comp"]); await pg.evaluate("window.__ready")

        await launch(); pg = B["pg"]
        adaptive = sh > 0 and await pg.evaluate("typeof window.__motion === 'function'")
        open_s = (sh / 360.0) / fps

        async def grab(t):
            await B["pg"].evaluate(f"window.__seek({t})"); st["captures"] += 1
            return await B["pg"].screenshot(type="png")

        done = 0
        for f in range(j["k"], j["N"], j["n"]):
            t = f / fps; path = f"{fr}/{f:05d}.png"
            if j.get("resume") and os.path.exists(path):
                continue
            if done and j.get("recycle") and done % j["recycle"] == 0:
                await launch()                   # a Chrome taking 4K screenshots for ~30 min grows until the OS closes it
            done += 1; pg = B["pg"]
            if sh <= 0:
                open(path, "wb").write(await grab(t))
                continue
            S = j["samples"]
            if adaptive:
                try:
                    far = await pg.evaluate(f"window.__motion({max(t - open_s / 2, 0.0)}, {min(t + open_s / 2, dur - 1e-6)})")
                    S = min(j["smax"], max(j["smin"], math.ceil(far * j["scale"] / j["gap"])))
                except Exception:                                   # a page whose __motion throws keeps the fixed count
                    S = j["samples"]
            times = [min(max(t + open_s * ((k + 0.5) / S - 0.5), 0.0), dur - 1e-6) for k in range(S)]
            first = await grab(times[0]); last = await grab(times[-1])
            if first == last:                                        # nothing moved while the shutter was open
                open(path, "wb").write(first); st["still"] += 1
                continue
            pngs = [first] + [await grab(tk) for tk in times[1:-1]] + [last]
            img, cut = integrate_png(pngs); st["cuts"] += cut
            Image.fromarray(img).save(path, compress_level=1)
            st["hist"][S] = st["hist"].get(S, 0) + 1
        await B["br"].close()
    return st


async def page_info(comp, width, height):
    async with async_playwright() as p:
        br = await p.chromium.launch()
        pg = await (await br.new_context(viewport={"width": width, "height": height})).new_page()
        await pg.goto("file://" + comp); await pg.evaluate("window.__ready")
        info = await pg.evaluate("({dur: (window.__meta && window.__meta.dur) || null, motion: typeof window.__motion === 'function'})")
        await br.close()
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comp"); ap.add_argument("--out", default="draft.mp4")
    ap.add_argument("--fps", type=int, default=30); ap.add_argument("--scale", type=int, default=1)
    ap.add_argument("--final", action="store_true", help="3840×2160 at 60 fps (sets --fps 60 --scale 2) — only once the cut is accepted")
    ap.add_argument("--shutter", type=float, default=180.0, help="shutter angle in degrees; 0 = no motion blur")
    ap.add_argument("--samples", type=int, default=8, help="captures per moving frame when the page has no window.__motion")
    ap.add_argument("--gap", type=float, default=24.0, help="px between neighbouring captures, for a page with window.__motion")
    ap.add_argument("--samples-min", type=int, default=4); ap.add_argument("--samples-max", type=int, default=12)
    ap.add_argument("--workers", type=int, default=max(1, min(8, (os.cpu_count() or 3) - 2)), help="browsers rendering in parallel processes")
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--dur", type=float, default=None); ap.add_argument("--sfx", default=None); ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--keep-frames", action="store_true")
    ap.add_argument("--recycle", type=int, default=150, help="relaunch each worker's browser after this many frames (0 = never)")
    ap.add_argument("--resume", action="store_true", help="keep _frames/ from a run that died and render only the missing frames (counts in the log cover this run only)")
    a = ap.parse_args()
    if a.final:
        a.fps, a.scale = 60, 2
    comp = os.path.abspath(a.comp); out = os.path.abspath(a.out); fr = os.path.join(os.path.dirname(out), "_frames")
    if not a.resume:
        shutil.rmtree(fr, ignore_errors=True)
    os.makedirs(fr, exist_ok=True)
    info = asyncio.run(page_info(comp, a.width, a.height))
    dur = a.dur or info["dur"] or 15; N = int(round(dur * a.fps)); nw = max(1, min(a.workers, N))
    adaptive = a.shutter > 0 and info["motion"]
    how = "no shutter" if a.shutter <= 0 else f"shutter {a.shutter:g}°, " + (
        f"captures per frame sized by __motion (gap {a.gap:g} px, {a.samples_min}–{a.samples_max})" if adaptive else f"{a.samples} captures per moving frame")
    print(f"{N} frames on {nw} workers · {how}", flush=True)
    job = dict(comp=comp, fr=fr, fps=a.fps, dur=dur, N=N, n=nw, width=a.width, height=a.height, scale=a.scale, shutter=a.shutter,
               samples=max(2, a.samples), gap=a.gap, smin=max(2, a.samples_min), smax=max(2, a.samples_max), resume=a.resume, recycle=a.recycle)
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=nw, mp_context=multiprocessing.get_context("spawn")) as ex:
        futs = [ex.submit(work, dict(job, k=k)) for k in range(nw)]
        while wait(futs, timeout=15).not_done:
            print(f"  {len(os.listdir(fr))}/{N}  {time.time() - t0:.0f}s", flush=True)
        res = [f.result() for f in futs]
    secs = time.time() - t0
    captures, still, cuts = (sum(r[k] for r in res) for k in ("captures", "still", "cuts"))
    errs = [e for r in res for e in r["errors"]]; hist = {}
    for r in res:
        for k, v in r["hist"].items():
            hist[k] = hist.get(k, 0) + v
    print(f"{N} frames, {captures} captures ({still} still frames skipped the shutter, {cuts} kept a cut hard) in {secs:.0f}s on {nw} workers; page errors: {errs[:3] or 'none'}")
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(a.fps), "-i", f"{fr}/%05d.png"]
    if a.sfx: cmd += ["-i", os.path.abspath(a.sfx)]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf), "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "5.2", "-movflags", "+faststart"]
    if a.sfx: cmd += ["-c:a", "aac", "-b:a", "256k", "-shortest"]
    subprocess.run(cmd + [out], check=True)
    if not a.keep_frames: shutil.rmtree(fr, ignore_errors=True)
    meta = {"comp": comp, "fps": a.fps, "scale": a.scale, "size": [a.width * a.scale, a.height * a.scale], "shutter": a.shutter if a.shutter > 0 else 0,
            "samples": ("adaptive" if adaptive else max(2, a.samples)) if a.shutter > 0 else 1}
    if adaptive:
        meta.update(gap_px=a.gap, samples_per_moving_frame={str(k): hist[k] for k in sorted(hist)})
    meta.update(workers=nw, frames=N, still_frames=still, cut_frames=cuts, captures=captures, seconds=round(secs, 1), final=a.final)
    json.dump(meta, open(os.path.splitext(out)[0] + ".render.json", "w"), indent=1)
    print("wrote", out)


if __name__ == "__main__":
    main()
