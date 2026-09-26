# one-dot-15s — the concept film

> This folder ships the film only. Its source (the composition, the score, the sound sources) is not part of the
> public release; files named below describe how it was made.
>
> The film: `one-dot.mp4`


The skill's first launch film (made when it was still called ohmymotion — the film shows that name): 15 s, 1920×1080, 30 fps draft, one canvas, zero assets — no footage, no images. Made in
Claude Code with this skill over 2026-09-13/14; the camera cut was accepted. Project: this folder.
— `comp.html` and `one-dot-cam.mp4` are the accepted cut, `comp-v1.html` and `one-dot-v1.mp4` the still-camera
version, `one-dot-4k60.mp4` the 4K60 final, `score.py` → `mix.wav` the sound, `sfx-src/` its recorded sources.

In this folder: `comp.html` runs in place on the skill's `lib/motion.js` and renders the accepted frames exactly
(camera samples, `__motion`, `__track` and pixel hashes at six times compared). `one-dot-cam.mp4` is the accepted
render with sound; `one-dot-cam.render.json` is its render record, so verify_promo.py reads the shutter from it.

Why it is a case — three firsts:

- **Concept.** The zero-asset demo before it reused motion-web's skeleton and got 「和那个 motion web 的动效视频很像……
  没有创造力吗」. This one came out of §2's three central ideas: one dot plays the whole film, so every boundary
  carries by construction (continuity 1.00, no edit cuts).
- **Camera.** The still-camera cut got 「很牛逼」 and then 「现在就缺灵动的跟踪运镜了」; the operator camera was accepted
  with 「细节都不用挑了 运镜 镜头和物理都没问题」. `OM.rig` and `OM.lattice` are that camera.
- **Sound.** Recorded CC0 / free sources layered with synthesis and mastered to a loudness target. The palette-only
  sound before it measured −21 LUFS with 58 % of its energy under 100 Hz.

## Beat sheet

| t | beat | the dot | carries into the next beat |
|---|---|---|---|
| 0.50 | a dot appears on black | pops (spring) | the dot |
| 1.00–1.50 | it finds its place, types "/" | glides left, stretches into a caret | the caret |
| 1.75–2.75 | "/" opens the skill list | contracts, splits into four dots + labels | the four dots |
| 2.50–3.35 | /ohmymotion is chosen | one pulses, three fall, it hops back | the label flies into the line; the dot is the caret again |
| 3.50–5.00 | "make a 15s film for Pocket Weather" types; a still beat | caret | the caret |
| 5.00–6.00 | send: the dot swallows the prompt | caret → dot, letters stream in, glides home | the dot, bigger |
| 6.00–7.25 | the skill loads | hollows into a ring, the ring fills | the ring |
| 7.25–8.00 | the math | the ring unrolls into `OM.spring`'s curve | the curve |
| 8.00–10.00 | it becomes a ball | a bead eats the curve, drops, bounces | the ball |
| 10.00–11.25 | the result | the second bounce opens a film; it is the sun | the sun |
| 11.25–12.00 | back to the dot | the film folds into the sun → dot; letters rise | the dot |
| 12.00–15.00 | ohmymotion | lands as the dot on the i; one wink | end |

Contacts sit on a 120 BPM grid (0.5 pop, 2.0 split, 6.0 home, 7.0 ready, 10.0 film, 12.0 land); the score cuts to it.

## Versions

