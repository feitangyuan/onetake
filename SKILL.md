---
name: onetake
license: PolyForm Noncommercial 1.0.0 (free for noncommercial use; see LICENSE)
metadata:
  author: Patrick (github.com/feitangyuan)
  lineage: otk-7f3e1c
description: "Make short product / skill motion videos (10–30 s, narrated feature demos up to ~60 s) the way high-end launch clips are made — kinetic type, real UI as the material, a hand that causes every reaction, beats that carry into each other instead of replacing each other, hard cuts only where they mean something — without HyperFrames or Remotion. A single HTML composition where every value is a pure function of time, built from a library of measured moves (springs, entrances, carries, contact, camera), rendered frame by frame with real shutter motion blur (1080p30 drafts, 4K60 final), with synthesised sound effects that share one room and an oracle that fails a slideshow before a human has to watch it. Use for 做个动效短片 / 产品宣传片 / 介绍视频 / 发布视频 / 15 秒 launch video / 给 skill 或 app 做个视频 / promo / teaser, for turning real pages or screen recordings into a cut, for product feature demos (产品功能演示 / 功能展示动效) where the UI is rebuilt in HTML from screenshots instead of screen-recorded (不录屏 / 复刻界面 / 截图还原 UI), for narrated cuts with voice-over and subtitles (配音 / 字幕 / 换配音) and for the same film in other languages (日语版 / 多语言 / 本地化), for adding motion vocabulary (动效库 / 转场 / 衔接), and for auditing why a motion video reads as a slideshow (像 PPT / 没节奏 / 一个一个展示 / 转场生硬)."
---

# onetake

Short motion films about a product, built from the product. Not a video editor, not a slideshow
generator: a **composition** (one HTML file, `window.__seek(t)`), a **move library** (`lib/motion.js`),
**footage** recorded from the real thing, a **sound palette** that shares one room, and an **oracle**
that says whether the cut has a rhythm and whether it carries, before a human has to watch it.

Six films taught it. **motion-web** took three cuts: one and two were rejected as 「PPT 式一个一个展示」
for a uniform cadence — the rhythm half. **Pocket Weather Club** had the rhythm and was *still* PPT: its v1
passed every rhythm check and was rejected, because each beat replaced the one before. v3 was accepted when
every beat grew out of the last — the character lands on the headline, the page grows out of its card, a
stage opens from the character. That is the carry half. **One dot** added the operator: with a still camera it was
「就缺灵动的跟踪运镜」; with a camera that chases what each beat frames — lagging, leaning, settling — it was
「运镜、镜头和物理都没问题」. **knockon** carried by cause: a light tabletop machine where every beat is the collision
that starts the next. **clearing** carried by scale: one take from a year to a free half hour and back, a camera that
chases the anchor on screen so it lands the same at 1× and 300×. **overlap** was the meaning lesson: its first cut was
「美术挺棒但没看出来啥意思」, and adding labelled cursors made it worse; it read only once the idea was built into the
artwork — an & hidden in two noise plates that appears at the instant the passes come into register. Everything here
exists so the next film starts where those films ended.

## When this skill, and when not

- A launch / teaser / intro clip for an app, a page, a skill, a feature — **yes**.
- A narrated feature demo (30–60 s) that shows the product being used, possibly in several languages — **yes**:
  rebuild the UI instead of recording it (§4, `references/product-demo.md`).
- The user has a reference clip they want the *feel* of — **yes**, start at §1.
- Long-form, talking-head, editing existing footage with transitions — **no**.
- The user names HyperFrames or Remotion explicitly — use what they name. Otherwise this pipeline.

## The protocol — in this order, no skipping

### 1 · Deconstruct the reference before touching anything (硬规则)

```bash
python3 scripts/analyze_ref.py ref.mp4 --out ana/     # energy map, cuts, stillness, contact sheets, motion line
```

Read the energy map and the sheets and write down the numbers the film has to match. The energy map says *when*
the film moves; the `motion:` line says *how* —
median t80 (snaps or S-curves) and smear (rendered with motion blur or not). What decided the motion-web film:
the reference was **34 % dead-still**, had **7 hard cuts** in two bursts, and kept every element **small with a
lot of white space**. None of that is obvious from watching once, and a film built without measuring it came
out on a uniform cadence — twice. `references/reference-deconstruction.md`.

