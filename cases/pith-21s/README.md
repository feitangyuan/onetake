# pith-21s — the window grew out of the terminal

> This folder ships the film only. Its source (the composition, the score, the sound sources) is not part of the
> public release; files named below describe how it was made.
>
> The film: `pith.mp4`


The sixth film: 21.5 s, 1920×1080, 30 fps draft, one canvas, one inlined bitmap font, zero footage. Made in Claude
Code with this skill on 2026-09-15 for **Pith**, a Tauri 2 desktop GUI that embeds the
`pi` coding agent's SDK in-process — "pi CLI 的一层皮肤，不是一个新的 agent".

Project: this folder.
- `comp.html` is the film and runs in place on the skill's `lib/motion.js`; `pith-21s.mp4` is the film with sound.
- `dump_events.py` writes `events.json` and `zoom.json`; `score.py` turns them into `mix.wav`.
- `sfx-src` is a link to the one-dot film's sources.

## Why it is a case

- **Carry by scale, pulling out.** clearing dived 1× → 300× → 1×. This one runs the technique in reverse and never
  comes back: 440× → 0.52× in one take. Nothing is replaced because everything is inside the frame that arrives
  around it — the pixel is in the caret, the caret is in the prompt, the prompt is in the stream, and the window draws
  its border around the stream that is already there.
- **The product's two themes are the film's one transition.** Pith ships a Platinum light default and an
  amber-phosphor dark theme. The film starts inside the dark one, and the title bar landing flips it to the light one
  in a single frame. The transition is not invented; it is `data-theme`.
- **The same bytes, rendered twice.** The lines that scroll as raw CLI output are the same lines the window then
  renders — same page positions, different presentation. The first thing the window does is fold nine of them away.
- **The claim is built out of the picture, not captioned over it.** pi 0.84.1 has exactly seven built-in tools —
  `read` `bash` `edit` `write` `grep` `find` `ls` — and the film's first turn runs every one of them. At 17.2 s those
  seven row squares leave the timeline on fanned arcs (`OM.gather`) and line up under the shrinking window, each
  naming itself. "This agent is seven tools" is the same seven objects that have been ticking since 3.8 s.
- **The mascot earns a close-up.** TopBar.tsx draws a pair of pixel eyes that blink and track the cursor on a 3 × 3
  pixel grid. At 1× they are four pixels nobody sees. The film pushes to 44× on them, holds dead still while they
  blink, then snaps their pupils toward the pointer — and the camera follows that gaze back out to the composer. The
  eyes are the beat that breaks the film's longest still stretch *and* the hand-off into the second turn.
- **The type is the product's type.** Fusion Pixel 12px, the app's own font, subset to the glyphs used and inlined as
  base64 (≈3.4 KB each) so the `file://` page render.py loads has it. One bitmap pixel is 1.5 page px, which is what
  makes "inside one pixel" a real place to put the camera.
- **No music until the window exists.** The first 7.8 s are a phosphor hum, coil whine and dry key clicks. The landing
  cuts the hum in 40 ms and the film's first note arrives in the silence after it.

## Beat sheet

