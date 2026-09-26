# motion-web-15s — the worked example

> This folder ships the film only. Its source (the composition, the score, the sound sources) is not part of the
> public release; files named below describe how it was made.
>
> The film: `motion-web.mp4`


The film this skill was extracted from: 15 s, 3840×2160, 60 fps, H.264 + AAC. Accepted on the third cut.
Project (composition, footage, score, film): this folder.

## Reference
Daniel Ch's Shipper launch clip (https://x.com/chddaniel/status/2094883770164015174). Measured with
`analyze_ref.py`: 34 % dead-still frames, 7 hard cuts in two bursts, small elements on a white ground,
a narrative (prompt → work → result), a hand visible whenever the UI reacts.

## Beat sheet (what shipped)

| t | beat | moves | still |
|---|---|---|---|
| 0.15–1.55 | "Web motion is usually **decoration.**" three words spring in .35 s apart | words | everything else |
| 1.65–3.0 | wordmark letters drop in with landing squash; "makes it **move**" wobbles | type | ground |
| 3.0–4.75 | mark folds to top-left; prompt card; text types at 38 cps; hand enters, clicks send | caret, hand | card |
| 4.85–7.0 | build panel, 7 lines tick .24 s apart, last is `VERDICT: PASS` | checkboxes | panel |
| 7.05 / 7.95 / 8.85 | three real pages fly through tilted + blurred, each held .9 s (footage, hand from paths.json) | footage | — |
| 9.55–12.15 | four micro cards overlap: magnetic button (click 10.05), spring follow, jelly ring, Verlet string. The hand causes each | sims + hand | ground |
| 12.1–13.25 | browser window hold: char-curtain footage, slow push-in, hard out | footage | frame |
| 13.25–14.3 | staccato hard cuts: MOTION / IS / THE / MATERIAL at .22–.25 s | cuts | — |
| 14.3–15 | black, serif wordmark | — | all |

Shot lengths: 0.35 … 1.15 … 0.9 … 2.6 … 0.22 → CV 0.78. Stillness 31 %. One burst (13.25–14.3).

## Sound
Palette air / glass / wood / sub / bubble / wobble in one room (T60 1.1 s). 3 glass touches, a breath
for the wordmark, one key in three while typing, click down/up, a scale of glass ticks + a PASS chord,
travelling air + felt landing per page, one bubble per card, one wobble for the jelly, four subs for the
staccato, the deep one under black. Peak −8 dBFS. Score: `templates/sfx_score.example.py`.

## What was rejected on the way (see references/rhythm.md)
- v1: nine cards, 0.74 s each, one after another → 「PPT 式一个一个展示」.
- v2: full-frame footage shots, 1.55 s each → 「没有节奏变化 依然是 PPT」.
- SFX v1: sine pops per event → 低劣. Confetti specks at the wordmark → 低劣, removed.

