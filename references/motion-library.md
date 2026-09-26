# The motion library — `lib/motion.js`

Numbers, not styles. Every move is a pure function of absolute film time that returns plain values — offsets,
scales, opacity, radii, matrices — which you write into a DOM transform or a canvas call. No DOM access, no
dependencies, no build step: `<script src="motion.js">` gives `window.OM`; `require('./motion.js')` works in node.
`node scripts/test_motion.js` checks the numbers on this page.

**Look before you pick.** `gallery/sheets/<move>.png` is six frames of the move above the speed of what it moves
(px/frame at 60 fps, t80 per move). A few moves share a sheet: `liftOut` is on popIn's, `impact` on hop's and
impactSplit's, `cursor` on press's, `sim.*` on sims', `view` and `dof` on camera's. `gallery/gallery.html?demo=<move>&play`
loops it live; `python3 scripts/gallery.py` re-renders the sheets after a change to the library.

Two films are the source. **motion-web** (case 1) gave the entrances and the live mechanisms. **Pocket Weather
Club** (case 2) gave the carries — the moves that turned a rejected slideshow into an accepted film.

## Applying a move

```js
const w = OM.wordRise(t, 0.15);
// DOM
el.style.opacity = w.op;
el.style.transform = `translateY(${w.y}px) scale(${w.s})`;
// canvas
g.save(); g.globalAlpha = w.op; g.translate(x, y + w.y); g.scale(w.s, w.s); g.fillText(word, 0, 0); g.restore();

const z = OM.zoomThrough(t, 6.3, 7.3, card);               // a matrix move: the same numbers either way
g.setTransform(...z.matrix);                                // canvas
layer.style.transform = `matrix(${z.matrix.join(',')})`;    // DOM, with transform-origin: 0 0
```

Times are absolute seconds, so the timeline is a list of numbers at the top of the composition and any frame can
be sought. The sims, which need the hand's history, are built once in `__ready` (`OM.sim.jelly(card, hand)`) and
sampled with `.at(t)`. Utilities: `clamp`, `lerp`, `seg(t, t0, t1)`, `sstep` / `ssstep`, `spline(knots, t)` (Hermite
through `{t, x, y}` → `[x, y]`), `rng(seed)` for anything random.

## Curves — choose by t80

t80 = the share of a move's duration spent before 80 % of its travel is done. probe.py reports it for every move
in a composition and analyze_ref.py for a reference film, so a curve here, a move in your film and a move in the
reference compare on one number.

| curve | t80 | reads as |
|---|---|---|
| `ease.expoIn` | .97 | a launch; exits only |
| `ease.linear` | .80 | mechanical: a ticker, a tracking shot |
| `ease.smooth` · `sineInOut` | .71 · .71 | soft S |
| `ease.smoother` | .67 | the symmetric S Pocket Weather v3 used for every move |
| `ease.cubicInOut` · `quintInOut` · `expoInOut` | .63 · .58 · .57 | a camera move with weight (`whip`, `zoomThrough`) |
| `ease.quadOut` | .55 | a gentle arrival |
| `ease.cubicOut` · `circOut` | .42 · .40 | UI arrival |
| `ease.quartOut` · `quintOut` | .33 · .28 | a snap |
| `ease.backOut` | .24 | a snap past the mark and back |
| `ease.expoOut` | .23 | there almost at once, then settles (`tween`, `morphRect`, `iris` default to it) |

`OM.bezier(x1, y1, x2, y2)` turns any CSS cubic-bezier into a curve; `OM.t80(curve)` measures one;
`OM.tween(t, t0, t1, curve)` applies one between two times.

Springs are closed forms — `OM.spring(tau, zeta, omega)` — so they seek like a curve:

