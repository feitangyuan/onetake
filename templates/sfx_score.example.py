#!/usr/bin/env python3
# onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
"""sfx_score.example.py — the motion-web-15s score, written on scripts/sfx_palette.py.

Copy next to your comp, edit the events, run:  python3 sfx_score.py  → sfx.wav (48 kHz, peak -8 dBFS)
Every `s.place(material, t, gain, pan, send, pan_to)` is a beat from the composition's timeline; pans come
from where the thing is on screen (pan_of(x)). Fewer events than beats. references/sound.md.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))   # or the skill's scripts dir
from sfx_palette import Score, air, glass, wood, sub, bubble, wobble, pan_of
import numpy as np
rng = np.random.default_rng(7)
s = Score(dur=15.0, T60=1.1)
place = s.place

# ── the score ──────────────────────────────────────────────────────────────
# 1 · words: three glass touches, low, spaced — the quiet opening
for t,f in zip((0.15,0.50,0.92),(659,784,523)): place(glass(f,0.8,0.6),t,0.16,0.0,0.45)
# 2 · wordmark: one rising breath of air as the letters drop in, a rounded pop when "move" wobbles
place(air(0.7,180,1800,1.2,0.6),1.62,0.28,-0.15,0.5,pan_to=0.15)
place(bubble(420,0.26),2.30,0.30,0.05,0.3)
place(air(0.35,1400,300,1.3),2.98,0.20,0.0,0.4)                       # the mark folds to the corner
# 3 · prompt: muted keys (about one in three, velocity varies), then a real click
TXT='make the hero feel alive — springs, not fades'
for i,ch in enumerate(TXT):
    if ch in ' —' or rng.uniform()<0.35: continue
    place(wood(170+rng.uniform(-20,20),0.09),3.15+i/38+rng.uniform(0,0.003),0.10*rng.uniform(0.7,1.3),-0.05,0.15)
place(wood(240,0.08),4.45,0.32,pan_of(1290),0.2); place(wood(190,0.07),4.51,0.22,pan_of(1290),0.2)   # down / up
place(air(0.3,2200,400,1.5),4.75,0.18,0.0,0.4)                                                          # prompt leaves
# 4 · panel: seven glass ticks up a scale, PASS as a soft two-note chord
place(air(0.32,300,2400,1.3),4.85,0.18,0.0,0.4)
for i,f in enumerate((523,587,659,784,880,1046,1318)):
    place(glass(f,0.6,0.8),5.15+i*0.24,0.15 if i<6 else 0.0,-0.1,0.4)
place(glass(1318,1.3,0.5),6.59,0.16,-0.05,0.6); place(glass(1976,1.3,0.4),6.61,0.11,0.05,0.6)         # PASS
place(air(0.3,2200,400,1.5),7.0,0.18,0.0,0.4)
# 5 · pages fly through: air that travels right→left with the picture, a felt landing as each settles
for t in (7.05,7.95,8.85):
    place(air(0.5,220,3000,1.3,0.35),t-0.03,0.55,0.6,0.5,pan_to=-0.1)
    place(sub(70,0.5),t+0.16,0.22,0.0,0.3)
    place(air(0.4,2600,260,1.4,0.3),t+0.88,0.35,-0.1,0.5,pan_to=-0.7)
# 6 · micro cards: a bubble as each lands; the mechanism gets exactly one sound
minis=[(9.55,10.40,700),(10.00,10.95,1320),(10.75,11.60,930),(11.35,12.15,1410)]
for t0,t1,x in minis: place(bubble(480+rng.uniform(-40,40),0.24),t0+0.02,0.26,pan_of(x),0.3); place(air(0.26,1600,300,1.4),t1,0.14,pan_of(x),0.4)
place(wood(240,0.08),10.05,0.30,pan_of(700),0.2); place(wood(190,0.07),10.11,0.20,pan_of(700),0.2)   # magnetic button click
place(wobble(150,0.6),11.03,0.42,pan_of(930),0.35)                                                     # jelly
place(air(0.22,700,3200,2.0),11.60,0.18,pan_of(1410),0.4,pan_to=pan_of(1500))                          # string swept
# 7 · the window: one long breath in, then silence
place(air(0.7,200,2000,1.1,0.5),12.08,0.40,0.0,0.6)
place(sub(58,0.8),12.22,0.20,0.0,0.4)
# 8 · hard cuts: four felt hits, then the deep one under black
for i,t in enumerate((13.25,13.50,13.72,13.94)): place(sub(72-i*3,0.5),t,0.40,0.0,0.25)
place(sub(48,1.2),14.30,0.58,0.0,0.45); place(glass(392,1.6,0.3),14.34,0.10,0.0,0.7)


s.write(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx.wav"))