### 2 · Concept — three central ideas before any beat sheet (硬规则)

A concept is one sentence about the *picture*, not the product: the single idea the film is made of. Write three
that differ in that idea — not three stories told with the same cards:

- **one element transforms through everything** — a dot is the caret, splits into the skill list, hollows into a
  loading ring, unrolls into a spring curve, lands as the dot on the i of the wordmark;
- **one camera move through scale** — start inside the caret, pull out to the input, dive through the send button
  into the work, come out through the finished film (`cases/clearing-15s`: a year → one day → a half hour → back);
- **a before/after split** — the same beats as a slideshow on the left and carried on the right, until the right
  side breaks into the left;
- **a chain reaction** — every beat is the collision that starts the next (`cases/knockon-15s`);
- or a physical metaphor, one continuous surface, a typographic system…

For each: the hook frame, what carries every boundary, what it rules out (no cards? no cuts?), and **its look** —
a preset from `looks/` (`python3 scripts/look.py sheet` → `gallery/sheets/looks.png`: paper, dusk, tabletop,
ultramarine, riso, ember, each measured from an accepted film), the product's own colours
(`look.py from-shot shots/*.png --out look.json`), or one made for this film. Show the three and let the user pick.
The template's story — kinetic words → typed prompt → ticking checklist → result → staccato
hits → black wordmark — is one concept, never the default: an operation demo built on it passed every oracle leg
(carry 1.00) and was sent back as 「和 motion web 很像…没有创造力」.

### 3 · Storyboard as rhythm *and* carry

Write the chosen concept as a **beat sheet**: `t · beat · what moves · what is still · what carries into the next
beat`.

**Rhythm.** Vary shot length by ≥ 4× (0.25 s words next to 2.5 s holds). At least one stretch of near-silence in
picture and sound. One story — the concept's — not a catalogue. Small elements, big ground.

**Carry.** At every section boundary, name the thing that survives it and moves: the hand, the subject, a
container that becomes the next scene (`morphRect`), a stage that opens from the subject (`iris`), a camera that
pushes into a card until it is the scene (`zoomThrough`), a cast that folds into the lockup (`gather` → `seal`).
If nothing survives, it is a slide change, whatever the rhythm. Bare cuts belong to bursts of hits and the end
card, when the concept has them. `references/rhythm.md`.

### 4 · Footage from the real thing — or the UI rebuilt from screenshots

```bash
python3 scripts/record_footage.py footage.json --out footage/
```

Real pages, driven in real time by Playwright (wall-clock-paced sweeps, wheel steps, clicks),
recorded at the size you will show them, with a magenta marker injected the instant the input starts
so the action frame is findable afterwards. Frames come out at 30 fps as JPEG; the pointer path is
saved so the composition can draw the hand back in — **the viewer must see the cause, not just the
effect**. Config format in the script's docstring.

**Or rebuild it.** When the film walks through an app's features (and above all when it has a voice or other
languages), the user screenshots or records only reference takes, and the UI is rebuilt in HTML in the reference's
own pixel frame. Every string lives in a table, every state is written by a pure `set(state)`, and the replica sits
on the plane where the camera can close in at any zoom. Highlights are measured from its DOM (`lib/ui_kit.js`).
Narration comes from `scripts/vo_tools.py`: audition, lines, word times, subtitles. A second language is `?lang=`
on the same comp, its VO mapped onto the authored timeline by `UIK.timeWarp` knots on words that mean the same
thing, checked pixel-identical for the source language with `scripts/frame_diff.py`. The content stays the product's
real output. Method, numbers and what bit: `references/product-demo.md`. It is a technique, not a look: palette,
stage, camera grammar and transitions are chosen fresh in §2 every time.

### 5 · Compose — one file, pure functions of time, moves from the library

```bash
mkdir -p cases/my-film && cp templates/comp.html lib/motion.js cases/my-film/   # the template loads motion.js → window.OM
python3 scripts/probe.py my-film/comp.html        # as soon as it plays end to end: what carries each boundary, each move's curve
```

