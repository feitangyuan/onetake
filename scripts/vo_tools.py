#!/usr/bin/env python3
# onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
"""vo_tools.py — narration for a film: voice lines, word times, line starts, subtitles. One line of lines.txt = one VO line.

  KPY=~/.cache/kokoro/venv/bin/python
  $KPY  vo_tools.py tts   vo/lines.txt --voice bf_emma --lang en-gb --out vo/bf_emma            # Kokoro, local; see --lang
  $KPY  vo_tools.py tts   vo/ja/lines.txt --read vo/ja/read.txt --voice jf_alpha --lang ja --out vo/ja/jf_alpha
  python3 vo_tools.py words vo/bf_emma --lang en --lines vo/lines.txt                            # faster-whisper → words.json
  python3 vo_tools.py plan  vo/bf_emma --lead 0.5 --breath 0.45 --gap 7:2.45                     # → plan.json: durs, VO starts
  python3 vo_tools.py subs  vo/lines.txt vo/bf_emma --max 42                                     # → subs.json [[t0, t1, text], …]

tts      each line → t<i>.wav (48 kHz mono), silence trimmed and inner pauses squeezed to --gap-in (Kokoro stops ~0.6 s at
         every full stop; 0.28 s reads as one speaker talking). `--lines 2,4` renders only those; `--sample` writes one
         joined <voice>.m4a instead of per-line files (auditions). Japanese: Kokoro's default espeak cannot read kanji —
         pass --read, a kana reading of each line (names spelled as they are said: エクセル, エイチティーエムエル),
         phonemised by misaki[ja] (+ unidic-lite) in the Kokoro venv. The subtitles still use lines.txt.
words    word-level times per line (faster-whisper small, CPU). English: when the count matches the line, the line's own
         words replace whisper's spelling (it hears brand names wrong). Japanese comes back as characters in whatever
         script whisper chose (kana for a katakana name, even a wrong kanji) — use it to find anchors by ear-order, not text.
plan     line starts: --lead before line 1, --breath between lines, --gap i:s for a longer music gap before line i.
         Continuous narration is the default; a gap is for a stretch where the picture carries on its own.
subs     each line split at its punctuation into chunks of at most --max characters (Latin) / --max-cjk (CJK), timed
         from the words: by word index for English, for CJK by the reading's proportion snapped to the nearest pause.
"""
import argparse, json, os, re, subprocess, sys

SR = 48000


def read_lines(p):
    return [l.strip() for l in open(p, encoding="utf-8") if l.strip()]


def is_cjk(s):
    return bool(re.search(r"[぀-ヿ㐀-鿿가-힯]", s))


# ── tts ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def trim(x, thr=10 ** (-45 / 20), gap=0.28):
    import numpy as np
    idx = np.where(np.abs(x) > thr)[0]
    x = x[max(0, idx[0] - 240): idx[-1] + 2400] if len(idx) else x
    env = np.convolve(np.abs(x), np.ones(480) / 480, "same") > thr
    out, i, n, keep = [], 0, len(x), int(gap * SR)
    while i < n:
        j = i
        while j < n and env[j] == env[i]:
            j += 1
        chunk = x[i:j]
        if not env[i] and len(chunk) > keep and 0 < i and j < n:
            h = keep // 2; chunk = np.concatenate([chunk[:h], chunk[-h:]])
        out.append(chunk); i = j
    return np.concatenate(out)