| t | beat | moves | carries into the next beat |
|---|---|---|---|
| 0.00–1.55 | one phosphor pixel | a lit cell edge, dead still; one blink at 1.12 | the pixel |
| 1.55–3.30 | the caret | pull 440× → 9×; the prompt types in amber at 28 cps | the line |
| 3.30–6.30 | the wall | pull 9× → 3.2×; 24 lines of pi output stream up past a frame that stays low | the text |
| 6.30–7.55 | the frame arrives | pull 3.2× → 1.35×; a 1 px border draws itself clockwise from the corner | the text |
| 7.55–7.77 | the clamp | the title bar drops on a ζ .5 / ω 26 spring and lands | the window |
| 7.77 | **the flip** | amber → ink in one frame; `impact` squash, a 13 px shake, the hum cut | the window |
| 7.77–8.60 | the held breath | dead still | the window |
| 8.60–9.77 | the desk | nine detail lines fold away; the sidebar folds out on `backOut`; the 3 px hard shadow drops | the window |
| 9.77–10.34 | rest | dead still, silent | the title bar |
| 10.34–11.06 | **the eyes** | a push 1× → 44× into the title bar's left corner | the eyes |
| 11.06–12.14 | the close-up | dead still and silent; they blink at 11.58; at 11.88 the pupils snap to the pointer | the gaze |
| 12.14–12.87 | the gaze | the camera follows where they are looking, out and down to the composer, 44× → 1.85× | the pointer |
| 12.87–14.97 | the use | the hand clicks into the field, types, sends | the message |
| 14.97–16.99 | the answer | the message lifts out of the composer into the timeline; three rows tick in already collapsed | the window |
| 16.99–18.39 | out | pull 1.85× → 0.52×; the window settles into the top third | the window |
| 17.19–17.91 | **the seven** | the seven tool squares leave their rows on fanned arcs and line up | the row |
| 17.99–18.6 | they name themselves | each name rises beside its square; the label above | the row |
| 18.64–21.50 | the name | Pith drops letter by letter in lavender; the line types; a caret blinks | end |

## Geometry

- **The window.** 1010 × 639 world px at zoom 1 — 31 % of the frame. Its interior is a 1240 × 784 page drawn under
  `mul(VIEW, [S, 0, 0, S, WIN.x, WIN.y])` with `S = 1010/1240`, so type is set at 18 px and stays crisp at 440×.
- **The page.** Title bar 30, sidebar 210, timeline 1030 × 570, composer box at y 626. The terminal's layout already
  *is* the window's layout — output above, input at the bottom — which is why the chrome can arrive without moving a
  single line.
- **The caret.** `CARET.x` equals `TXT.x`, so the first character typed lands exactly where the caret was: the pixel
  the film opens inside becomes the first letter of the prompt.
- **The stream.** Bottom-anchored: each line's height is arrival × fold state, summed upward from the timeline's
  bottom edge, so a line arriving pushes the older ones up and a fold lets them settle back down. One pure function
  of t, and `layout(t)` is also what tells the gather where each square currently is.
- **The phosphor.** A grid in page units at `CELL = FS/12 = 1.5` page px: unlit cells hold a 5.5 % amber residue (so
  the deep camera has a ground to slide against), gaps are 16 % of a cell, scanlines darken every other row, and lit
  content carries a screen-constant `shadowBlur` bloom. All of it fades out over `CELL·S·zoom` = 13 → 3.5 screen px.

## Camera

`RIG = OM.rig(want, { zoomRate: 1.0 })` in screen space, `want(t)` returning where the beat's **subject** should sit.

| until | frames | zoom | ω |
|---|---|---|---|
| 1.55 | one lit pixel | 440 | 5 |
| 3.30 | out to the caret | 440 → 9 | 8 |
| 6.30 | the wall, frame settling to 0.86 H | 9 → 3.2 | 8 |
| 7.55 | the whole window | 3.2 → 1.35 | 7 |
| 8.60 | the clamp, dead still | 1.35 | 6 |
| 9.77 | the desk | 1.35 → 1 | 6 |
| 10.34 | rest | 1 | 6 |
| 11.06 | push into the title bar | 1 → 44 | 12 |
| 12.14 | the eyes, dead still | 44 | 6 |
| 12.87 | follow the gaze to the composer | 44 → 1.85 | 7 |
| 16.99 | the use and the answer | 1.85 → 1.74 | 6–7 |
| 18.39 | out to the lockup, window centred at (960, 300) | 1.74 → 0.52 | 5 |

- **Keep the eye where a terminal's eye is.** The wall beat's first cut framed the caret while the output built off
  screen above it — a second of nothing. Settling the subject to 0.86 H over the beat's first 0.9 s fixed it: the
  frame sits low and the output grows past it, which is what looking at a terminal is.
