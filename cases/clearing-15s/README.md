# clearing-15s — the one-take dive through scale

> This folder ships the film only. Its source (the composition, the score, the sound sources) is not part of the
> public release; files named below describe how it was made.
>
> The film: `clearing.mp4`


The fifth film: 15 s, 1920×1080, 30 fps draft, one canvas, zero assets, a fictional product (clearing, a calendar that
keeps time free). Made in Claude Code with this skill on 2026-09-14. The user left concept, palette, camera and visual
elements entirely to Claude; the first draft was accepted with 「牛逼牛逼 太牛逼了，你找到了技巧。神来之笔」.

Project: this folder.
- `comp.html` is the film; `clearing.mp4` is the film with sound.
- `dump_events.py` writes `events.json` and `zoom.json`; `score.py` turns them into `mix.wav`.
- `sfx-src` is a link to the one-dot film's sources.

In this folder:
- `comp.html` runs in place on the skill's `lib/motion.js`. Its frames at seven times and its `__events()` match the
  project's byte for byte.
- `clearing.mp4` is the accepted draft, with sound.
- `clearing.render.json` is its render record.

## Why it is a case

- **Carry by scale.** Case 2 carried by containers, case 3 by one element's identity, case 4 by cause. Here nothing is
  ever replaced because every level is inside the one before: the year holds the day, the day holds the gap, the gap
  holds the block. The yellow found at the bottom of the dive is the yellow the year ends in.
- **A camera that works at 1× and at 300×.** `OM.rig` chases the anchor's **screen position** and the log of the zoom,
  not a world position. At 300× a world-space spring swings the target a frame-width for every pixel of lag; a
  screen-space spring lags and settles the same at every scale. The camera is recovered from it (below).
- **Levels drawn in their own units.** A day is a 1440 px page inside a 24 px cell, drawn through a composed matrix
  `mul(VIEW, [s, 0, 0, s, ox, oy])`. Type is set at normal sizes and stays crisp at any zoom; detail fades in by the
  cell's size on screen (level of detail), so the year never draws 364 pages.
- **The camera is the instrument.** The comp exports the zoom's speed; the air under both dives and the whip out is as
  loud as that speed and as bright as the depth. Two held silences sit around the one landing.
- **The word was in the data.** CLEARING is a 5×7 pixel font laid over the year's grid; the kept days are those cells.
  The target day (col 30, row 2) happens to sit inside the R, so the first kept half hour is part of the name.

## Beat sheet

| t | beat | moves | carries into the next beat |
|---|---|---|---|
| 0.20–1.30 | the year fills | 364 days pop in, a wave left to right | the grid |
| 1.00–1.80 | 2027 · 2,184 events · 0 hours free | the header types; a hold | the grid |
| 1.80–3.60 | dive | the camera falls into Wed 28 Jul; the day's hours resolve | the day |
| 3.60–4.80 | scan | a yellow line sweeps the day, decelerating, and stops at 15:00 | the gap |
| 4.80–5.60 | the gap | a dashed outline and "15:00–15:30 · free"; a held breath | the gap |
| 5.60–7.00 | dive | into the half hour, 50× → 300× | the slot |
| 7.00–7.60 | inside | a minute ruler draws; near-silence | the slot |
| 7.60–9.00 | kept | a yellow block lands: "Clear. 30 min · kept for you"; the frame holds dead still | the yellow |
| 9.00–10.40 | out | the camera whips back to the year; the block stretches across the day as it goes | the yellow day |
| 10.40–11.67 | the name | kept days ripple out from it and spell CLEARING; the rest of the year dims 60 % | the word |
| 11.90–15.00 | Room, found in a full year. | "63.5 hours kept" types; the line rises; the first day pulses | end |

## Geometry

- **The year.** 52 × 7 cells, 24 px on a 30 px pitch; busy level per day from a hash, four alphas over the ground.
- **A day.** 1440 px page, scale 24/1440; 08:00–20:00 mapped to y 120–1320, so a half hour is 50 page px. Meetings from
  a hash; the target day is fully booked except 15:00–15:30.
- **Anchor A.** The day page's point (310, 15:15): the middle of the ruler-plus-block span, so both fit at 300×.
- **Level of detail**, by the cell's size on screen `sz = 24 · zoom`:

  | what | fades in over sz |
  |---|---|
  | a day's hours and meetings | 70 – 260 px |
  | meeting titles and times | 380 – 700 px |
  | the minute ruler; neighbours' text steps back to 25 % | 2,600 – 5,000 px |

## Camera

`RIG = OM.rig(want)` with `want(t)` returning where A should be on screen:

```js
const aim = (P, sP, z, w) => ({ x: sP[0] + (A[0] - P[0]) * z, y: sP[1] + (A[1] - P[1]) * z, zoom: z, w });   // put world P at screen sP
// camera from the rig's output r (screen shake added to r.x, r.y first):
CAM = { x: A[0] + (960 - r.x) / r.zoom, y: A[1] + (540 - r.y) / r.zoom, zoom: r.zoom, rot }
```

A dive eases log zoom on `cubicInOut` while the target's screen position moves linearly to the centre.

| until | frames | zoom | ω |
|---|---|---|---|
| 1.80 | the whole year | 1 → 1.03 | 6 |
| 3.60 | dive into the day | 1.03 → 40 | 9 |
| 4.80 | ride the scan down to the gap | 40 → 46 | 5 |
| 5.60 | the held breath | 46 → 50 | 5 |
| 7.00 | dive into the half hour | 50 → 300 | 9 |
| 8.95 | inside, dead still | 300 | 6 |
| 15.00 | whip out to the year, then hold | 1 | 5 |