def cmd_tts(a):
    import numpy as np, soundfile as sf
    from kokoro_onnx import Kokoro
    from scipy.signal import resample_poly
    K = os.path.expanduser("~/.cache/kokoro")
    tts = Kokoro(os.path.join(K, "kokoro-v1.0.onnx"), os.path.join(K, "voices-v1.0.bin"))
    lines = read_lines(a.read or a.lines)
    g2p = None
    if a.lang == "ja":
        from misaki import ja
        g2p = ja.JAG2P()
    pick = [int(i) for i in a.pick.split(",")] if a.pick else list(range(1, len(lines) + 1))
    os.makedirs(a.out, exist_ok=True); parts, durs = [], []
    for i in pick:
        if g2p:
            ph, _ = g2p(lines[i - 1]); x, sr = tts.create(ph, voice=a.voice, speed=a.speed, is_phonemes=True)
        else:
            x, sr = tts.create(lines[i - 1], voice=a.voice, speed=a.speed, lang=a.lang)
        x = trim(resample_poly(np.asarray(x, np.float64), SR, sr), gap=a.gap_in).astype(np.float32); durs.append(len(x) / SR)
        if not a.sample:
            sf.write(os.path.join(a.out, f"t{i}.wav"), x, SR)
        parts += [x, np.zeros(int(0.45 * SR), np.float32)]
    wav = os.path.join(a.out, f"{a.voice}.wav"); sf.write(wav, np.concatenate(parts), SR)
    subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", wav, "-c:a", "aac", "-b:a", "160k", wav[:-4] + ".m4a"]); os.remove(wav)
    print(a.voice, "lines", pick, " ".join(f"{d:.2f}" for d in durs), f"total {sum(durs):.1f}s →", wav[:-4] + ".m4a")


# ── words ────────────────────────────────────────────────────────────────────────────────────────────────────────────
def wavs(d):
    return sorted((int(m.group(1)), os.path.join(d, f)) for f in os.listdir(d) for m in [re.match(r"t(\d+)\.wav$", f)] if m)


def cmd_words(a):
    from faster_whisper import WhisperModel
    m = WhisperModel(a.model, device="cpu", compute_type="int8")
    lines = read_lines(a.lines) if a.lines else None
    out = {}
    for i, p in wavs(a.dir):
        segs, _ = m.transcribe(p, language=a.lang, word_timestamps=True)
        w = [[x.word.strip(), round(x.start, 2), round(x.end, 2)] for s in segs for x in s.words]
        if lines and not is_cjk(lines[i - 1]):
            own = lines[i - 1].split()
            if len(own) == len(w):
                w = [[o, s, e] for o, (_, s, e) in zip(own, w)]
            else:
                print(f"  line {i}: whisper heard {len(w)} words, the line has {len(own)} — kept whisper's spelling", file=sys.stderr)
        out[str(i)] = w
        print(i, " ".join(f"{x[0]}@{x[1]:.2f}" for x in w))
    json.dump(out, open(os.path.join(a.dir, "words.json"), "w"), ensure_ascii=False)


# ── plan ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)


def cmd_plan(a):
    gaps = {int(k): float(v) for k, v in (g.split(":") for g in a.gap)}
    ds = [dur(p) for _, p in wavs(a.dir)]; vo, t = [], a.lead
    for i, d in enumerate(ds, 1):
        if i > 1:
            t += gaps.get(i, a.breath)
        vo.append(round(t, 2)); t += d
    plan = {"durs": [round(d, 3) for d in ds], "VO": vo, "end": round(t, 2)}
    json.dump(plan, open(os.path.join(a.dir, "plan.json"), "w")); print(json.dumps(plan))


# ── subs ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def clauses(line):
    cj = is_cjk(line)
    parts = re.findall(r"[^、。？！,.?!]+[、。？！,.?!」』]*\s*" if cj else r"[^,.?!;:]+[,.?!;:]*\s*", line)
    return [p.strip() for p in parts if p.strip()] or [line]


def chunks(line, mx):
    """→ [(text, n_clauses)]: clauses merged left to right while they fit in mx and no sentence ends between them;
    a stub under mx/3 (「だから、」, "So,") joins the next clause even if that runs to 1.3 × mx."""
    cj, out = is_cjk(line), []
    for p in clauses(line):
        if out and not re.search(r"[。？！.?!]$", out[-1][0]) and (len(out[-1][0]) + len(p) <= mx or (len(out[-1][0]) < mx / 3 and len(out[-1][0]) + len(p) <= 1.3 * mx)):
            out[-1] = (out[-1][0] + ("" if cj else " ") + p, out[-1][1] + 1)
        else:
            out.append((p, 1))
    return out


