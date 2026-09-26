#!/usr/bin/env python3
# onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
"""sfx_palette.py — the sound materials, one shared room, and a Score helper.

    import sys; sys.path.insert(0, "<skill>/scripts"); from sfx_palette import *
    s = Score(dur=15)
    s.place(glass(659, 0.8, 0.6), t=0.15, gain=0.16, send=0.45)
    s.place(air(0.5, 220, 3000, 1.3, 0.35), t=7.02, gain=0.55, pan=0.6, send=0.5, pan_to=-0.1)
    s.write("sfx.wav")                       # 48 kHz stereo, peak -8 dBFS, soft-limited

    python3 scripts/sfx_palette.py --demo demo.wav     # every material once, to listen

Materials: air (whoosh), glass (struck tone), wood (key / click), sub (felt hit), bubble (rounded pop),
wobble (jelly). All return mono float arrays at SR; gains in Score.place set the level.
Design notes: references/sound.md.
"""
import numpy as np, wave, os
from scipy import signal

SR = 48000
_rng = np.random.default_rng(7)

def _t(n): return np.arange(n) / SR
def bp(x, f, q=1.0):
    f = float(np.clip(f, 30, SR / 2 - 100)); b, a = signal.iirpeak(f / (SR / 2), q); return signal.lfilter(b, a, x)
def lp(x, f, order=2):
    b, a = signal.butter(order, float(np.clip(f, 30, SR / 2 - 100)) / (SR / 2)); return signal.lfilter(b, a, x)
def hp(x, f, order=2):
    b, a = signal.butter(order, float(np.clip(f, 20, SR / 2 - 100)) / (SR / 2), "high"); return signal.lfilter(b, a, x)
def sweep_bp(x, f0, f1, q=1.0, blocks=24):
    n = len(x); out = np.zeros(n); L = n // blocks + 1
    for i in range(blocks):
        a = i * L; b = min(n, a + L); f = f0 * (f1 / f0) ** (i / (blocks - 1))
        out[a:b] = bp(x[max(0, a - 400):b], f, q)[-(b - a):]
    return out
def sat(x, k=1.6): return np.tanh(x * k) / np.tanh(k)

# ── materials ──────────────────────────────────────────────────────────────
def air(dur=0.45, f0=250, f1=2600, q=1.4, shape=0.45):
    """a soft whoosh: filtered air whose centre glides f0→f1; shape = where the envelope peaks (0..1)"""
    n = int(SR * dur); x = sweep_bp(_rng.standard_normal(n), f0, f1, q); x = lp(x, 5500)
    t = _t(n) / dur; e = np.sin(np.pi * np.clip(t, 0, 1)) ** 1.4 * np.where(t < shape, t / shape, 1)
    return x * e / (np.abs(x * e).max() + 1e-9)
def glass(f, dur=0.9, bright=1.0):
    """a small struck tone: fundamental + inharmonic partials + a fast noise transient"""
    n = int(SR * dur); t = _t(n)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 6) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 14) * bright + 0.18 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 24) * bright
    tr = lp(hp(_rng.standard_normal(n), 2000), 9000) * np.exp(-t * 220) * 0.5
    return (s * 0.7 + tr) / 1.2
def wood(f=180, dur=0.12):
    """a muted knock: low body with a pitch drop + a short filtered snap (keys, mouse down/up)"""
    n = int(SR * dur); t = _t(n)
    body = np.sin(2 * np.pi * f * t * (1 + 0.3 * np.exp(-t * 90))) * np.exp(-t * 60)
    snap = bp(_rng.standard_normal(n), 3200, 2.2) * np.exp(-t * 380)
    return body * 0.9 + snap * 0.5
def sub(f=62, dur=0.7):
    """a felt low hit: sine with a pitch drop, gently saturated"""
    n = int(SR * dur); t = _t(n); ph = np.cumsum(2 * np.pi * (f + f * 2.2 * np.exp(-t * 28)) / SR)
    s = np.sin(ph) * np.exp(-t * 5.5); tr = lp(_rng.standard_normal(n), 500) * np.exp(-t * 90) * 0.8
    return sat(s * 1.1 + tr * 0.5, 1.8)
