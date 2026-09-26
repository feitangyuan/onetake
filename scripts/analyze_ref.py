#!/usr/bin/env python3
# onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
"""analyze_ref.py — read a reference clip in numbers before composing anything.

  python3 scripts/analyze_ref.py ref.mp4 --out ana/
  python3 scripts/analyze_ref.py ref.mp4 --out ana/ --no-flow      # rhythm only

Writes into --out:
  energy.txt      one char per 1/12 s (' .:-=+*#%@'), rows of 4 s — where the film rests and where it hits
  summary.json    duration, stillness ratios, cut times, burst windows, longest quiet stretch, and "flow"
  sheet_NN.png    contact sheets at 4 fps, 24 frames each (6×4)
  frame_NN.png    9 full frames spread across the clip

The energy map says WHEN things move. "flow" (optical flow at 30 fps — or the source's own rate if slower, so a
24 fps clip is not padded with repeated frames — 320 px wide) says HOW: the dominant speed per frame (median flow
over moving edges, px per 1/30 s normalised to 1920 wide), the moves cut from it with their t80
(share of the move's duration before 80 % of its travel is done — .23 is an expo snap, .67 a symmetric S-curve),
and whether fast frames are smeared along their motion. Smear = gradient energy along the motion / across it, on
the pixels that changed: < .78 is shutter blur (render.py's 180° shutter: a linear test move .64, Pocket Weather v3
.69); sharp renders read ~.9 or more (the test move unblurred .99, v3 as drafted 1.07, motion-web .88 — its CSS
blur() on fly-throughs is not motion blur). It is a fingerprint of the dominant motion, not a per-element track:
speed reads up to ~30 % low on fast small objects (a 100 px box at 167 px/frame reads 121–155). probe.py measures
a composition exactly.

Then write the beat sheet (references/reference-deconstruction.md). Also works on your own render:
`verify_promo.py` prints the same map next to the reference's.
"""
import argparse, glob, json, math, os, shutil, subprocess
import numpy as np
from PIL import Image

CHARS = " .:-=+*#%@"
SMEAR_BLUR = 0.78   # fast frames smeared below this were rendered with motion blur

def energy(video, workdir, fps=12, width=320):
    d = os.path.join(workdir, "_e"); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps={fps},scale={width}:-1", f"{d}/f_%05d.png"], check=True)
    prev = None; diffs = []
    for f in sorted(glob.glob(f"{d}/f_*.png")):
        a = np.asarray(Image.open(f).convert("L"), dtype=np.float32)
        diffs.append(0.0 if prev is None else float(np.abs(a - prev).mean())); prev = a
    shutil.rmtree(d, ignore_errors=True)
    return np.array(diffs), fps

def energy_map(d, fps, row_s=4):
    per = fps * row_s; lines = []
    for r in range(0, len(d), per):
        lines.append(f"{r/fps:5.1f}s |" + "".join(CHARS[min(9, int(v / 3))] for v in d[r:r + per]) + "|")
    return "\n".join(lines)

def stats(d, fps, cut_thr=18.0, still_thr=0.5, low_thr=2.0):
    cuts = [round(i / fps, 2) for i in range(1, len(d)) if d[i] > cut_thr]
    # bursts: windows of 1.5 s holding >= 3 big changes (> 8)
    big = [i for i in range(len(d)) if d[i] > 8]; bursts = []
    for i in big:
        win = [j for j in big if i <= j < i + int(1.5 * fps)]
        if len(win) >= 3 and (not bursts or i / fps > bursts[-1][1]): bursts.append((round(i / fps, 2), round(win[-1] / fps, 2)))
    # longest quiet stretch (below low_thr)
    best = cur = 0
    for v in d:
        cur = cur + 1 if v < low_thr else 0; best = max(best, cur)
    return {"duration_s": round(len(d) / fps, 2), "still_ratio": round(float((d < still_thr).mean()), 3),
            "low_ratio": round(float((d < low_thr).mean()), 3), "cuts": cuts, "bursts": bursts,
            "longest_quiet_s": round(best / fps, 2), "mean_energy": round(float(d.mean()), 3)}