| ζ, ω | 80 % at | settles ±2 % | overshoot | used by |
|---|---|---|---|---|
| .5, 28 | 0.067 s | 0.29 s | 16 % | `tick` |
| .5, 26 | 0.073 s | 0.31 s | 16 % | `letterDrop` |
| .6, 22 | 0.093 s | 0.27 s | 9.5 % | `wordRise` |
| .47, 17 | 0.109 s | 0.49 s | 19 % | `maskRise` |
| .62, 18 | 0.116 s | 0.33 s | 8 % | `popIn` |
| .7, 16 | 0.140 s | 0.37 s | 5 % | the calm window hold |
| .78, 14 | 0.172 s | 0.26 s | 2 % | `flyThrough` |

A spring reaches 80 % within a quarter to a third of its settle time — a snap with an overshoot chosen by ζ.
`OM.settle(ζ, ω)` gives the settle time so the next beat can start on it; `OM.springVel` is its exact velocity
(× the distance, it feeds `squash`); `OM.ring(tau, decay, omega)` is the decaying wobble after a hit.

## enter — something arrives

| move | returns | what it is | from |
|---|---|---|---|
| `wordRise(t, t0, {zeta, omega, dist, s0, fade})` | `{op, y, s}` | a word lands: spring rise and scale; opacity leads the spring so it never reads as a fade | motion-web |
| `letterDrop(t, t0, i, {stagger, dist, squash})` | `{op, y, sx, sy}` | wordmark letters drop; speed flattens each, the spring restores it | motion-web |
| `popIn(t, t0, {rise, s0})` · `liftOut(t, t1, {dur, dist, blur})` | `{op, s, dy}` · `{op, dy, blur, s}` | a card springs up · lifts, grows a touch and blurs away | motion-web |
| `maskRise(t, t0, i, {stagger, dist})` | `{y, visible}` | lines rise into place from behind a clip | Pocket Weather |
| `typeOn(t, t0, text, {cps, blink})` | `{n, str, done, caret}` | typing at a steady rate, caret solid while typing | motion-web |
| `tick(t, tl)` | `{on, s}` | a checkbox pops from .8 when its line is reached | motion-web |
| `flyThrough(t, t0, hold, {from, exit, rotY0, blurIn})` | `{visible, x, rotY, rotX, s, op, blur}` | a screen flies in tilted, holds, flies out (CSS 3D) | motion-web |

## carry — the next beat grows out of this one

These make a boundary *carried* in probe.py's terms: something survives it and visibly moves or scales into the
next beat.

| move | returns | what it is | reach for it when |
|---|---|---|---|
| `morphRect(t, t0, t1, A, B, {curve})` | `{x, y, w, h, r, cx, cy}` | container transform: one rect becomes another | the thing pressed becomes the result (button → window, card → page) |
| `iris(t, t0, t1, cx, cy)` | `{r, covered}` | a circle opens from a point until it covers the frame | the subject opens its own world (Pocket Weather 6.95 s) |
| `zoomThrough(t, t0, t1, target, {curve, fit})` | `{s, tx, ty, matrix}` | log-space push until the target fills the frame | one card among many is the next scene |
| `hop(t, t0, t1, from, to, {height})` | `{x, y}` | an arc from one slot to the next; land it with `impact` | the subject picks the next thing (Pocket Weather 1.8 s) |
| `gather(t, t0, t1, i, n, from, to, {stagger, arc, spin})` | `{x, y, rot}` | the cast travels on fanned arcs into a cluster | many become one group (10.05 s) |
| `ribbon(t, switches, {amp, lag})` | `{shift, index, wobble, rot, sx, sy, textDx}` | an elastic rail: panels switch with a ring-out, words lag behind | options change under the hand (8.05, 8.95 s) |
| `seal(t, t0, t1, {r, turns})` | `{r, rot}` | a turning disc grows under the folding cast | the cast becomes the brand mark (11.5 s) |
| `staccato(t, list)` | `{word, i}` | hard-cut words | a burst of hits — the one place a bare cut is right |

A `camera` move over one continuous world (below) carries too: at its boundaries everything survives.