def bubble(f=520, dur=0.22):
    """a rounded pop: a resonance rising as it closes"""
    n = int(SR * dur); t = _t(n); ph = np.cumsum(2 * np.pi * (f * (1 + 0.9 * (1 - np.exp(-t * 30)))) / SR)
    return np.sin(ph) * np.exp(-t * 26) * 0.9 + bp(_rng.standard_normal(n), f * 3, 3) * np.exp(-t * 200) * 0.4
def wobble(f=150, dur=0.6):
    """jelly: an FM'd tone whose vibrato dies out"""
    n = int(SR * dur); t = _t(n); ph = np.cumsum(2 * np.pi * f * (1 + 0.10 * np.sin(2 * np.pi * 8.5 * t) * np.exp(-t * 3.5)) / SR)
    return lp(np.sin(ph) + 0.25 * np.sin(2 * ph), 1400) * np.exp(-t * 5.5)
def pan_of(x, width=1920): return float(np.clip((x - width / 2) / (width / 2) * 0.6, -0.7, 0.7))

# ── the room + the score ───────────────────────────────────────────────────
def impulse(T60=1.1):
    n = int(SR * T60 * 1.3); t = _t(n); ir = _rng.standard_normal((n, 2)) * np.exp(-6.9 * t / T60)[:, None]
    ir = np.stack([lp(ir[:, 0], 3800), lp(ir[:, 1], 3400)], 1); ir[:int(SR * 0.012)] *= 0
    for d, g in ((0.017, 0.5), (0.029, 0.35), (0.041, 0.25)): ir[int(d * SR):int(d * SR) + 2] += g * _rng.uniform(0.5, 1, (2, 2))
    return ir / np.abs(ir).sum(0).max() * 4

class Score:
    def __init__(self, dur=15.0, T60=1.1):
        self.dur = dur; n = int(SR * (dur + 2)); self.dry = np.zeros((n, 2)); self.wet = np.zeros((n, 2)); self.T60 = T60; self.events = []
    def place(self, sig, t, gain=1.0, pan=0.0, send=0.25, pan_to=None):
        sig = np.asarray(sig, dtype=float); i0 = int(t * SR); n = len(sig)
        p = np.linspace(pan, pan if pan_to is None else pan_to, n); L = np.sqrt(0.5 * (1 - p)); R = np.sqrt(0.5 * (1 + p))
        self.dry[i0:i0 + n, 0] += sig * gain * L; self.dry[i0:i0 + n, 1] += sig * gain * R
        self.wet[i0:i0 + n, 0] += sig * gain * send * L; self.wet[i0:i0 + n, 1] += sig * gain * send * R
        self.events.append(round(t, 3))
    def mix(self, peak_db=-8.0):
        ir = impulse(self.T60); rev = np.stack([signal.fftconvolve(self.wet[:, c], ir[:, c])[:len(self.dry)] for c in (0, 1)], 1)
        m = self.dry + rev * 0.9; m = np.stack([hp(m[:, c], 38) for c in (0, 1)], 1)
        m = sat(m / (np.abs(m).max() + 1e-9) * 0.9, 1.3); m = m / np.abs(m).max() * 10 ** (peak_db / 20)
        return m[:int(SR * self.dur)]
    def write(self, path, peak_db=-8.0):
        m = self.mix(peak_db)
        with wave.open(path, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((m * 32767).astype(np.int16).tobytes())
        print(f"{path}: {len(self.events)} events, peak {peak_db} dBFS")

def demo(path):
    s = Score(dur=9)
    s.place(glass(659, 0.9), 0.3, 0.3, send=0.5); s.place(glass(1318, 1.2, 0.5), 1.0, 0.25, send=0.6)
    s.place(wood(180), 2.0, 0.4); s.place(wood(240, 0.08), 2.6, 0.4); s.place(wood(190, 0.07), 2.66, 0.3)
    s.place(air(0.5, 220, 3000), 3.3, 0.6, 0.6, 0.5, pan_to=-0.4)
    s.place(bubble(480), 4.5, 0.4, send=0.3); s.place(wobble(150), 5.3, 0.5, send=0.35)
    s.place(sub(70, 0.6), 6.4, 0.5); s.place(sub(48, 1.2), 7.3, 0.6, send=0.45)
    s.write(path)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--demo", default=None); a = ap.parse_args()
    if a.demo: demo(a.demo)
    else: print(__doc__)