def flow(video, fps=30, width=320, fast=24.0, vmin=2.0):
    try:
        import cv2
    except ImportError:
        return None
    wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,avg_frame_rate", "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip().split(",")
    h = int(round(int(wh[1]) * width / int(wh[0]) / 2) * 2)
    num, _, den = wh[2].partition("/")
    src = float(num) / float(den or 1) if float(den or 1) else 0.0
    # Resampling a slower source up to `fps` repeats frames (24 → 30 repeats every 4th): each repeat reads as a
    # zero-flow frame and splits every move in pieces. Sample slower sources at their own rate and rescale speeds
    # to px per 1/fps s, so peak, thresholds and the comparison with a render stay in one unit.
    sfps = src if 0 < src < fps else fps
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps={sfps},scale={width}:{h}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, h, width)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    norm = 1920.0 / width * sfps / fps
    speed = np.zeros(len(frames)); smear = []
    for i in range(1, len(frames)):
        a, b = frames[i - 1], frames[i]
        f = dis.calc(a, b, None)
        mag = np.hypot(f[..., 0], f[..., 1]); moving = mag > 0.5
        if moving.mean() < 0.002:
            continue
        g = b.astype(np.float32)
        gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
        edges = moving & (np.hypot(gx, gy) > 20)               # flow is trustworthy where there is an edge to follow
        speed[i] = float(np.median(mag[edges] if edges.sum() > 20 else mag[moving])) * norm
        if speed[i] >= fast:                                   # fast frame: is the changed content smeared along its motion?
            dx, dy = float(np.median(f[..., 0][moving])), float(np.median(f[..., 1][moving])); n = math.hypot(dx, dy)
            changed = moving & (np.abs(b.astype(np.int16) - a.astype(np.int16)) > 12)
            if n > 0.3 and changed.sum() > 20:
                ux, uy = dx / n, dy / n
                e_par = float(((gx * ux + gy * uy)[changed] ** 2).mean()); e_per = float(((-gx * uy + gy * ux)[changed] ** 2).mean())
                if e_per > 1.0:
                    smear.append(e_par / e_per)
    moves, k = [], 1
    while k < len(speed):
        if speed[k] < vmin:
            k += 1; continue
        a = k
        while k < len(speed) and speed[k] >= vmin:
            k += 1
        path = speed[a:k]; L = float(path.sum()) * fps / sfps     # px travelled: speeds are per 1/fps s, frames 1/sfps s apart
        if k - a >= 3 and L >= 40:
            k80 = int(np.searchsorted(np.cumsum(path), 0.8 * path.sum())) + 1
            moves.append({"t0": round(a / sfps, 2), "t1": round(k / sfps, 2), "path": round(L), "t80": round(k80 / (k - a), 2), "peak": round(float(path.max()))})
    total = sum(m["path"] for m in moves)
    med = None
    if moves:
        acc = 0.0
        for m in sorted(moves, key=lambda m: m["t80"]):
            acc += m["path"]
            if acc >= total / 2:
                med = m["t80"]; break
    return {"fps": fps, "sampled_fps": round(sfps, 3), "peak": round(float(speed.max())), "moves": moves, "t80_median": med,
            "soft_share": round(sum(m["path"] for m in moves if m["t80"] >= 0.55) / total, 2) if total else 0.0,
            "fast_frames": len(smear), "smear_median": round(float(np.median(smear)), 2) if smear else None}

def sheets(video, out, fps=4):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps={fps},scale=426:-1,tile=6x4", f"{out}/sheet_%02d.png"], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip())
    for i in range(9):
        t = dur * (i + 0.5) / 9
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", f"{out}/frame_{i:02d}.png"], check=True)
    return dur

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--out", default="ana"); ap.add_argument("--no-flow", action="store_true"); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    d, fps = energy(a.video, a.out); m = energy_map(d, fps); s = stats(d, fps)
    fl = None if a.no_flow else flow(a.video)
    if fl: s["flow"] = fl
    open(os.path.join(a.out, "energy.txt"), "w").write(m + "\n" + json.dumps({k: v for k, v in s.items() if k != "flow"}) + "\n")
    json.dump(s, open(os.path.join(a.out, "summary.json"), "w"), indent=1)
    sheets(a.video, a.out)
    print(m); print()
    print(f"still (<0.5): {s['still_ratio']}   low (<2): {s['low_ratio']}   longest quiet: {s['longest_quiet_s']} s")
    print(f"cuts at: {s['cuts']}"); print(f"bursts: {s['bursts']}")
    if fl:
        blur = "no fast frames" if fl["smear_median"] is None else f"smear {fl['smear_median']} over {fl['fast_frames']} fast frames ({'smeared along the motion: shutter blur' if fl['smear_median'] < SMEAR_BLUR else 'sharp: no shutter blur'})"
        med = "—" if fl["t80_median"] is None else fl["t80_median"]
        print(f"motion: peak {fl['peak']} px/frame @{fl['fps']} · {len(fl['moves'])} moves · median t80 {med} · soft curves {fl['soft_share'] * 100:.0f} % of travel · {blur}")
    elif not a.no_flow:
        print("motion: skipped (opencv-python not installed)")
    print(f"\nsheets + frames in {a.out}/ — look at them before writing the beat sheet")

if __name__ == "__main__":
    main()
