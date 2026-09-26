# Product demos without a screen recording — rebuild the UI, narrate it, cut it in any language

A **product feature demo** (产品功能演示 / 功能展示动效): the film shows the product being used — open it, pick a mode,
upload, get the result — usually with a voice and subtitles, 30–60 s. The obvious route is a screen recording; the
cheaper and more controllable one is to **rebuild the product's UI in HTML** from a few reference takes and drive it
from `seek(t)` like everything else in the composition. This page is the method; `lib/ui_kit.js`,
`scripts/vo_tools.py` and `scripts/frame_diff.py` are its tools. It carries no look — see the last section.

## Why a replica beats a recording

- **Every string is data.** A second language is a strings table, not a re-shoot; the product need not even ship that
  language's UI.
- **The camera can go anywhere.** A replica is vector and DOM: a 2.5× close-up on a dropdown is as sharp as the wide.
  A recording is capped by its pixels and its window size.
- **No account, no timing, no leaks.** Nobody waits for a slow run; there are no names, tokens or placeholder strings
  on screen by accident; nothing moves that the film didn't author.
- **It is cheaper than it sounds.** One app screen is a few hundred lines of absolutely positioned HTML, and it only
  needs the states the film shows.

What it costs: the replica must be checked against the real thing side by side, and **content must be real** (below).

## 1 · Reference takes: the smallest ask

The user records or screenshots only **reference takes** — the screens and states the film will show, at any quality.
Asking a non-technical user for a shot list fails (「看不懂让我录什么」). Ask for one concrete thing: "open X, click
Y, type /, screenshot each step". Pull frames from the takes (`ffmpeg -ss … -frames:v 1`), and note every state: the
default, the dropdown open, the menu, the chip after picking, the button lit.

**Content comes from the product's real output only.** The data on screen, the generated file names, the numbers in
the charts: all read by a script from the files the product actually produced (`gen_data.py` → `data.js`, "nothing
typed by hand"). Numbers invented because they look good are a claim the product never made.

## 2 · Build the replica

- **Lay it out in the reference's own pixel frame** (a Retina screenshot halved, e.g. 1918 × 1080), every element
  absolutely placed at its measured position; show it scaled by `s` inside a window on the plane
  (`UIK.stage({x, y, s, chrome})`).
- **Put every string in `STR[lang]` from the first line.** A `build({S})` writes the DOM once; a
  `set(el, state)` writer changes it per frame (mode, placeholder, menu open, hover row, chip shown, send lit) —
  pure, so `seek(t)` can call it at any t.
- **Namespace the CSS under one root class.** A generic class name in the replica (`.ph`) collided with the
  composition's own and painted dashed yellow boxes.
- **Build and measure while visible.** A `display:none` container measures zero; measure after fonts load.
- **Fixed lefts only fit one language.** Keep the reference's measured lefts for the source language, and lay rows
  out by measured width (`UIK.flow`) for every other one.
- **Hide what the client doesn't want seen**: account names, download buttons, workspace names.
- **Compare against the reference.** A `compare.html?s=<state>` shows the replica beside the reference frame at 1:1;
  go state by state until the only differences are deliberate.

## 3 · Show it so it reads

- **Legibility is arithmetic**: text on screen = font px × replica scale × camera zoom (`UIK.screenPx`). Anything
  the VO names should be ≥ 26 px. A 13 px dropdown label in a 0.75-scaled replica needs zoom ≈ 2.7
  (`UIK.zoomFor(13, 0.75)`). A window that must be read should be ~70–80 % of the frame width. Fitting cards, the
  window and a result into one wide shot made the UI unreadable and was sent back.
- **One close-up per operation**: each step (mode → pick → upload → send) gets its own framing, and the camera
  follows the hand between them. The wide shot is for moments where the relation *is* the point.
- **Highlights come from the DOM, drawn on the canvas.** `UIK.domLocal(el, rootClass)` walks the offset chain, not
  `getBoundingClientRect`, which already includes the camera. `stage.box()` turns that into a plane rect.
  `UIK.rectCache()` keeps the last rect so a ring can fade out after its element hides.
- **The user's standing highlight preference**: a glowing rounded rectangle sized to the content (`UIK.glowRing`,
  drawn on, then out) — never a thin frame, never a circle. For a menu row, ring the icon and name, not the whole row.
  Colour, padding, glow and timing are free per film.
- **The cause is visible.** A cursor clicks real element centres, with a press/release pair (~75 ms apart) on each click.

## 4 · Narration

```bash
KPY=~/.cache/kokoro/venv/bin/python
$KPY    scripts/vo_tools.py tts vo/lines.txt --voice <v> --lang en-gb --lines 2,4 --sample --out vo/samples   # audition voices on 2 lines
$KPY    scripts/vo_tools.py tts vo/lines.txt --voice <v> --lang en-gb --out vo/<v>
python3 scripts/vo_tools.py words vo/<v> --lang en --lines vo/lines.txt
python3 scripts/vo_tools.py plan  vo/<v> --lead 0.5 --breath 0.45 [--gap 7:2.45]
python3 scripts/vo_tools.py subs  vo/lines.txt vo/<v>
```

- **Audition before you commit.** Render the same two lines in 5–8 voices and let the client pick. Clients change
  their mind: the timeline has to survive a voice swap (below).
- **Continuous narration**: 0.45 s breaths. A longer gap only where the picture carries on alone (a scroll with the
  music). Never space lines out to fill a length. The film's length follows the VO.
- **Beats sit on words**: `T.PICK: 15.3, // "select"`. Every beat names the word it lands on, so a new VO means
  re-reading `words.json`, not re-deciding the film.
