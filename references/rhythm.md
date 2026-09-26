# Rhythm and carry — what the first two films taught

Two films, six cuts, one verdict for two different reasons: 「PPT」. motion-web failed on rhythm. Pocket
Weather had the rhythm and failed on carry.

# Rhythm — the three cuts of motion-web

The same nine pages, the same 15 seconds, three completely different results. Cut three shipped.

## Cut 1 — the card field (rejected: 「PPT 式一个一个展示」)

Nine pages as cards on a 2.5-D field, camera dollying past each for 0.74 s, depth blur, labels.
Measured: 0.02 still frames, camera never stopped, every card the same dwell.

Why it failed: **uniform cadence** and **thumbnails**. A page's motion does not survive being 700 px
wide and blurred for 0.7 s. The camera move made it *feel* like a gallery walk — which is a slideshow
with a dolly.

## Cut 2 — full-frame footage, hard cuts (rejected: 「也没有节奏变化 依然是 ppt」)

Seven pages full-frame, 1.55 s each, hand drawn back in, label pill, push-in per shot, spring settle
on cuts. Better legibility, still rejected.

Why it failed: **still a metronome**. Seven equal shots with the same shape (cut, push-in, label) is
seven slides even when each slide moves. No rests, no bursts, no story — a catalogue.

## Cut 3 — the reference's structure (accepted)

| t | beat | length | motion |
|---|---|---|---|
| 0–1.6 | three words | 0.4 s per word | pops only |
| 1.6–3.0 | wordmark letters drop and squash, tag wobbles | 1.4 s | small |
| 3.0–4.8 | prompt card types, hand clicks send | 1.8 s | typing |
| 4.8–7.0 | build panel ticks 7 lines | 2.2 s | ticks |
| 7.0–9.6 | three pages fly through tilted, blurred in/out | 0.9 s each | **burst** |
| 9.5–12.1 | four micro cards, live sims, hand pokes each | ~0.85 s, overlapping | short |
| 12.1–13.25 | browser window, slow push-in | 1.15 s | **rest** |
| 13.25–14.3 | MOTION · IS · THE · MATERIAL | 0.25 s each | **hits** |
| 14.3–15 | black, wordmark | 0.7 s | still |

Measured: 0.54 still frames, one burst, one rest, hits at the end. Shot lengths from 0.22 s to 2.2 s.

Why it worked: it **tells what the thing does** (the checklist is the skill's real workflow; the
micro cards are its mechanisms running live; the fly-throughs are its outputs) instead of showing
outputs one after another; and the **energy curve has shape**.

## The rules that fall out

- Shot lengths: coefficient of variation ≥ 0.25 or it is a metronome. `verify_promo.py --shots` checks.
- At least 25 % of frames dead-still; at least one ≥ 1 s stretch under the low threshold.
- If the reference hits, at least one burst (≥ 3 big changes inside 1.5 s), not at a uniform interval. A concept
  without hits — one element transforming, one continuous camera move — has none, and that is not a flaw.
- Show mechanisms as **components in cards** when the page's motion is too small to read at card size.
- Show pages **full-frame** only for a hold, with the hand visible.
- Never end a shot the same way twice in a row (spring-out, blur-out, hard cut — alternate).
- Kill any flourish that is not the product's own behaviour (confetti, specks, sparkles).

# Carry — the three cuts of Pocket Weather Club

Made in Codex with this skill, after motion-web. It had learned
the rhythm lesson: v1 passed every rhythm leg. It was still rejected as PPT.

## v1 — rhythm passed, rejected: 「像 PPT」

Key visual, character showcase, full-page recording, brand end card, 4K60. Cadence, rest, burst, not-flat and
audio all passed. The code shows what those legs cannot see: every beat is its own scene, and showing one sets
`display:none` on the rest. probe.py afterwards: **two boundaries, both bare — carry score 0.00.**

## v2 — the first 6 s accepted, the rest sent back

Re-cut as a 1080p30 draft. Sunny lands on the headline and knocks its letters apart, hops to its slot, the cards
spring up around it, the hand picks it, the page grows out of the card. Then three recorded pages one after
another and a pocket lockup. The user kept the first 6 s and sent back the rest. probe.py: **carry score 0.40** —
carried at 2.97 s (Sunny) and 11.60 (the lockup); bare at 6.03 (the page growing out of the card, a seam v3 kept),
8.13 and 9.83 — page replaced by page, in the rejected half.