def morae(s):
    """rough spoken length of a Japanese string: kanji ~2 morae, small kana and punctuation ~0, the rest 1"""
    return sum(2 if "\u3400" <= ch <= "\u9fff" else 0 if ch in "ゃゅょャュョぁぃぅぇぉァィゥェォ、。？！「」 " else 1 for ch in s)


def cmd_subs(a):
    lines = read_lines(a.lines); reads = read_lines(a.read) if a.read else lines
    words = json.load(open(os.path.join(a.dir, "words.json"))); plan = json.load(open(os.path.join(a.dir, "plan.json")))
    subs = []
    for i, line in enumerate(lines, 1):
        t0, d, w = plan["VO"][i - 1], plan["durs"][i - 1], words.get(str(i), [])
        cs, starts = chunks(line, a.max_cjk if is_cjk(line) else a.max), [0.0]
        if is_cjk(line):
            # the reading keeps the line's punctuation: the share of its morae spoken before a chunk says roughly
            # when the chunk starts; snap to the widest pause within 0.8 s of that, preferring the nearer
            rc = clauses(reads[i - 1]) if len(clauses(reads[i - 1])) == len(clauses(line)) else clauses(line)
            n, tot = 0, sum(morae(c) for c in rc)
            for _, k in cs[:-1]:
                n += k; est = d * sum(morae(c) for c in rc[:n]) / tot
                gaps = [(w[j][1] - w[j - 1][2] - 0.3 * abs(w[j][1] - est), w[j][1]) for j in range(1, len(w)) if abs(w[j][1] - est) < 0.8]
                starts.append(max(gaps)[1] if gaps else est)
        else:
            n = 0
            for c, _ in cs[:-1]:
                n += len(c.split()); starts.append(w[n][1] if n < len(w) else d * n / max(1, len(line.split())))
        for j, (c, _) in enumerate(cs):
            s0 = t0 + starts[j] - (0.05 if j == 0 else 0)
            e = t0 + starts[j + 1] if j + 1 < len(cs) else t0 + d + 0.05
            subs.append([round(s0, 2), round(e, 2), c])
    json.dump(subs, open(os.path.join(a.dir, "subs.json"), "w"), ensure_ascii=False)
    for q in subs:
        print(f"{q[0]:6.2f} {q[1]:6.2f}  {q[2]}")


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = ap.add_subparsers(dest="cmd", required=True)
p = sp.add_parser("tts"); p.add_argument("lines"); p.add_argument("--voice", required=True); p.add_argument("--lang", default="en-us", help="en-us | en-gb | ja")
p.add_argument("--read", help="a reading per line to speak instead (Japanese: kana)"); p.add_argument("--speed", type=float, default=1.0); p.add_argument("--gap-in", type=float, default=0.28)
p.add_argument("--lines", dest="pick", default=""); p.add_argument("--sample", action="store_true"); p.add_argument("--out", required=True); p.set_defaults(f=cmd_tts)
p = sp.add_parser("words"); p.add_argument("dir"); p.add_argument("--lang", default="en"); p.add_argument("--lines"); p.add_argument("--model", default="small"); p.set_defaults(f=cmd_words)
p = sp.add_parser("plan"); p.add_argument("dir"); p.add_argument("--lead", type=float, default=0.5); p.add_argument("--breath", type=float, default=0.45)
p.add_argument("--gap", nargs="*", default=[], help="i:s — s seconds before line i instead of the breath"); p.set_defaults(f=cmd_plan)
p = sp.add_parser("subs"); p.add_argument("lines"); p.add_argument("dir"); p.add_argument("--read"); p.add_argument("--max", type=int, default=42); p.add_argument("--max-cjk", type=int, default=20); p.set_defaults(f=cmd_subs)
a = ap.parse_args(); a.f(a)