| | what it was | verdict |
|---|---|---|
| v1 | still camera. 8 captures per moving frame: 590 s and 2,886 captures in one browser, and the film opening (633 px/frame) and closing (428) stepped, so a one-off refine pass (since folded into render.py's adaptive shutter) re-captured 35 frames at up to 48 (738 captures, 153 s) | 「很牛逼，就是时间有点太长了」; 「现在就缺灵动的跟踪运镜了」 |
| camera, render 1 | an operator over a far lattice; shutter sized by `__motion`, 8 workers: 106 s, 2,507 captures | lost the dot at 1.10 s — the glide's expoOut outran the spring. Every verify leg passed it; not shown |
| camera, render 2 | the camera leads the glide to the caret from 0.85 s; 103 s, 2,480 captures | accepted |

## Camera

`OM.rig(want, { dur: 15, hits: HITS })`: position springs at ζ 0.8, zoom in log space at ζ 0.95 and 0.8 ω, integrated
at 240 Hz once in `__ready`. The output is quantised (1/16 px, 0.05 % zoom), so a settled camera repeats its frame and
that frame skips the shutter. Behind the story sits `OM.lattice` at depth 1.2: a dot every 48 px, 1.4 px on screen, `C.dim`
at 0.9, under a screen-space vignette. Without it the dark ground gave the camera nothing to move against.

| until | frames | zoom | ω |
|---|---|---|---|
| 0.85 | the pop, centred | 2.4 | 6 |
| 1.85 | the line, 173 px ahead of where the caret lands — led from before the glide, which outruns a chase | 1.7 | 7 |
| 2.80 | the skill list | 1.55 | 6 |
| 3.50 | the line | 1.55 | 7 |
| 5.00 | rides with the caret: 42 % of its travel, 0.2 s ahead | 1.5 | 5 |
| 5.60 | pushes in on the swallow | 1.5 → 1.95 | 7 |
| 6.00 | whips home with the dot, 0.1 s ahead | 1.3 | 11 |
| 7.25 | leans in while the ring loads | 1.3 → 1.9 | 8 |
| 8.00 | pulls back for the curve | 1.35 | 8 |
| 8.80 | tracks the bead, 0.1 s ahead | 2.0 | 9 |
| 9.05 | holds on the hang | 2.2 | 8 |
| 10.00 | follows the drop, 0.1 s ahead | 1.6 | 8 |
| 11.25 | blown back by the film | 1 → 1.06 | 12 |
| 11.60 | dives into the sun | 1.7 | 10 |
| 12.00 | out to the name | 1.05 | 9 |
| 15.00 | a slow push on the name, 12.2–14.0 | 1.05 → 1.12 | 9 |

Hits `[t, px, decay]`: 6.00 [7, 9] home, 7.00 [5, 10] ready, 9.50 [9, 9] and 10.00 [16, 7] the bounces, 12.00 [10, 8]
the landing. `__meta.inFrame = { dot: [0.5, 15], mark: [12.2, 15, 'whole'] }`.

## Numbers (the accepted cut)

- render.py: 1080p30, 180° shutter sized by `__motion` (6 px gap, 4–48), 8 workers. 450 frames, 39 holds, 40 frames
  kept a cut hard (in v1 all such frames were letters appearing), 2,480 captures, 103 s. 293 of the 411 moving frames
  took 4 captures and three took 48; a fixed 8 would have taken 3,366 and stepped.
- verify_promo.py `--comp` on this mp4: PASS.

  | leg | result |
  |---|---|
  | cadence | CV 0.44 |
  | rest | still 0.389, longest quiet 2.75 s |
  | burst | 10.0–11.42 and 11.5–12.0 |
  | not-flat | 0.99 |
  | audio | peak −3.5 dBFS, 0 clipped, quiet 0.178 |
  | continuity | 1.00 over 6 boundaries |
  | curves | peak 935 px/frame at 10.00 s (on screen, camera included); 82 % of travel on soft curves; median t80 .80 |
  | framing | the dot in frame at all 431 samples from 0.5 s; the name whole at all 85 from 12.2 s |
- Frame by frame over the accepted camera, three counts, all zero:
  - the dot off frame;
  - its centre within 60 px of the edge;
  - the name cut.
- rest is nearly free for a minimal film. The energy map at 320 px can't see a small dot move on black, so v1 read
  still 0.844 and blank before 8 s. The camera and the lattice brought it to 0.389. Here it isn't rhythm evidence.

## What the film added to the skill

- **`lib/motion.js` 1.1.0.** Added `rig`, `lattice`, and `project` / `unproject` / `projectBox` / `screenTravel`. This is
  the comp's own camera, moved into the library after acceptance; the frames did not change. Gallery demo: `rig`.
- **render.py.**
  - `--workers`: one Chromium per process. A capture is a ~156 ms screenshot; the canvas draws in under 1 ms.
  - Captures per frame come from `window.__motion`.
  - v1's silent render took 590 s in one browser; the camera cut took 103 s.
- **probe.py / verify_promo.py.** The framing leg, from `__meta.inFrame`.

## Sound

`score.py` → `mix.wav`, 48 kHz stereo, built in 2.8 s. Recorded sources carry the detail synthesis can't; synthesis
carries what has to follow the picture exactly.

- **Sources.** In the project's `sfx-src/`, downloaded with the user's permission; not in the skill.

  | source | license | used for |
  |---|---|---|
  | Kenney | CC0 | clicks, ticks, soft impacts |
  | Mixkit | Mixkit Sound Effects Free License | whooshes |
  | University of Iowa MIS | free for any project | marimba, vibraphone, crotales in F major pentatonic |
  | Voxengo impulse responses | — | Nice Drum Room for the room, French 18th Century Salon for the hall |
- **Synthesis.**
  - a sub with harmonics under each landing, so it is heard on a phone speaker;
  - a Shepard riser into the ring closing;
  - an FM tone whose pitch follows `OM.spring`'s curve;
  - pads.
- **Mix.**
  - The dot's own sounds play alone until the music enters on the 6.00 downbeat.
  - The music is ducked 5 dB under the effects.
  - The whole mix is gated silent on the hang (8.83–9.17).
  - The vibraphone is choked when the film folds.
- **Master.**
  - BS.1770 −16.0 LUFS integrated, −3.5 dBTP.
  - A +3 dB shelf at 4 kHz, then an oversampled true-peak limiter: at most 3.3 dB at 10.00 s, over 1 dB for 0.11 s.
  - Mono fold-down −0.7 dB.

  | band | < 100 Hz | 100–300 Hz | 300 Hz–2 kHz | 2–8 kHz | above 8 kHz |
  |---|---|---|---|---|---|
  | share | 15.8 % | 23.7 % | 57.5 % | 2.6 % | 0.3 % |

  | beat (s) | 0.5 | 3.9 | 6.0 | 7.0 | 8.4 | 10.0 | 12.0 | 13.6 | 14.2 |
  |---|---|---|---|---|---|---|---|---|---|
  | K-weighted 400 ms loudness | −15 | −24 | −15 | −13 | −20 | −11 | −13 | −51 | −18 |
- **What bit.**
  - A −14 LUFS / −1 dBTP master failed the audio leg: peak −1.0 after AAC, quiet 0.089.
  - Mixkit whoosh 1465 peaks 1.57 s into its file, so aligning its peak started it 1.5 s early, over the rest after
    typing. `from_peak()` now cuts a source's run-up.
  - By RMS the opening pop sat within 1 dB of the climax. The arc is judged by K-weighted loudness per beat instead.