- **Shake in screen space.** Hits `[t, px, decay]`: 7.60 [14, 8] the landing, 10.40 [4, 10] the ripple, 14.30 [3, 10] the
  pulse. `OM.rig`'s own hits divide x and y by zoom but add rotation unscaled, so they vanish at depth; here
  `OM.shake` is sampled per hit and added to the rig's screen output instead.
- **The whip** is a step in `want` at 8.95: the log-zoom spring covers 300× → 1× in about 0.6 s, peaking at −8.8 log
  units a second at 9.17 s.
- `__meta.inFrame = { day: [2.6, 5.6], slot: [6.4, 9.0], word: [10.6, 15, 'whole'] }`.

## Numbers (the accepted draft)

- **render.py**: 1080p30, 180° shutter sized by `__motion`, 8 workers.
  - 450 frames: 56 held, 42 kept a cut hard.
  - 7,422 captures in 331 s — three times case 4's, because the dives and the whip move every pixel.
- **verify_promo.py `--comp`**: PASS.

  | leg | result |
  |---|---|
  | cadence | CV 0.36 (first render; the beats did not change) |
  | rest | still 0.294, longest quiet 4.08 s |
  | burst | 2.33–3.5, 6.17–7.58, 7.58–9.0, 9.08–10.17 — the two dives and the whip |
  | not-flat | 0.59 |
  | audio | −3.5 dBFS, 0 clipped, quiet 0.244 |
  | continuity | 1.00 over 3 boundaries |
  | curves | peak 51,670 px/frame at 8.93 s — the year's box through the whip; shutter at its 48-capture cap |
  | framing | day (91 samples), slot (79), word whole (133) — all in frame |

## Sound

- **Sources.** `sfx-src` links to the one-dot film's sources: Kenney CC0, Mixkit, University of Iowa MIS (marimba,
  vibraphone, crotales) and Voxengo IRs. Nothing new was downloaded.
- **`score.py`.** It copies case 4's source, shaping, synthesis, bus and master code and adds a new score. Every time
  and pan comes from `events.json`; the camera's air from `zoom.json`.
- **`zoom_air(t0, t1)`.** Noise in three bands (150–600 Hz, 600–2,400 Hz, 2.4–9 kHz), crossfaded by depth
  `log(zoom) / log(300)` so closer is brighter, scaled by `|d log zoom / dt| ^ 1.3`.
- **Layers, in order.**
  - **The fill.** A tick per other column, rising in pitch and panned across the year, over a swell of air.
  - **2027.** Marimba C5; the header types one key in three.
  - **The dive.** The camera's air, a Mixkit whoosh on its fastest frame, a Shepard rise.
  - **The scan.** A thin FM tone that sinks as the line slows; a tick and a falling note (C5, A4, G4) each time it passes
    a meeting.
  - **Found.** Crotale A6 and a select. Then silence.
  - **Into the half hour.** Deeper air, a whoosh 4 dB under the landing, a rise; six ruler ticks in near-silence.
  - **Kept.** A soft heavy hit, the sub, a vibraphone Fmaj7 struck and held, crotale F6, a pad until the whip.
  - **Out.** The widest air, a whoosh on the fastest frame, a soft arrival at 9.62.
  - **The name.** Every fourth kept day plays the next note of an F pentatonic climbing F4 → C6, panned where it
    lights; when the word is whole the landing's Fmaj7 returns with the sub.
  - **The end.** Keys for "63.5 hours kept", crotale C6 under the tagline, one marimba note on the pulse.
- **Master.** −16.0 LUFS integrated, −3.5 dBTP; the limiter works hardest at 7.60 s (0.9 dB); quiet 0.240.

  K-weighted 400 ms loudness per beat:

  | t | 0.6 | 1.0 | 2.9 | 4.2 | 4.8 | 5.3 | 6.46 | 7.2 | 7.6 | 9.17 | 11.0 | 11.7 | 13.0 | 14.3 |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
  | LUFS | −31 | −23 | −17 | −22 | −24 | −39 | −16 | −43 | −14 | −15 | −16 | −12 | −16 | −20 |

  Energy by band:

  | band | < 100 Hz | 100–300 Hz | 300 Hz–2 kHz | 2–8 kHz | > 8 kHz |
  |---|---|---|---|---|---|
  | share | 6.1 % | 19.2 % | 68.6 % | 4.7 % | 1.4 % |

## What bit

- **Scale mismatch at the bottom.** At 230× the half hour was 192 px tall while the next meeting's title was 115 px, and
  the eye went to the neighbour. Fix: 300×, a narrower block (240 page px), neighbours' text down to 25 % at depth.
- **The word didn't read.** Yellow against days at 34–64 % white has too little luminance contrast. Fix: as the ripple
  passes, every other day dims 60 %.
- **The ruler fell off frame.** At 300× a page pixel is 5 screen px, so a ruler 200 page px left of A sat off screen.
  Fix: the ruler moved to the block's left edge and A to the middle of the pair.
- **The rest leg failed the first render: still 0.178.** Every hold had a slow push (the inside ×1.05, the end card
  1 → 1.05), and at 320 px a push over a grid of cells is never dead still. The two rests were made truly still: 0.294.
- **The second dive was as loud as the landing** (−14 LUFS both). The dive's air came down 4 dB and its whoosh 4 dB, so
  the landing is the loudest moment until the name.
- **`fm_tone` takes a function of t** for its frequency, not a number.