- **The anchor has to follow the subject.** clearing's rig chased one fixed world anchor, which works while
  everything framed is near it. Here the eyes are 524 world px from the caret: at 44× a fraction of a second of zoom
  lag put the frame in the *sidebar*, three lines away from the shot. `subj(t)` now travels caret → eyes → composer
  and both `aim()` and `camAt()` read it, so the residual shrinks exactly as the zoom grows.
- **A 3.8-log-unit zoom step needs time on both ends.** The first cut of the eyes beat wanted 1× → 44× in 0.54 s and
  the spring was still at 9× when the "hold" began, 16× a tenth of a second later. Fixes: `zoomRate` 0.8 → 1.0,
  ω 9 → 12 on the push, the push stretched to 0.72 s, and the hold given a full second so ~0.35 s of it is a settled,
  dead-still close-up. The pointer's click was moved behind the settle for the same reason.
- **Shake in screen space**: `[[7.77, 13, 9], [11.88, 5, 14], [14.64, 4, 12]]`.
- `__meta.inFrame = { caret: [0.2, 3], win: [8.67, 10.27, 'whole'], eye: [11.45, 12.10, 'whole'], row: [15.6, 16.9],
  tools: [18.2, 18.9, 'whole'], mark: [19.7, 21.5, 'whole'] }`.

## Sound

- **Sources.** `sfx-src` links to the one-dot film's (Kenney CC0, Mixkit, University of Iowa MIS, Voxengo IRs).
  Nothing new was downloaded. Mixkit's licence does not allow redistributing its files.
- **`score.py`** reuses clearing's source handling, shaping, synthesis, buses and master and adds a new score plus a
  `hum()` generator (60/120/180 Hz + an 8.1 kHz coil whine + 1.8–7 kHz screen hiss, killed in 40 ms).
- **`zoom_air(t0, t1)`** is clearing's, re-aimed: brightness from `log(zoom)/log(440)` so deeper is thinner and
  brighter, loudness from `|d log zoom / dt| ^ 1.3`.
- **The quiet is scored, not left over.** The first mix passed every leg but audio (quiet 0.10 against 0.15): the hum
  ran from frame 0 and a pad ran straight through the rest. Starting the hum at 0.34 s, holding 0.5 s of nothing
  after the landing, and putting *no* bed under the rest or the eye close-up took it to 0.186. Rests: 0.00–0.50,
  11.00–11.83 (the close-up), 13.83–14.08, 15.08–15.58, 20.58–21.42.
- **The eyes get two pixels of sound**: two lid ticks for the blink, and one hard high tick plus a 120 Hz sub for the
  snap. The gather gets the same `tick_002` the rows have used all film, transposed up seven times.

## What the first cut (20.0 s) did not have

It passed all eight legs and was still missing two things the user named: the eyes were four pixels in a title bar
nobody would notice, and "pi is a very small agent" was nowhere in the picture. Both fixes are beats, not captions —
a close-up that doubles as the rhythm break and the hand-off, and seven objects that were already on screen lining
up. The film grew 1.5 s. (It also corrected the tool count: the user remembered four, pi 0.84.1 registers seven.)

## Numbers (the accepted draft)

- **render.py**: 1080p30, 180° shutter sized by `__motion`, 8 workers. 645 frames: 63 held, 97 kept a cut hard.
  6,369 captures in 107 s.
- **probe.py**: continuity 1.00 over 3 boundaries, all carried. Peak 3,865 px/frame at 10.37 s (the push into the
  eyes), median t80 0.66.
- **verify_promo.py `--comp`**: PASS on all eight legs.

  | leg | result |
  |---|---|
  | cadence | CV 0.51, shot lengths 0.22–3.0 s |
  | rest | still 0.291, longest quiet 3.25 s |
  | burst | six, in the stream, at the landing and around the eyes |
  | not-flat | 0.76 |
  | audio | −3.5 dBFS, 0 clipped, quiet 0.186 |
  | continuity | 1.00 over 3 boundaries |
  | curves | peak 3,865 px/frame, shutter 180° |
  | framing | caret, win (whole), eye (whole), row, tools (whole), mark (whole) — all in frame |