Pick moves by looking at `gallery/sheets/<move>.png` — six frames over the speed curve of what moves. The library
has 39: entrances, carries, contact and live sims, camera and its projection helpers, and a fluid set (a light field, ripples, silk, a belt, SwiftUI springs); each is a function of time returning numbers for a DOM
transform or a canvas call. Never re-derive a spring or an ease with fixed constants. The template is the
motion-web film (kinetic words, typed prompt, ticking checklist, fly-throughs, live sims, a hold, staccato hits,
one continuous hand path every sim reads from) — copy its beats only when that is the concept picked in §2;
otherwise keep its contract and helpers and write the concept's own beats. Everything is `f(t)`; sims are pre-simulated once at 240 Hz and
sampled. Preview `?play`, pin `?t=6.4&hud`. `references/motion-library.md`, `references/composition.md`.

**The look ships with the comp.** `python3 scripts/look.py apply ember cases/my-film/comp.html` (or a `look.json`)
writes `look.js` beside it: the eight colours as CSS variables and `LOOK.color`, three OFL faces subset to the glyphs
the comp sets and inlined, so the `file://` render gets real type. Load it before the comp's script, write against
`var(--ink)` / `var(--display)` or `LOOK.font('display', 96)`, and chain `window.__ready` on `LOOK.ready`. Re-run it
after copy changes; it names any character a face lacks (`--cjk <font>` for Chinese / Japanese / Korean).

**Camera: keyed, but operated.** `OM.camera(t, keys)` puts the camera where each beat needs it; the feel of an
operator comes from how the keys are placed: key the subject ~0.1 s ahead on `sineInOut` to follow it, key the landing
point before a snap on `expoInOut` to whip to it, add a hand (a slow two-sine float, zero in the holds) and `OM.shake`
on every landing. Draw a faint `OM.lattice` farther back, or on an empty ground the move doesn't read. With a camera,
`__track` returns screen boxes (`OM.projectBox`), `__motion` hands render.py the travel, and `__meta.inFrame` names
what must never leave the frame. The method, with code: `references/composition.md` → *A camera*.

### 6 · Render — 1080p30 drafts, 4K60 only after acceptance

```bash
python3 scripts/stills.py comp.html --times 0.7,2.4,3.8,6.2,9.9,12.7 --out stills.png   # look before you render
python3 scripts/render.py comp.html --out draft.mp4 --sfx sfx.wav            # 1920×1080 · 30 fps · 180° shutter
python3 scripts/render.py comp.html --out film.mp4 --final --sfx sfx.wav     # 3840×2160 · 60 fps, once the cut is accepted
```

The shutter is real motion blur: each moving frame is several seeks across the open shutter, averaged in linear
light; holds are detected and skip it. A capture is a Chrome screenshot (~150 ms; the page itself draws in under 1 ms),
so render.py runs `--workers` browsers in parallel processes (default cores − 2, max 8). A page that defines
`window.__motion(t0, t1)` — the farthest anything travels on screen, camera included — gets as many captures per frame
as keep copies `--gap` px apart, between `--samples-min` and `--samples-max`; if a fast move shows bands, tighten the gap and raise the cap. Budget: the
one-dot camera cut took 103 s for 2,480 captures on 8 workers (one browser: ~0.2 s a capture, ~8.5 minutes) — tell
the user the estimate before starting a long render.

### 7 · Sound — a palette in a room, never one beep per event

```bash
python3 scripts/sfx_palette.py --demo demo.wav     # quick pass: the synthetic palette (see templates/sfx_score.example.py)
python3 dump_events.py && python3 score.py         # the films since one-dot: the comp's __events() → recorded + synthesised mix
```

