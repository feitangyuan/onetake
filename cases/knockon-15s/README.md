# knockon-15s — the chain-reaction film

> This folder ships the film only. Its source (the composition, the score, the sound sources) is not part of the
> public release; files named below describe how it was made.
>
> The film: `knockon.mp4`


The fourth film and the first light one: 15 s, 1920×1080, 30 fps draft, one canvas, zero assets, a fictional product
(knockon). Made in Claude Code with this skill on 2026-09-14. The first draft was accepted with
「牛逼可以啊…把 html 玩得出神入化了」.

Project: this folder.
- `comp.html` is the film; `knockon.mp4` is the film with sound.
- `dump_events.py` writes `events.json` and `roll.json`; `score.py` turns them into `mix.wav`.
- `sfx-src` is a link to the one-dot film's sources.

In this folder:
- `comp.html` runs in place on the skill's `lib/motion.js`.
- `knockon.mp4` is the accepted draft, with sound.
- `knockon.render.json` is its render record.

## Why it is a case

- **The concept step, on demand.** The user wanted a light film and had no idea what it should be. Three pitches differed
  in the central idea: a chain reaction, a one-take dive through scale, and a comic page whose panel widths are the rhythm.
  The user picked the first. There was no reference film and no reference numbers.
- **Causal carry.** Case 2 carried by containers and case 3 by one element's identity. Here every boundary is a collision:
  - the key ejects the marble;
  - the marble flips the toggle;
  - the toggle tips the first card;
  - the last card presses Send;
  - Send throws the notification.

  Nothing is replaced, because each beat is caused by the one before.
- **A light tabletop seen from above.** Height is shown by the shadow: its offset and blur grow with z, and a flying card
  grows a little. The machine is laid along a pencil ↵, and the closing pull-out reveals it as the product's glyph.
- **Sound read from the picture.** The comp exports two things:
  - `__events()`: every contact's time, kind and on-screen pan;
  - `__marbleSpeed(t)`: the marble's speed.

  `score.py` places every sound from those, so a retimed beat takes its sound with it.

## Beat sheet

| t | beat | moves | carries into the next beat |
|---|---|---|---|
| 0.00–0.70 | a key on a table | the cursor arrives | the cursor |
| 0.70–0.95 | press | the key goes down, a marble pops out | the marble |
| 0.95–2.29 | down the slider, round the corner | the marble accelerates; the slider's fill is the marble | the marble |
| 2.29–3.30 | the bump | climbs, stops on top, teeters (a rest) | the marble |
| 3.30–3.86 | over | rolls off, bounces into the toggle: ON | the toggle's knob |
| 3.84–5.67 | ten tasks fall | cards tip in a quickening run, each landing face up with its task | the last card |
| 5.67–8.75 | Send | pressed; a notification is thrown up and hangs (a rest) | the notification |
| 8.75–9.90 | it lands | checks; the bell rings three times | the ink |
| 9.30–10.30 | the path inks | the pencil ↵ turns to ink; the camera rises | the ↵ |
| 10.90–15.00 | knockon | the name rises inside the ↵; one more tap on the key | end |

## The machine

- **The run.** Card i falls through an angle of π/2·u^2.2 over 0.40·0.9^i s, so it starts slowly like a real domino. It
  starts card i+1 once it has leant asin(112/170), which is far enough to reach it. The ten cards take 3.84–5.67 s,
  speeding up.
- **The marble.**
  - On the slider it falls under gravity: distance ∝ t².
  - Round the corner it keeps a constant ~1,100 px/s.
  - It decelerates evenly to rest on top of the bump.
  - It teeters there (`OM.ring`), rolls off the far side and bounces once into the knob.
- **The rest.**
  - The toggle's knob moves on `spring(ζ 0.7, ω 42)`.
  - The notification rises 440 px (cubicOut), hangs with a 1.7 s bob and a 1.25 s flutter, falls as u² and lands with
    `OM.impact`.

## Camera

| until | frames | zoom | ω |
|---|---|---|---|
| 0.80 | the key and the cursor | 1.75 | 6 |
| 2.15 | the marble, 0.14 s ahead, looking down the slider | 1.4 | 9 |
| 2.56 | the marble, 0.1 s ahead, round the corner and up | 1.5 | 9 |
| 3.30 | the bump, pushing in while it teeters | 1.6 → 2.1 | 5 |
| 3.84 | between the bump and the toggle — where the marble lands, before it rolls | 1.6 | 10 |
| 5.77 | the run's front, 0.15 s ahead | 1.45 → 1.2 | 8 |
| 8.20 | the notification and its shadow | 1.25 | 5 |
| 9.60 | the landing and the bell | 1.6 | 9 |
| 15.00 | the whole ↵ | 0.76 → 0.79 | 3.2 |

Hits `[t, px, decay]`:

| t | hit | px | decay |
|---|---|---|---|
| 0.70 | the press | 4 | 12 |
| 3.75 | the knock | 6 | 10 |
| 5.67 | Send | 5 | 10 |
| 8.75 | the landing | 12 | 8 |
| 9.15 | the first ring | 4 | 12 |

`__meta.inFrame = { marble: [0.95, 3.9], note: [5.95, 10.0], mark: [11.7, 15, 'whole'] }`.

## Numbers (the accepted draft)

- **render.py**: 1080p30, 180° shutter sized by `__motion`, 8 workers.
  - 450 frames: 38 held, 31 kept a cut hard.
  - 1,935 captures. Of the 412 moving frames, 341 took 4; none took more than 19.
  - 141 s; 2:25 including the encode.
- **verify_promo.py `--comp`**: PASS.

  | leg | result |
  |---|---|
  | cadence | CV 0.67 |
  | rest | still 0.272, longest quiet 3.42 s |
  | burst | WARN — none, and there is no reference |
  | not-flat | 0.55 |
  | audio | −3.5 dBFS, 0 clipped, quiet 0.239 |
  | continuity | 1.00 **over 0 boundaries** |
  | curves | peak 360 px/frame (the cursor arriving at 0.10 s); 46 % of travel on soft curves; median t80 .54 |
  | framing | marble (89 samples), note (122), mark (100) — all in frame |

- **The continuity pass is empty.** The probe found no boundary to judge in one continuous top-down world with a moving
  camera, so carry here was judged by eye.

## Sound

- **Sources.** `sfx-src` links to the one-dot film's sources: Kenney CC0 (impact, interface and UI packs), Mixkit,
  University of Iowa MIS (marimba, vibraphone, crotales) and Voxengo IRs. Nothing new was downloaded.
- **`score.py`.** It copies the one-dot film's source, shaping, synthesis, bus and master code and adds a new score. Every
  time and pan comes from `events.json`.
- **Layers, in order.**
  - **The key.** A thock (Kenney light wood, −5 st), a click and a short sub.
  - **The roll.** Noise band-passed to 140–1400 Hz plus a band above 2.5 kHz, both scaled by the marble's speed, with a
    seam once a turn. The slider ticks every 10 %, climbing in pitch.
  - **The teeter.** Silence.
  - **The toggle.** The knock (plank, +4 st); the switch lands ON on C5.
  - **Each card.** A wood clack rising in pitch, a paper slap, and the next note of an F pentatonic climbing F4 → D6.
  - **Send and the throw.** A click, a soft impact and a sub; then a whoosh and air, a crotale at the top, and a faint pad
    under the hang.
  - **The landing.** A soft heavy impact, the sub and marimba F3; a select tick on A4; the bell is crotales F6, A6, C6.
  - **The rise into the name.** A pen scratch, air, a Shepard riser and a pad.
  - **The name.** A soft heavy impact, the sub, a strummed vibraphone Fmaj7, marimba F4/F3 and a pad.
  - **The last tap.** The key again, plus C5.
- **Master.** −16.0 LUFS integrated, −3.5 dBTP; the limiter works hardest at 10.93 s (3.5 dB); quiet 0.235.

  K-weighted 400 ms loudness per beat:

  | t | 0.7 | 1.8 | 2.9 | 3.86 | 4.8 | 5.67 | 7.0 | 8.75 | 9.15 | 10.9 | 12.5 | 13.7 |
  |---|---|---|---|---|---|---|---|---|---|---|---|---|
  | LUFS | −21 | −19 | −53 | −20 | −17 | −17 | −32 | −15 | −16 | −11 | −14 | −21 |

  Energy by band:

  | band | < 100 Hz | 100–300 Hz | 300 Hz–2 kHz | 2–8 kHz | > 8 kHz |
  |---|---|---|---|---|---|
  | share | 11.5 % | 32.0 % | 51.7 % | 3.5 % | 1.2 % |

## What bit

- **Canvas shadows and filters ignore the transform.** `shadowBlur`, `shadowOffset*` and `filter: blur()` are measured in
  canvas pixels. Under a camera at DPR 2 they have to be multiplied by DPR × zoom by hand (`lift`, `softPoly`), or the
  shadows shrink as the camera pulls out.
- **Mud from a low arpeggio, not from the rumble.**
  - The first mix put 41.6 % of its energy in 100–300 Hz, and thinning the roll noise changed nothing.
  - Measuring energy per 0.5 s window found the source: 95 % of the window at 4.5 s was 100–300 Hz. The run's marimba
    started at F3, and its 1.8 s tails piled up.
  - Fix: an octave up, each note cut to 0.7 s. That window fell to 6 % and the whole mix to 32 %.
- **The run hides itself.** Seen from above, a card lying on the next one covers it, so the last card stays hidden under
  the ninth until its top edge clears it. That is physically right, but the last card's fall doesn't read.
- **Still open when accepted.**
  - At 5.6 s the camera chasing the end of the run blurs the whole frame.
  - Standing cards read more as pale strips with long shadows than as cards on edge.