- **Measure before promising a length.** "Cutting 8–10 words will do" was wrong once. TTS pauses at punctuation don't
  shrink with speed.
- **Music under a voice**: duck it under the VO envelope (fast attack, ~350 ms release), ~11 dB under the voice RMS.
  Cut the track on its beat grid so its drop lands on the film's big moment. A narrated film is never quiet, so
  verify's audio leg fails. That is structural: don't tune for it.

## 5 · Languages: one composition, many cuts

- **One file, `?lang=xx`.** No parameter means the source language, and it must stay **pixel-identical**. Freeze
  the accepted comp, then check it with `scripts/frame_diff.py frozen/comp.html comp.html --times …`. Byte-compare the
  source language's mix and events too. Render with the query in the path: `render.py "comp.html?lang=ja"`. Copying
  the comp per language means every later motion fix is made twice.
- **Write, don't translate.** Rewrite each VO line for the new language: the natural order and length of that
  language, about the same seconds. Any line that names a UI label must use the **localised** label the replica
  shows.
- **Text through one helper** (`UIK.tr(lang)` or `J(en, xx)`). Display names for products, channels and statuses
  map at draw time, and the data keeps its keys.
- **Localise the mess too.** If "messy data" is part of the story, make it messy the way that locale is messy.
  Japanese: half-width vs full-width katakana and digits, 9月15日 vs 2026/9/16. Values stay the same.
- **Currency follows the client's rule.** Switching the symbol without converting the numbers is a legitimate brief
  (¥12 where the source said £12); converting is a different claim. Ask if unstated.
- **Fonts**: a CJK face is local and loaded only for that language: `UIK.loadFont('Noto Sans JP',
  'brand/fonts/…ttf', {need: lang === 'ja'})`, awaited in `__ready`. Put it second in the stack (`Inter, 'Noto Sans
  JP'`), so Latin keeps the house face.
- **Japanese TTS**: Kokoro's espeak path can't read kanji. Write a kana reading per line (`read.txt`, brand names as
  said: エクセル, エイチティーエムエル) and phonemise it with misaki[ja] (`--read`). Subtitles still use `lines.txt`.

### Timing another language: warp the clock, not the beats

The beats, camera keys, hand path and events are authored once, on the source VO. Another language gets
`const {U, Ui} = UIK.timeWarp(KNOTS)`: knots `[filmT, authorT]` placed on **words that mean the same thing**, not
just line starts. Word order moves: the Japanese says "Pro mode, switch", so the dropdown opens on 「プロ」 and Pro
is chosen on 「切り替え」.

- `seek(tf)` draws at `t = U(tf)`: the camera (`camAt(U(tf))`), scroll, every `T`. Subtitles use film time
  `tf`. `__meta.dur = Ui(authorDur)`. `__events()` maps each `t`
  through `Ui`, so sound lands in film time. `__motion(t0, t1)` samples `camAt(U(t))`.
- **Check `slopes`**: authoring s per film s. Keep it between ~0.5 and ~1.4. Below that a move plays in visible slow
  motion, above it the move rushes. Where one language talks longer before the payoff, let the payoff start earlier
  in the sentence rather than slowing a burst to a crawl.
- **A voice swap is a knot rewrite.** Take the new `words.json` and move each knot to the same word. Drop a knot when
  two anchors fall closer than the move between them needs; the new voice may not pause where the old one did.
- **Loudness per language.** A peak-normalised mix of a denser voice came out 5 LU louder than the source cut. Match
  each language's integrated loudness to the source mix's (ffmpeg `ebur128`) as the last step.
- **Per-language end clips.** Brand kits often ship one per market; extract the right one at the film's fps.

## 6 · Ending on the brand's own clip

Extract the official end clip to frames at the film's fps. From its first frame on, the composition draws those frames
full-screen. Before that, land the film's subject on the **exact screen spot** of the logo in frame 1 (`OM.unproject`
from that point), then cross over to a crop of that logo while the ground fades to the clip's background. The cut
into the clip is then invisible.

## 7 · Things that bit

- **A preview that cuts away and back is two cuts.** Showing the result early then returning made the base shot
  reappear, and each reappearance read as a cut. A lens or window *over* the base shot shows the future without
  leaving it.
- **Camera shake at 30 fps with a 180° shutter becomes double images.** Every letter in that frame ghosted. Narrated
  UI films want no shake.
- **`__motion` must track everything that moves**, including copies and scroll. Undercounting left fast tiles
  stepping in bands.
- **79 concurrent `img.decode()` calls reject in Chrome.** Wait on `onload` instead.
- **A `//` comment pasted mid-line swallows the rest of that line.** It ate a string (on screen as `undefined`) and
  two camera keys.
- **Whisper mishears brand names** (a made-up name comes back as a real word, or as an unrelated kanji). Use its times, the script's words.

## 8 · What is *not* in this method — decide it fresh every film

The replica, the narration pipeline and the warp are tools. They say nothing about how the film looks, so don't carry
the last demo's look into the next one:

- **the concept**, per §2 of SKILL.md: what the film is made of. "The data records are tiles that become the
  charts" was one film's idea. Others: the UI itself as the only material, a single object passed through the
  product, a before/after split, a scale dive into one control…;
- **the palette**: light or dark, one accent or tonal planes, how issues are coloured. Show 2–3 stills and pick;
- **the stage**: a window on an infinite plane, the UI full-frame, a device, several windows side by side;
- **the camera grammar**: an operator chasing the hand, locked close-ups with cuts, one continuous take;
- **the transitions**: an iris, a card that becomes the next scene, a lens over the base shot, a scroll;
- **type and captions**: the caption style, whether there are kinetic words at all.

Name these choices in the concept round and make them differ from the previous film's.