## contact — one thing causes another

| move | returns | what it is | from |
|---|---|---|---|
| `impact(t, tHit, {decay, omega, sqx, sqy})` | `{r, sx, sy}` | the landing: squash on the hit, ring out | both |
| `impactSplit(t, tHit, x, cx, {width, spread, bounce})` | `{dx, dy, rot}` | glyphs split by distance from the hit, bounce, rejoin | Pocket Weather |
| `press(t, tc, {depth, flash})` | `{s, sq, down, active}` | a click: dip, ring, state flip | motion-web |
| `cursor(t, knots, clicks)` | `{x, y, s}` | the pointer on the hand spline, shrinking at each click | motion-web |
| `squash(vx, vy, {k, max})` | `{ang, sx, sy}` | stretch along the velocity, thin across it | motion-web |
| `sim.magnet` · `follow` · `jelly` · `verlet` `(card, hand, opts)` | `{at(t), …}` | magnetic button, spring follower, jelly ring, Verlet string — precomputed at 240 Hz | motion-web |

## camera

| move | returns | what it is |
|---|---|---|
| `camera(t, keys)` | `{x, y, zoom, rot}` | keyed camera `{t, x, y, zoom, rot, curve}`, zoom interpolated in log space |
| `view(cam, {depth})` | `[a, b, c, d, e, f]` | the matrix for a layer at `depth` (0 = focus plane, + farther, − nearer): parallax from one camera |
| `dof(depth, focus, {k, max})` | px | blur by distance from the focus plane |
| `whip(t, t0, dur, dist)` | `{k, d}` | a whip pan |
| `shake(t, tHit, {amp, decay, freq, seed})` | `{x, y, rot}` | decaying, deterministic, zero before the hit |
| `drift(t, t0, t1, amount)` | scale | the slow push of a hold, 1 → 1 + amount — verify's rest leg counts it as motion, so keep it off the rests |
| `lattice(cam, {depth, spacing, px})` | `{matrix, r, spacing, x0, x1, y0, y1}` | OD · the visible points of a far grid through `cam`, dots a constant `px` on screen — something for a move to slide against |
| `project(M, x, y)` · `unproject(M, x, y)` · `projectBox(M, box)` | `[x, y]` · box | world ↔ screen through a `view()` matrix; `__track` boxes on screen |
| `screenTravel(c0, c1, cMid)` | px | how far the frame's corners move between two cameras — the camera's share of `__motion` |

**A keyed camera that feels operated.** Still, the one-dot film was 「就缺灵动的跟踪运镜」; with a camera that chases
what each beat frames it was 「运镜、镜头和物理都没问题」. Keys get you there: key the subject a little ahead
(~0.1 s) on `sineInOut` to follow it, key the landing point before a snap on `expoInOut` to whip to it, add a hand
(a slow two-sine float, zero in the holds) and `shake` on every landing (composition.md → *A camera*). ebb and the
onetake launch film were made this way. A move on an empty ground doesn't read: draw a `lattice` farther back
(depth 1.2). The camera's travel adds to every element's: the one-dot camera cut peaked at 935 px/frame at 30 fps.

## fluid — a ground of light, silk, a belt (ebb)

Promoted from `cases/ebb-15s` (accepted 2026-09-24), measured from David Ch's Shipper launch and Nazday's Elera carousel.
The comp is the worked example: the light field is time, the flood drains in rings onto the next scene, silk fills every
card, the belt slows with its own clock.

