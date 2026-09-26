#!/usr/bin/env python3
# onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
"""verify_promo.py — does the cut have a rhythm, and does it carry? The checks that fail a slideshow before a human has to.

  python3 scripts/verify_promo.py film.mp4 --comp comp.html --ref ref.mp4 --shots 0,1.6,3.0,4.8,7.0,9.6,12.1,13.25,14.3

Legs (each prints a number and PASS / WARN / FAIL; only FAIL fails the verdict):
  cadence     shot lengths (from --shots) must vary: coefficient of variation >= 0.25. Equal shots = slides.
  rest        >= 25 % of frames dead-still (<0.5 mean abs diff at 320 px) and one quiet stretch >= 1.0 s.
  burst       a window of 1.5 s holding >= 3 big changes (> 8). FAIL only when --ref has a burst and the film has none;
              otherwise WARN — a concept without hits (one element transforming, one camera move) is not a defect.
  not-flat    advisory: the energy map's row profile varies (std of row means / grand mean >= 0.35). It passed the
              rejected Pocket Weather v1 (0.54) and failed the accepted v3 (0.33), so it no longer decides.
  audio       (if the file has audio) peak <= -3 dBFS, 0 clipped samples, >= 15 % of 1/12 s frames quiet.
  continuity  (with --comp) probe.py's carry score: FAIL < 0.5, WARN < 0.7. Every rhythm leg above passed both rejected
              Pocket Weather cuts; this one fails them (v1 0.00, v2 0.40; accepted motion-web 0.56, v3 0.75).
  curves      (with --comp) FAIL when something travels more than 80 px per frame (normalised to 1920 wide, at the
              film's fps) in a film without shutter blur: a render defect, fixed by rendering with render.py. Blur is
              read from <film>.render.json (render.py writes it), else from the film itself (analyze_ref.py smear
              < .78). Soft-curve share and median t80 are printed, not judged: they did not separate accepted from
              rejected cuts (motion-web 70 %, v1 72 %, v2 57 %, v3 69 % of travel on soft curves).
  framing     (with --comp and window.__meta.inFrame) FAIL when a declared id is entirely off frame at any sampled frame
              inside its window, or — marked 'whole' — not wholly inside. The one-dot film's first camera render lost its
              dot behind a snap the camera's spring couldn't follow; nothing else caught it.
  reference   (with --ref) both energy maps, then stillness, cuts and the flow fingerprint side by side; no verdict.
Exit code 1 if any leg fails.
"""
import argparse, asyncio, json, os, subprocess, sys, tempfile, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_ref import energy, energy_map, stats, flow, SMEAR_BLUR

PEAK_PX = 80

def audio_stats(video):
    tmp = tempfile.mkdtemp(); wav = os.path.join(tmp, "a.wav")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vn", "-ac", "2", "-ar", "48000", wav], capture_output=True)
    if r.returncode != 0 or not os.path.exists(wav): return None
    w = wave.open(wav); x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2) / 32767; w.close()
    n = 4000; rms = np.array([np.sqrt((x[i:i + n] ** 2).mean()) for i in range(0, len(x) - n, n)])
    return {"peak_db": round(20 * np.log10(np.abs(x).max() + 1e-9), 1), "clipped": int((np.abs(x) >= 0.999).sum()),
            "quiet_ratio": round(float((20 * np.log10(rms + 1e-9) < -40).mean()), 3)}

def leg(name, state, detail):
    print(f"  {state:4}  {name:10} {detail}"); return state != "FAIL"

