# Reading a reference in numbers

You are not copying the reference. You are measuring the *rhythm* it has so yours is not uniform.

## Run

```bash
python3 scripts/analyze_ref.py ref.mp4 --out ana/
```

Produces `ana/energy.txt` (the map below), `ana/summary.json` (the flow fingerprint under `"flow"`),
`ana/sheet_NN.png` (4 fps contact sheets, 24 frames each), and 9 full frames spread across the clip.
The fingerprint needs `opencv-python`; `--no-flow` skips it.

## The energy map

One character per 1/12 s, rows of 4 s; ` .:-=+*#%@` from still to hard cut. The Shipper reference
(Daniel Ch, 26.6 s):

```
  0.0s |                          .    .       .        |
  4.0s |            .      ..........:::...        .....|
  8.0s |...::::::::::::::::::::::::....        .::=*++=+|
 12.0s |*@%                        ........:-::..      .|
 16.0s |.                                 @...:.:.::-:-:|
 20.0s |-:=:=:-:-@                               @      |
still (<0.5): 0.34   low (<2): 0.57   cuts: 11.6 12.0 12.1 12.2 18.8 20.8 23.4
```

What to read off it:

- **Stillness ratio.** 0.34 dead-still, 0.57 barely moving. The film breathes. The first motion-web
  cut measured 0.02 still — it never stopped moving, and that is exactly what felt like slides.
- **Where the bursts are.** Two: a 0.6 s flurry at 11.6–12.2 (UI cards flying with blur) and the word
  hits at 18.8–20.8. Everything else is small motion inside otherwise still frames.
- **The long quiet.** 15–18.8 s is one slow zoom on a monitor. 3.8 s of almost nothing, right before
  the hits. That contrast is the whole trick.
- **Cut count.** 7 in 26 s. A cut every second is not this genre.

## The contact sheets

Look for, and write down:

- **Element scale.** How much of the frame does the biggest thing take? (Shipper: cards ≈ 25 % width;
  only the monitor shot fills the frame.)
- **What actually moves inside a beat.** Typing, checkmarks ticking, a toggle, a cursor click — the
  product's own micro-interactions, not camera moves over static screenshots.
- **The narrative.** Shipper: problem words → logo → prompt typed → queue ticks → built site flies in →
  feature cards each with one click → product on a monitor → tagline → logo. One story.
- **Entrances/exits.** Spring pop-ins (overshoot), fly-throughs with blur and a few degrees of 3D tilt,
  hard cuts for words. No cross-fades.
- **Type.** Small, medium weight, one accent colour; a serif wordmark; uppercase bold only for the
  staccato beat.

## The beat sheet

Write it before composing. Columns: `t · beat · picture · what is still · sound`. Force the shot
lengths to vary by ≥ 4× and mark at least one rest. The one for motion-web is in
`cases/motion-web-15s/README.md`.

## Reading a style — take the rule, not the frames

A style reference is not a beat sheet. The part-kit study (Pinckus / Flatwhite Motion's Buildathon piece, 2026-09) was
stopped at draft 1: a new topic on the reference's beats was 「完全抄袭复刻没意义」. What transfers:

1. **The one rule every object obeys.** There: every word sits on a machined part — pills with two rivets, plates with
   four screws, hex nuts, brackets with holes, pipes in pairs, a cursor with a hole in its tail. Palette, grid and type
   follow from it. Copied parts without the rule read as clip-art; the rule applied to your own subject reads as the style.
2. **The tool behind the look.** Made in Cavalry, where path-offset bands, duplicator echoes and per-glyph typing are
   cheap — so the film is full of them. Knowing that separates the signature from what was merely easy there. In `f(t)`
   each is a few lines.
3. **Numbers, not impressions.** Palette hex from full frames, grid pitch from one pixel row, type size from cap height
   at 1080p, rivet and screw radii as a share of the part. They go at the top of the comp.
4. **Its objects, our carries.** The reference hard-cuts between beats. The study carried every boundary with the
   style's own parts — the track's edges stretch into rails, the pill becomes the reel's window and then a plate, the
   rails thicken into pipes, the camera goes down a bolt hole. A reference's cuts are not part of its style.
5. **Its language, our meaning.** Make the rule say something about the new subject, and let the beats come from
   that through §2's three concepts — not from the reference's order of scenes.