| move | returns | what it is | reach for it when |
|---|---|---|---|
| `swiftSpring(tau, kind, {duration, bounce})` | `number` | SwiftUI's `Spring(duration d, bounce b)` = `OM.spring` at ζ 1 − b, ω 2π/d; `.smooth` b 0, `.snappy` .15, `.bouncy` .3 | a UI should feel native (Apple) rather than "animated" |
| `lightField(level, {rest, top, r0, r1})` | `{cx, cy, rx, ry, tilt, horizon, core, stops}` | a persistent glow anchored below the frame: level 0 at rest (horizon 0.84 H), 1 flooded. Fill the ellipse with a radial gradient at `stops`; `core` (half radius) is where type turns white. Flood ≤ 0.4 s, drain ~1 s | the ground itself should be the punctuation: it rises, floods, and the next scene appears as it drains |
| `ripple(t, t0, {n, stagger, dur, rMax})` | `{r: [radii], done}` | n rings leave one point `stagger` apart; fill the flood outside r[0], alternate two tints between, the world shows inside the last | a flood has to end on a new scene without a wipe |
| `silk(tau, seed, stops, {gx, gy, contrast, out})` · `silk.ramps` · `silk.ramp` | RGBA `gx × gy` | domain-warped noise, two octaves, 16×20, ×3.4; putImageData, draw up with blur(28 px per 520 wide) and one pale screen wisp. Ramps `ember` `peach` `dusk` carry the dark fold between two brights | a card, wallpaper or lock screen should be alive without content |
| `carouselLoop({dur, start, speed, rampDur, stop})` | `{at(t) → {x, tau}}` | a belt at constant speed after a `.smooth` start, integrated once; `tau` is a clock that slows with it — drive each card's own loop from it | many items should flow past and settle together (Elera: 0.106 W/s) |

## Speed and the shutter

Peak speed decides whether a move needs motion blur. Measured in the gallery at 60 fps: `whip` 540 px/frame,
`iris` 206, `flyThrough` 189, `morphRect` 156, `ribbon` 118, `shake` 115, the follow sim 102, `zoomThrough` 72; the
entrances and the other carries stay under 50. **At 30 fps every number doubles**, so in a draft most carries
cross verify's 80. Render with render.py's default shutter and they smear as far as they travel. The `blur` that
`liftOut` and `flyThrough` return is a CSS filter for depth; it does not replace the shutter.

## Candidates — measured, not yet in a film

A move enters `lib/motion.js` only after a film that used it was accepted: it is written inside that film's
comp.html first, then promoted with a test, a gallery sheet and a row above. The
moves below were measured frame by frame from references and have not been in an accepted film of ours: **HF** — the
Higgsfield × Claude Opus 5.5 launch (41 s, 24 fps, x.com/higgsfield/status/2102451022216179935); **PK** — Pinckus's
part of Flatwhite Motion's Rednote Buildathon piece (7.5 s, 30 fps, x.com/Pinckus102xz/status/2101491848179331220, made
in Cavalry); **FL** — two fluid-ground references: David Ch's Shipper launch (49.9 s, 60 fps,
x.com/chhddavid/status/2102666619029999989) and Nazday's Elera post carousel (16 s, 60 fps, 1600×1200,
x.com/nazmijavierl/status/2102712897701097828) — the FL rows are promoted, see *fluid* above. Build them in the film from these numbers, not from memory; promote them when the film is accepted. Times
are the reference's, sizes at 1080p.