Two ways, one rule. The **palette** is five synthesised materials (air, wood, glass, sub, bubble) in one reverb, peaks
at −8 dBFS so music can sit on top — enough for a draft. Every accepted film since one-dot uses a **score.py**: recorded
sources (Kenney's CC0 packs, UIowa MIS, Voxengo IRs — not shipped here; download them yourself) layered with synthesis, timed and panned
from `window.__events()`, convolution reverb, the music ducked under the hits, mastered to −16 LUFS with the ceiling
low enough (−3.5 to −4 dBTP) that the AAC render stays under verify's −3 dBFS. Fewer events than beats either way: the
first motion-web pass put a raw sine pop on every event and was rejected as 低劣 within a minute. Before shipping any
recorded source inside a product, check its licence (Mixkit's does not allow redistributing the files). `references/sound.md`.

**Music is royalty-free by default.** Look for a track licensed for reuse (NCS, Pixabay Music, the YouTube Audio
Library, Free Music Archive under a CC licence that allows it) and keep its source and licence next to the score. A
commercial or copyrighted track goes in only when the user supplies it and says so; never pull one in on your own.

### 8 · Verify before showing

```bash
python3 scripts/verify_promo.py draft.mp4 --comp comp.html --ref ref.mp4 --shots 0,1.6,3.0,4.8,7.0,9.6,12.1,13.25,14.3
```

Rhythm legs fail uniform shot lengths, no dead-still stretch, clipped or never-quiet audio. **burst** fails only
when `--ref` has one and the film doesn't; without a reference it is a warning — a concept without hits isn't wrong.
**continuity** fails beats that replace each other (carry score < 0.5) — the only leg that failed both rejected
Pocket Weather cuts (v1 0.00, v2 0.40) while the accepted films passed (v3 0.75; motion-web 0.56, a warning).
**curves** fails fast moves (> 80 px/frame) in a film without shutter blur. **framing** fails any frame where an id
in `__meta.inFrame` is off frame (or, marked `'whole'`, cut) — the one-dot film's first camera render lost its dot
behind a snap and nothing else noticed. With `--ref`, the reference's energy map and motion line print alongside.

## Hard rules (each one cost a cut)

- **Never default to the template's story.** Three concepts that differ in their central idea; the user picks
  (§2). A new film in the template's beats reads as the template, however good the craft.
- **Never carry the last film's look into the next.** Palette, stage, camera grammar, transitions: the tools
  (replica, narration, time warp) are reusable, the look is not. Name those choices in the concept round. A preset
  from `looks/` is fine when it is picked there by name; a silent default is not.
- **A second language never forks the composition.** `?lang=`, a time warp, and the source cut checked
  pixel-identical. A copied comp doubles every later fix.
- **Never cut on a metronome.** Equal shot lengths read as slides no matter how good each shot is.
- **Never replace a beat — carry it.** Something on screen survives every section boundary and visibly moves or
  scales into the next beat. Mutually exclusive scenes (`display:none` swaps) are slides even with perfect rhythm.
  The exceptions are a burst of hard-cut hits and the end card.
- **Never show a page as a thumbnail expecting its motion to read.** Either full-frame with the hand, or
  a *component* of it live in a card. Small cards of whole pages showed nothing.
- **Never let the frame be always in motion.** Rests are what make the bursts land; the reference is
  still a third of the time.
- **Small elements, big ground.** The genre's frame is 70 % white. Full-bleed footage is the exception
  (one calm hold), not the rule.
- **The cause must be visible.** The hand drawn from the recorded path, or the concept's own subject — a dot that
  splits, a ball that lands. A page reacting to nothing reads as a screensaver.
- **Moves from the library, curves chosen by t80.** One hand-rolled smootherstep everywhere makes every move the
  same soft S-curve; snaps (`ease.expoOut`, t80 .23) and springs are what lands.
- **Fast moves need the shutter.** Over 80 px/frame without motion blur strobes into copies. render.py's default
  shutter is the fix; CSS blur is not.
- **A camera that chases, and never loses the subject.** A still camera left the one-dot film 「就缺灵动的跟踪运镜」;
  a camera that chases what each beat frames was accepted. Declare `__meta.inFrame`; for a snap, key where it lands
  before it moves.
- **Drafts at 1080p30.** No 4K60 render before the cut is accepted.
- **No particles / confetti / speck bursts.** They read as a template. Let the type itself land with
  squash and wobble if a beat needs a flourish.
- **One material set for sound, one room.** Every event getting its own synth tone is the audio version
  of the slideshow.
- **Everything deterministic.** `__seek(t)` twice must give the same frame — the shutter depends on it; sims are
  precomputed from a fixed seed; no `Math.random()` on the render path (`OM.rng(seed)`).

## Files

| path | what |
|---|---|
| `lib/motion.js` | the move library → `window.OM`: curves, springs, entrances, carries, contact, sims, camera, fluid |
| `looks/looks.json` | six starting looks (eight colour tokens, three faces each) measured from accepted films; `looks/fonts/` the OFL faces and their licences |
| `scripts/look.py` | `list` / `sheet` / `check` the looks, `from-shot` a look from product screenshots, `apply` → `look.js` with the faces subset and inlined |
| `lib/ui_kit.js` | → `window.UIK`: a rebuilt UI on the plane (`stage`, `domLocal`, `rectCache`, `flow`), the content-hugging `glowRing`, legibility (`screenPx`, `zoomFor`), languages (`tr`, `loadFont`), `timeWarp` between a narration and the authored timeline, `subAt` |
| `gallery/gallery.html` | one live demo per move (`?demo=ribbon&play`); `gallery/sheets/<move>.png` six frames + speed graph; `gallery/sheets/looks.png` the looks |
| `scripts/analyze_ref.py` | reference → energy map, cuts, stillness, contact sheets, motion line (t80, smear), JSON |
| `scripts/record_footage.py` | config → real-time recordings with action marker → 30 fps frames + paths |
| `scripts/probe.py` | comp → what is on screen per frame → continuity per boundary, curves per move |
| `scripts/render.py` | comp → mp4: 1080p30 draft by default, `--final` 4K60, shutter motion blur sized by `__motion`, parallel `--workers`, `.render.json` |
| `scripts/stills.py` | comp → contact sheet of chosen times |
| `scripts/vo_tools.py` | narration: `tts` (Kokoro, English and Japanese via a kana reading, auditions), `words` (faster-whisper), `plan` (line starts), `subs` (chunked, timed) |
| `scripts/frame_diff.py` | two comps (or one with `?lang=`) at chosen times → identical or not, with diff images |
| `scripts/sfx_palette.py` | the sound materials, the room, `Score` helper, `--demo` |
| `scripts/verify_promo.py` | the acceptance oracle: rhythm legs, plus continuity, curves and framing with `--comp` |
| `scripts/gallery.py` | gallery demos → sheets |
| `scripts/test_motion.js` | `node scripts/test_motion.js` — the library's numbers |
| `templates/comp.html` | composition skeleton (the motion-web film) on the library |
| `templates/footage.example.json` | footage config used for the motion-web film |
| `templates/sfx_score.example.py` | the motion-web sound score |
| `references/reference-deconstruction.md` | how to read a reference in numbers |
| `references/rhythm.md` | rhythm (motion-web's three cuts) and carry (Pocket Weather's three) |
| `references/motion-library.md` | every move, applying it to DOM or canvas, the curve table, which carry for which boundary |
| `references/composition.md` | the `f(t)` architecture, primitives, hand path, probe, render and shutter |
| `references/sound.md` | palette, room, levels, what sounded cheap |
| `references/product-demo.md` | feature demos without a recording: the replica, legibility, highlights from the DOM, narration, languages and the time warp, brand end clips, what bit |
| `cases/motion-web-15s/README.md` | case 1: the rhythm film — beat sheet and numbers |
| `cases/one-dot-15s/README.md` | case 3: one dot is the whole film — the concept step, an operator's camera, recorded + synthesised sound |
| `cases/knockon-15s/README.md` | case 4: the light chain-reaction film — causal carry, height from shadows, sound placed from the comp's `__events()` |
| `cases/clearing-15s/README.md` | case 5: the one-take dive through scale — levels drawn in their own units, a screen-space camera for 1×–300×, sound driven by the zoom's speed |
| `cases/pith-21s/README.md` | case 6: the reverse dive — 440× → 0.52× out of one phosphor pixel, the product's own dark→light theme flip as the film's one transition, a mascot close-up used as the rhythm break, and a claim built from seven objects already on screen |
| `cases/ebb-15s/` | case 7: one take through five places, carried by a field of light — keyed camera with a hand, shake and depth, odometer digits, a flood that drains in rings onto the next scene, silk cards on belts at three depths |
| `cases/<film>/` | every film made with this skill: the film and a README (beat sheet, numbers, what was rejected and why). Also: overlap, unbroken, skill-demo, and onetake's own launch film. The films' source code is not included |

Requires: python3 with `playwright` (chromium), `numpy`, `scipy`, `Pillow`, `matplotlib`, `fonttools` + `brotli` (looks); `opencv-python` for the
motion line; `ffmpeg` / `ffprobe`; `node` for the library tests. Narration: `faster-whisper` (python3), and Kokoro
(`kokoro-onnx`, `soundfile`, plus `misaki[ja]` and `unidic-lite` for Japanese) in `~/.cache/kokoro/venv`.
