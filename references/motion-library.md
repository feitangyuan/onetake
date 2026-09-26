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