## v3 — carried throughout, accepted

The first 6 s kept; the rest rebuilt so every beat grows out of the one before: a push into Sunny on the page, a
circular stage opening from Sunny until it is the frame, the hand dragging an elastic rail of moods while the words
lag, the cast gathering on arcs and folding into a turning seal as the name rises from its masks. probe.py:
**carry score 0.75** — carried at 2.97 (Sunny), 8.27 and 9.17 (the hand), 11.30 (the cast); anchored at 7.27
(Sunny, unmoved while the stage opens); bare at 6.03. It failed `not-flat` (0.33), the leg v1 had passed.

## The numbers

| film | verdict | carry score | carried · anchored · bare | rhythm legs |
|---|---|---|---|---|
| motion-web cut 3 | accepted | 0.56 | 5 · 0 · 4 | all pass |
| Pocket Weather v1 | rejected | **0.00** | 0 · 0 · 2 | all pass |
| Pocket Weather v2 | first 6 s accepted | **0.40** | 2 · 0 · 3 | all pass |
| Pocket Weather v3 | accepted | 0.75 | 4 · 1 · 1 | not-flat fails (0.33) |

Continuity separates the verdicts; no rhythm leg does. So verify fails a carry score under 0.5 and warns under
0.7. motion-web passes at 0.56 with four bare boundaries — the setup words giving way to the wordmark (1.6 s), the
checklist to the first fly-through (7.1), one fly-through to the next (8.0), the micro cards to the hold (12.3) —
and would be a better film carried.

Curves separated nothing: 57–72 % of all travel was on soft curves (t80 ≥ .55) in all four films, median t80
.64–.71. All four were rendered without motion blur, and three have moves far over 80 px/frame at 30 fps
(v2 664, motion-web 385, v3 354).

## How the probe decides, and where it is blind

A boundary is a 0.4 s window in which most of the on-screen area changes identity; fades through the ground are
bridged. **Carried**: something survives and moves ≥ 2 % of the frame diagonal or scales ≥ 10 %. **Anchored**:
the only survivor is large (≥ 3 % of the frame) and unchanged. **Bare**: nothing survives. Exempt: inside a burst
of hard cuts (≥ 3 within 1.5 s), the last 1.2 s, and times listed in `__meta.cuts`. Score = (carried +
anchored / 2) / boundaries considered.

It tracks identity, so a carry built from two elements is invisible to it. At Pocket Weather 6.03 s the page is a
*new* image fading in at the card's size while the card fades out: a viewer sees the card become the page, the
probe sees a replacement — and the user accepted that seam twice. Build a carry as one element changing
(`morphRect`, one layer scaled by `zoomThrough`), or list the time in `__meta.cuts` with the reason in the beat sheet.

Two more blind spots, from the camera films:

- **One continuous world has few or no boundaries.** knockon, a top-down machine under a moving camera, scored
  continuity 1.00 over 0 boundaries; clearing did it over 3 and unbroken's split over 1. There the carry was judged by
  eye. A PASS over fewer boundaries than the beat sheet has is not evidence.
- **rest reads energy at 320 px.** It over-reads small detail on a dark ground: a dot on black (one-dot v1, still
  0.844) or bone-white brush strokes (unbroken, 0.628). It also counts any camera push as motion: clearing's first
  render failed at 0.178 because every hold had a slow push. Make the rests truly still; then the leg is honest.

## The rules that fall out

- Write the carry into the beat sheet: for each boundary, the element that survives it and what it does.
- The carries that worked: the thing pressed becomes the result, a stage opens from the subject, the hand drags the
  next option in, the cast folds into the lockup (motion-library.md → *carry*). A fade or a slide between unrelated
  scenes is not a carry.
- The hand is the cheapest carrier: keep it on screen across a boundary it caused.
- Page after page is a slideshow even when each page moves (v2 at 8.13 and 9.83, motion-web at 8.0).
- Bare cuts only in a burst of hits or into the end card.
- Run probe.py on the first playable storyboard. Its `bare` lines are the beats that will read as slides.
- Rests are dead still: no `drift`, no settling camera. A push in a hold is motion to verify.