| candidate | what it is | measured |
|---|---|---|
| `glowPress` | a key lit from inside — no cursor; the lit state is the click | attack 1 frame, no ease-in; fill base → cream (rgb 212,122,102 → 250,208,193), brightest at +0.17 s; scale → 0.8 in 0.15 s; a radial halo in the base hue reaches 2.3× the key's width on the first frame, 2.7× at +0.17 s; hold 0.45 s while a white specular runs round the bevel; release 0.13 s back to base, left a shade lighter (219,142,121). 0.67 s in all, the camera drifting through it (8.29 s) |
| `glowBox` | an emphasis pill that lights the scene, then becomes the next one | born as a blurred glow at ~40 % width, full width in 0.2 s; label typed at ~23 cps, the newest glyph magenta for one frame; the whole ground takes a lime cast while it is on (spill); hard cut in to 2.9× with the ground defocused; a heartbeat to 0.8× and back (14.6 s); then it grows past 1.4× until its halo whites out the frame, and the next scene builds on that white (13.72–15.05 s). probe reads the bloom as a fade through the ground — list it in `__meta.cuts` |
| `contourGlow` | the model picks a part: a stroke that follows the silhouette, not a box | ~8–10 px; frame 1 soft amber, frame 2 crisp lime, then thins to nothing — 0.35 s; several parts at once, slightly staggered (16.08 s). Canvas: the cutout's alpha dilated, filled `source-in` |
| `heatType` | typing whose newest glyphs are hot and cool to ink; the line above cools to grey when the next begins | leading glyphs lime → magenta, ink after ~0.3 s (prompt 6.0–7.6 s); status lines reveal left to right with the same hot edge (9.1–10.0 s) |
| `focusIn` | rack-focus entrance: blur, a little extra scale and opacity settle together | the film's most used entrance — the big status text (10.6 s), the 4-up variants (28.3 s), the hero card |
| `wavefront` | stagger by position, not index: many items arrive as flat mattes along a front, then fill with texture | ~120 parts, magenta mattes sweeping in over ~0.5 s, texture following (15.1–15.7 s) |
| `scanBox` · `countUp` | a detection box: stroke, label typed, value counted up, colour = verdict | yellow 42 → 67 %, red 16 %, green 84 → 96 % whose tint fill blinks twice at 12 fps (17.0–19.5 s) |
| `punchLadder` | hard cuts in on one subject, each a step tighter | cuts at 16.08, 16.92, 17.75, 18.5 s through the parts field, each ~1.5–1.8× tighter; ANALYZE's 2.9× cut-in (14.26 s) is a one-step ladder |
| `exposure` | a flash to white that starts a `morphRect`: the photo is taken, then shrinks into the attachment | 5.38–6.0 s |
| `ghost` | a part arrives as a translucent tinted preview, then solidifies | orange ghost wheels (24.5–25.0 s) |
| `belt` (PK) | bands chase round a closed path — a conveyor that carries the title | boundaries along the arc length, each band a stroke with round caps (155 px on a 984 × 330 stadium); the ring unrolls from one point, runs on an expo start then creeps; one band laps and swallows the rest to end the beat (0–1.0 s). Code: `bandState` |
| `reel` (PK) | a slot reel with a pill as its window | index = Σ spring(t − tᵢ, .56, 34) over the step times; neighbours in the pill's colour one pitch above and below, fading by distance; the pill's width follows the fractional index; steps accelerate then brake (0.22 → 0.13 → 0.30 s) and land on the word the next beat needs (1.7–2.9 s). Code: `reelPos`, `reel` |
| `echo` (PK) | grey copies of the landed word stack above and below it, a staircase | copies spring out of the source (ζ .7, ω 26, 0.04 s apart) to ±1, ±2 rows with small x offsets, grey #3a3a3a under the source; retract into it before the next beat (2.9–3.3 s) |
| `lateType` (PK) | typing where one glyph arrives late (NEXT WRLD → WORLD) | ~14 cps, the late glyph ~0.25 s behind; reads as live input rather than a title (0.1–0.6 s) |
| `paintIn` (PK) | a part snaps in unpainted and takes its colour a beat later | grey #c2c2c2 at scale .55 and 0.35 rad, spring ζ .55 ω 20, colour at +0.09 s (3.4–4.0 s) |
| `iconCycle` (PK) | one part changes shape and icon on an accelerating cadence while a word cloud types out around it | swaps 0.26 → 0.16 s apart, each a 0.84 → 1 pop; new words take the current icon's colour, older ones dim to grey; for the last ~0.6 s rows fill the frame edge to edge, then a hard cut (4.4–6.0 s) |

`glowPress`, `glowBox` and `heatType` share one colour logic — hot when new, cooling to ink — so build them together.