def film_fps(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", video], capture_output=True, text=True).stdout.strip()
    num, _, den = r.partition("/")
    try: return max(1, int(round(float(num) / float(den or 1))))
    except ValueError: return 30

def render_info(video):
    p = os.path.splitext(video)[0] + ".render.json"
    return json.load(open(p)) if os.path.exists(p) else None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("--ref", default=None); ap.add_argument("--shots", default=None)
    ap.add_argument("--comp", default=None, help="the composition the film was rendered from — adds the continuity and curves legs")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(); d, fps = energy(a.video, tmp); s = stats(d, fps); m = energy_map(d, fps)
    print(f"\n{os.path.basename(a.video)} — energy map:\n{m}\n"); oks = []
    if a.shots:
        ts = sorted(float(x) for x in a.shots.split(",")); L = np.diff(ts + [s["duration_s"]]); cv = float(L.std() / L.mean())
        oks.append(leg("cadence", "PASS" if cv >= 0.25 else "FAIL", f"shot lengths {np.round(L,2).tolist()}  CV {cv:.2f} (need >= 0.25)"))
    else: print("  skip  cadence    (pass --shots t0,t1,… to check shot-length variety)")
    oks.append(leg("rest", "PASS" if s["still_ratio"] >= 0.25 and s["longest_quiet_s"] >= 1.0 else "FAIL", f"still {s['still_ratio']}  longest quiet {s['longest_quiet_s']} s"))
    dr = sr = None
    if a.ref: dr, _ = energy(a.ref, tmp); sr = stats(dr, fps)
    if s["bursts"]: oks.append(leg("burst", "PASS", f"bursts {s['bursts']}"))
    elif sr is not None and sr["bursts"]: oks.append(leg("burst", "FAIL", f"no burst; the reference has {len(sr['bursts'])} {sr['bursts']}"))
    else: oks.append(leg("burst", "WARN", "no burst — the reference has none either" if sr is not None else "no burst — fine for a concept without hits; --ref holds it to a reference"))
    rows = [d[i:i + fps * 4].mean() for i in range(0, len(d), fps * 4)]; flat = float(np.std(rows) / (np.mean(rows) + 1e-9))
    oks.append(leg("not-flat", "PASS" if flat >= 0.35 else "WARN", f"row-profile variation {flat:.2f} (advisory, >= 0.35)"))
    au = audio_stats(a.video)
    if au: oks.append(leg("audio", "PASS" if au["peak_db"] <= -3 and au["clipped"] == 0 and au["quiet_ratio"] >= 0.15 else "FAIL", f"peak {au['peak_db']} dBFS  clipped {au['clipped']}  quiet {au['quiet_ratio']}"))
    else: print("  skip  audio      (no audio track)")
    info = render_info(a.video)
    ff = flow(a.video) if a.ref or (a.comp and not info) else None
    if a.comp:
        import probe
        vfps = film_fps(a.video)
        res = asyncio.run(probe.collect(a.comp, fps=vfps)); ct = probe.continuity(res); cv = probe.curves(res)
        bare = [e["t"] for e in ct["events"] if not e["exempt"] and e["kind"] == "bare"]
        state = "FAIL" if ct["score"] < 0.5 else "WARN" if ct["score"] < 0.7 else "PASS"
        oks.append(leg("continuity", state, f"carry score {ct['score']:.2f} over {ct['considered']} boundaries; nothing carried at {bare or '—'} (probe.py lists each)"))
        if info:
            blurred = info.get("shutter", 0) > 0
            blur = f"shutter {info['shutter']:g}° (render.json)" if blurred else "rendered with --shutter 0"
        else:
            sm = ff["smear_median"] if ff else None
            blurred = sm is not None and sm < SMEAR_BLUR
            blur = ("no render.json and no opencv to read the film: assumed sharp" if ff is None else
                    "no render.json, and no fast frames in the film to read blur from" if sm is None else
                    f"no render.json, film smear {sm:g} ({'blurred' if blurred else 'sharp'})")
        state = "FAIL" if cv["peak"] > PEAK_PX and not blurred else "PASS"
        where = f" ({cv['peak_at'][0]} at {cv['peak_at'][1]:.2f} s)" if cv["peak_at"] else ""
        med = f"{cv['t80_median']:.2f}" if cv["t80_median"] is not None else "—"
        oks.append(leg("curves", state, f"peak {cv['peak']:.0f} px/frame @{vfps} fps{where}, {blur}; soft curves {cv['soft_share'] * 100:.0f} % of travel, median t80 {med}"))
        fr = probe.framing(res)
        if fr:
            off = {k: v["bad"] for k, v in fr.items() if v["bad"]}
            detail = ("; ".join(f"{k} off frame at {len(b)} samples {b[:6]}" for k, b in off.items()) if off else
                      "; ".join(f"{k} {'wholly ' if v['whole'] else ''}in frame {v['window'][0]:g}–{v['window'][1]:g} s ({v['samples']} samples)" for k, v in fr.items()))
            oks.append(leg("framing", "FAIL" if off else "PASS", detail))
        else:
            print("  skip  framing    (declare window.__meta.inFrame = {id: [t0, t1] | [t0, t1, 'whole']} to check what must stay in frame)")
        if res.get("failed"):
            print(f"  !!    __seek threw at {len(res['failed'])} samples (first t={res['failed'][0][0]}): {res['failed'][0][1]}")
    if a.ref:
        print(f"\nreference — energy map:\n{energy_map(dr, fps)}")
        rows = [("still", s["still_ratio"], sr["still_ratio"]), ("low", s["low_ratio"], sr["low_ratio"]), ("cuts", len(s["cuts"]), len(sr["cuts"])),
                ("bursts", len(s["bursts"]), len(sr["bursts"])), ("quiet s", s["longest_quiet_s"], sr["longest_quiet_s"])]
        fr = flow(a.ref) if ff else None
        if ff and fr:
            rows += [("peak px/f", ff["peak"], fr["peak"]), ("t80 median", ff["t80_median"], fr["t80_median"]),
                     ("soft %", round(ff["soft_share"] * 100), round(fr["soft_share"] * 100)), ("smear", ff["smear_median"], fr["smear_median"])]
        print(f"\n              {'film':>8} {'reference':>10}")
        for k, x, y in rows:
            print(f"  {k:11} {'—' if x is None else x:>8} {'—' if y is None else y:>10}")
    print("\nVERDICT:", "PASS" if all(oks) else "FAIL"); sys.exit(0 if all(oks) else 1)

if __name__ == "__main__":
    main()
