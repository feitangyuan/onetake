# The composition — one HTML file, every value a function of time

## Contract

```js
window.__seek  = async (t) => { ... ; return true; }   // sets every style for time t; resolves when images are decoded
window.__ready = document.fonts.ready.then(() => { measure(); simulate(); return seek(0); });
window.__meta  = { dur: 15, fps: 30 };                 // render.py reads dur; probe.py also reads cuts: [t, …] (bare cuts you mean) and inFrame: {id: [t0, t1] | [t0, t1, 'whole']}
window.__track = (t) => ({ hand: [x, y], card: { x, y, w, h, op } });   // optional — probe.py follows these instead of auto-tracking; with a camera, boxes on screen
window.__motion = (t0, t1) => px;                     // optional — farthest on-screen travel between t0 and t1 (elements + camera); render.py sizes each frame's shutter from it
```

Query flags: `?play` runs it live in a browser, `?t=6.4&hud` pins a frame and shows the HUD.

`seek(t)` must be **pure**: calling it with 6.4 then 2.0 then 6.4 gives identical frames. So:
no state that accumulates across calls; springs as closed forms; anything that genuinely needs
integration (soft bodies, Verlet strings, magnetic pulls that depend on the hand's history) is
simulated **once** at 240 Hz from a fixed seed and sampled by index — `OM.sim.*` does exactly that.
Purity is also what makes motion blur possible: render.py seeks between frames.

## Moves come from `lib/motion.js`

Copy it next to the composition; `templates/comp.html` already loads `motion.js` and takes its helpers from it:

```js
const {clamp, lerp, sstep, ssstep, spring: spr, ring, spline} = OM;
place(el, x, y, s, op, blur)   // the template's one transform write per element per frame
```

Every move is a function of absolute time returning numbers — `OM.wordRise(t, 0.15)` → `{op, y, s}` — that you
write into a transform or a canvas call. Catalogue, curve table, DOM vs canvas: `references/motion-library.md`;
what each looks like: `gallery/sheets/<move>.png`. Don't hand-roll `ease` / `spring` with fixed constants:
Pocket Weather v3 did, and every move in it came out on the same symmetric S-curve.

## Primitives, and what each is for

| primitive | moves | genre role | knobs |
|---|---|---|---|
| kinetic words | `wordRise` | the setup line; one word per beat | word times, one accent colour |
| wordmark letters | `letterDrop` | the name; letters drop with **landing squash** (velocity → scaleY) | stagger 0.055 s, ζ 0.5 |
| prompt card | `popIn` · `typeOn` · `press` · `liftOut` | "what the user typed"; types at ~38 cps; hand clicks send | text, click time |
| checklist panel | `tick` | "what it does"; lines tick one by one; last line is the proof | lines, 0.24 s spacing |
| flying screens | `flyThrough` | outputs; 1000×625 tilted −18°→−9° Y, in from the right, out to the left | footage, hold 0.9 s |
| micro cards | `sim.magnet` · `sim.follow` · `sim.jelly` · `sim.verlet` · `press` · `squash` | mechanisms alive in 460×270 canvases; the hand pokes each | sim kind, position, window |
| browser hold | `popIn` × `drift` | the one calm beat; slow push-in 1.00→1.07 | footage, 1.2 s |
| staccato words | `staccato` | the hits; hard cut, uppercase, small | 0.22–0.36 s each |
| the hand | `cursor` on `spline` | the cause of every reaction | knots, click times |
| end card | — | black, wordmark | |

The template is the motion-web film, and that film has no carries. The moves that join one beat to the next —
`morphRect`, `iris`, `zoomThrough`, `hop`, `gather`, `ribbon`, `seal`, `impactSplit`, `camera` / `view` — are in the
library, from Pocket Weather. Which one for which boundary: motion-library.md → *carry*.

## The hand

One `HAND` array of `{t,x,y}` knots for the whole film; `hand(t)` is the spline through it. The cursor
SVG is drawn from it **and every sim reads from it**, so cause and effect agree by construction.
Clicks are a list of times; `OM.cursor` scales the pointer to 0.84 for 0.14 s at each.

For footage shots, the hand comes from `footage/paths.json` (what actually drove the page): rebuild
it as equal-time segments with smoothstep inside each, exactly as the recorder moved.

## Footage in the composition

Frames are `footage/frames/<name>/NNNN.jpg` at 30 fps. `info.json` gives `n` and `mark` (the frame
where input began). For a shot starting at `t0` that should show the reaction 0.2 s in:

```js
f = clamp(mark - round(0.2*30) + round((t - t0)*30), 0, n-1)
```

Set `img.src` only when the frame changes and push `img.decode()` into the pending list `seek`
returns — the renderer awaits it, so no frame is captured half-decoded.

## Probe — read the composition before rendering it

```bash
python3 scripts/probe.py comp.html                  # continuity per boundary + curves per move
python3 scripts/probe.py comp.html --out probe/     # + tracks.json and curves.png (speed of the top elements)
```

After every `__seek` it lists what is on screen — DOM elements by transformed rect and effective opacity, every
canvas `drawImage` / `fillText` / fill located through the context transform — so it needs no annotations. It
prints each beat boundary with what carried it (or `bare`), and each move with its t80 and peak px/frame. Run it
as soon as the storyboard plays end to end: a bare boundary is a comp edit, not a re-render. Thresholds and the
films they were calibrated on: rhythm.md → *carry*. `verify_promo.py --comp` turns the numbers into legs.

## Render

```bash
python3 scripts/stills.py comp.html --times 0.7,2.4,6.2 --out stills.png      # look before you render
python3 scripts/render.py comp.html --out draft.mp4 --sfx sfx.wav              # 1920×1080 · 30 fps · shutter 180° — every review round
python3 scripts/render.py comp.html --out film.mp4 --final --sfx sfx.wav       # 3840×2160 · 60 fps — only after the cut is accepted
```

**Drafts until accepted.** A 4K60 render of a cut that gets rejected is minutes spent on nothing; every round
before acceptance is 1080p30.

**Shutter.** A screenshot is an instant, so a fast move strobes into sharp copies; a camera integrates while its
shutter is open. For each frame render.py seeks several times across the open shutter (180° = half a frame
interval, centred on the frame time) and averages the captures in linear light — `--samples` (8) of them, or, when
the page defines `__motion`, as many as keep neighbouring copies `--gap` px apart on screen (4–48, set by
`--samples-min` / `--samples-max`). It captures the two ends first; if they are identical the frame is a hold and
is written as is. Because `__seek` is pure this is the real
integral, not a blur filter: a 100 px box moving 167 px/frame at 30 fps left a 173 px streak with a 27 px solid
core — what a 180° shutter predicts — and the holds stayed byte-identical to an unblurred render. It never
integrates across a cut: when one step between neighbouring captures carries the change, only the captures on the
frame time's side of it are averaged — Pocket Weather v3's hard cut at 11.5 s had become a one-frame dissolve
before that rule. `--shutter 0`
turns it off. CSS `filter: blur()` is not motion blur (it blurs across the motion as much as along it); keep it
for depth.

Cost is captures: a hold takes 2, a moving frame its sample count, and a hold has to be byte-identical — a canvas
comp whose springs are still ringing out rarely is (hold a key flat and keep the hand off it so a settled camera is). Pocket
Weather v3's 15 s draft, fixed at 8, had 93 holds in 450 frames: 3,042 captures, 7.4 minutes in one browser, where
motion-web's draft without shutter took 24 s. A streak is overlapping copies, so a fixed count shows its steps on
the fastest moves: v3's rail at ~340 px/frame smears 170 px in 8 copies 21 px apart, visible on text and edges in a
still, and the one-dot film's 633 px/frame opening stepped into bands. `__motion` puts the captures where the travel
is: the one-dot camera cut spent 4 on 293 of its 411 moving frames and 48 on three — 2,480 captures, where a fixed 8
would have taken 3,366 and still stepped. A capture costs ~0.2 s, most of it Chrome encoding the screenshot (156 ms;
the canvas draws in under 1 ms), so render.py deals the frames to `--workers` processes, each with its own Chromium
(default cores − 2, at most 8): that cut rendered in 103 s on 8 workers, ~8.5 minutes' work for one browser.
900 frames at 4K60 without shutter took 116 s.

render.py writes `<out>.render.json` (fps, scale, shutter, samples — a count, or `adaptive` with captures per moving
frame — workers, still and cut frames, captures, seconds); verify_promo.py reads it.
PNG frames, libx264 crf 16, `yuv420p`, SFX muxed in the same pass. Footage stays 30 fps inside a 60 fps render
(each frame shown twice); the composition's own motion is what gets the 60.

## A camera

One camera, keyed with `OM.camera`, and layers seen through it. Author in world coordinates (the 1920×1080 layout at
zoom 1) and set each layer's matrix before drawing it; the ground's gradient and vignette stay on screen. Keys say
where the camera is at a time and the curve that gets it there; the operator's feel comes from three layers on top:
a hand (a slow two-sine float, faded to zero in the holds), shakes on the landings, and a far lattice to slide against.

```js
KEYS = [                                                              // in __ready, after measure()
  { t: 0, x: 540, y: 0, zoom: 2.3 },
  { t: 3.95, x: 1330, y: 2, zoom: 2.15, curve: OM.ease.sineInOut },  // riding the caret
  { t: 5.35, x: 0, y: -12, zoom: 0.93, rot: -0.008, curve: OM.ease.quintInOut },
];
HITS = [[4.4, 6, 10], [12.7, 10, 9]];                                 // [t, amp, decay]
const handEnv = t => OM.sstep(0.1, 0.6, t) * (1 - OM.sstep(15.5, 15.9, t));   // zero where the frame must be dead still
function camAt(t) {
  const c = OM.camera(t, KEYS), e = handEnv(t) * 4.2;
  let x = c.x + e * (Math.sin(1.7 * t) + 0.6 * Math.sin(2.9 * t + 1)) / c.zoom, y = c.y + e * (Math.sin(1.3 * t + 2) + 0.5 * Math.sin(3.3 * t)) / c.zoom;
  let rot = c.rot;
  for (const [th, amp, decay] of HITS) { const s = OM.shake(t, th, { amp, decay, seed: Math.round(th * 100) }); x += s.x / c.zoom; y += s.y / c.zoom; rot += s.rot; }
  return { x, y, zoom: c.zoom, rot };
}
function seek(t) {
  CAM = camAt(t);
  ground();                                                           // screen space
  const G = OM.lattice(CAM, { depth: 1.2 }); mat(G.matrix);          // a dot of radius G.r at every lattice point
  mat(OM.view(CAM));                                                  // the world layer: everything the story draws
  TRACK = { dot: part(dot, t), … };
}
```

**Chase, don't follow.** A key that lands where the subject *will* be, reached on an `expoInOut`, reads as an operator
snapping to it; a key that trails the subject by ~0.1 s on `sineInOut` reads as one following it. For a snap faster
than the move, key the landing point before the subject gets there. Keep the hand off the holds: a floating camera is
never dead still, and the rests are what make the moves land.

**Report the screen, not the world.** With a camera, `__track` returns boxes on screen (`OM.projectBox(OM.view(CAM), box)`),
so probe measures what the viewer sees move. `__motion(t0, t1)` is the larger of `OM.screenTravel(cam(t0), cam(t1),
cam(mid))` and each box's edge travel between the two times; render.py sizes each frame's shutter from it (*Render*
above). `__meta.inFrame = { dot: [0.5, 15], mark: [12.2, 15, 'whole'] }`
makes verify fail any frame where the dot is off frame or the name is cut.

**Deep zoom: key the screen, not the world.** Past ~20× a world-space move swings the subject a frame-width for every
pixel of error. Key where an anchor A sits on screen and the log of the zoom instead, and recover the camera from that:

```js
const s = screenKeysAt(t);                                               // { x, y, zoom }: A's screen position, log-eased zoom
CAM = { x: A[0] + (960 - s.x) / s.zoom, y: A[1] + (540 - s.y) / s.zoom, zoom: s.zoom, rot };
```

A dive eases log zoom on `cubicInOut` while the target's screen position moves linearly to the centre. Shakes divide x
and y by zoom, so they vanish at depth: add `OM.shake` to the screen position before recovering the camera. The
clearing film went 1× → 300× → 1× this way.

**Nested levels draw in their own units.** A day is a 1440 px page inside a 24 px cell: draw it under
`mul(VIEW, [s, 0, 0, s, ox, oy])` with type at normal sizes and it stays crisp at any zoom. Fade each level's detail in
by its parent's size on screen (`sstep(70, 260, 24 * zoom)`) and cull what is off frame, so the year never draws 364
pages.

**Canvas effects ignore the transform.** `shadowBlur`, `shadowOffsetX/Y` and `filter: blur()` are in device pixels.
Multiply them by DPR × zoom by hand, or shadows shrink as the camera pulls out (`cases/knockon-15s`, `lift`).

## Natural media — a brush

unbroken's ensō is procedural ink with no textures (`cases/unbroken-15s/`). A stroke is an arc sampled every ~4 px — position, radial normal, width,
dryness — drawn as 56 hair polylines spread across the width:

- **width** = a touch-down swell × a breathing body (`vnoise(d / 260)`) × a taper; a stroke cut short thins fast instead;
- **dryness** rises along the stroke. A hair skips where `0.72 · vnoise(i · 0.055) + 0.28 · vnoise(i · 0.45)` falls under
  `dry × (0.45 + 0.9·|o|^1.5 + 0.45·(1 − load))`, so edge hairs and thin-loaded hairs run out first and leave 飞白;
- **ends are round**: edge hairs touch down ~4 samples late and lift ~5 early (∝ o²);
- **drawn to k**: each hair to its own fraction with the head interpolated between samples, so the shutter smears it.

What didn't read: a few thick, even hairs (a plastic band); width swelling from zero at the touch-down (fans); strokes
under ~140 px (tufts).

## Things that bit

- A `filter: blur()` on an element translated tens of thousands of pixels off-screen painted the
  whole frame **black**. Anything that has left the frame gets `display:none`.
- Fonts: subset and inline (`subset_fonts.py` from motion-web); `file://` pages and remote fonts do not mix,
  and a font that loads late shifts every measured position.
- Measure text positions (`getBoundingClientRect`) **after** `document.fonts.ready`, in `__ready`.
- Word beats written as `opacity` fades read as PowerPoint; write them as springs with translateY and
  a little scale so they *land* (`OM.wordRise`).
- **A dark gradient bands after encoding.** unbroken's radial ground came out of 8-bit `yuv420p` in visible rings. Draw a
  fixed 256² noise pattern (alpha ≤ 7/255, half white, half black) over the ground in device pixels. It is fixed, so
  still frames stay still.
- **A slow push is not a rest.** At 320 px a 1 → 1.05 push over a grid is never dead still: clearing's first render
  failed the rest leg at 0.178 because every hold pushed. With the holds truly still it passed at 0.294.
- A `__seek` that throws at some t is easy to miss in a film. Pocket Weather v2 threw
  `EncodingError: The source image cannot be decoded` from 12.8 s on; probe.py and verify print `__seek threw at N samples`.
