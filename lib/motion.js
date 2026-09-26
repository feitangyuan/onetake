// onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
/* onetake · lib/motion.js — the genre's moves as pure functions of time.
 *
 * Numbers in, numbers out. Nothing here touches the DOM or a canvas, so one call drives
 * `el.style.transform` or `ctx.setTransform` alike. No state and no Math.random: the same arguments
 * always give the same answer, which is what `__seek(t)` needs. The four sims and the camera rig integrate, so
 * they run once at 240 Hz and are sampled by time.
 *
 * Every move comes from a film that was accepted — motion-web-15s (MW), pocket-weather-15s (PW), one-dot-15s (OD) —
 * and has a sheet in gallery/sheets/<name>.png. Catalogue, curve table, carry grammar:
 * references/motion-library.md.
 *
 * Classic script (file:// pages cannot import modules): <script src="motion.js"></script> → window.OM.
 * Node: const OM = require('./motion.js').
 *
 *   curves   ease.* · bezier · tween · t80 · spring · springVel · ring · settle · spline · rng
 *   enter    wordRise · letterDrop · popIn · liftOut · maskRise · typeOn · tick · flyThrough
 *   carry    morphRect · iris · zoomThrough · hop · gather · ribbon · seal · staccato
 *   contact  impact · impactSplit · press · cursor · squash · sim.{magnet, follow, jelly, verlet}
 *   camera   camera · view · dof · whip · shake · drift · lattice · project · unproject · projectBox · screenTravel
 *   fluid    swiftSpring · lightField · ripple · silk · carouselLoop
 */
(function (root) {
  'use strict';

  // ─────────────────────────────── scalars ───────────────────────────────
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, k) => a + (b - a) * k;
  const seg = (t, t0, t1) => (t1 === t0 ? (t >= t1 ? 1 : 0) : clamp((t - t0) / (t1 - t0), 0, 1));
  const sstep = (e0, e1, x) => { const k = clamp((x - e0) / (e1 - e0), 0, 1); return k * k * (3 - 2 * k); };
  const ssstep = (e0, e1, x) => { const k = clamp((x - e0) / (e1 - e0), 0, 1); return k * k * k * (k * (k * 6 - 15) + 10); };

  // ─────────────────────────────── curves ───────────────────────────────
  // t80 = share of the duration spent before 80 % of the distance is covered. Low = snaps then settles
  // (launch-clip feel); ~.7 = symmetric S-curve (soft, reads as a web transition when used for travel).
  const powOut = n => u => 1 - Math.pow(1 - u, n);
  const powInOut = n => u => (u < 0.5 ? Math.pow(2, n - 1) * Math.pow(u, n) : 1 - Math.pow(-2 * u + 2, n) / 2);
  const EXPO = 1 - Math.pow(2, -10);
  const ease = {
    linear: u => u,                                              // t80 .80
    smooth: u => u * u * (3 - 2 * u),                            // t80 .71 smoothstep
    smoother: u => u * u * u * (u * (u * 6 - 15) + 10),          // t80 .67 smootherstep — PW's travel curve
    sineInOut: u => -(Math.cos(Math.PI * u) - 1) / 2,
    cubicInOut: powInOut(3),                                     // camera legs that start and stop at rest
    quintInOut: powInOut(5),
    quadOut: powOut(2),                                          // t80 .55
    cubicOut: powOut(3),                                         // t80 .42
    quartOut: powOut(4),                                         // t80 .33
    quintOut: powOut(5),                                         // t80 .28
    expoOut: u => (u <= 0 ? 0 : u >= 1 ? 1 : (1 - Math.pow(2, -10 * u)) / EXPO),   // t80 .23
    expoIn: u => (u <= 0 ? 0 : u >= 1 ? 1 : (Math.pow(2, 10 * u) - 1) / 1023),
    expoInOut: u => (u < 0.5 ? ease.expoIn(2 * u) / 2 : 1 - ease.expoIn(2 - 2 * u) / 2),  // whips
    circOut: u => Math.sqrt(1 - Math.pow(1 - clamp(u), 2)),
    backOut: u => { const s = 1.70158; return 1 + (s + 1) * Math.pow(u - 1, 3) + s * Math.pow(u - 1, 2); },
    back: (s = 1.70158) => u => 1 + (s + 1) * Math.pow(u - 1, 3) + s * Math.pow(u - 1, 2),
  };

  // CSS cubic-bezier(x1, y1, x2, y2) as a function of u — for curves taken from a spec or a reference.
  function bezier(x1, y1, x2, y2) {
    const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx, cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
    const sx = s => ((ax * s + bx) * s + cx) * s, sy = s => ((ay * s + by) * s + cy) * s, dsx = s => (3 * ax * s + 2 * bx) * s + cx;
    const solve = x => {
      let s = x;
      for (let i = 0; i < 8; i++) {
        const e = sx(s) - x; if (Math.abs(e) < 1e-7) return s;
        const d = dsx(s); if (Math.abs(d) < 1e-6) break;
        s -= e / d; if (s < 0 || s > 1) break;
      }
      let lo = 0, hi = 1; s = x;
      for (let i = 0; i < 60; i++) { const v = sx(s); if (Math.abs(v - x) < 1e-7) return s; if (x > v) lo = s; else hi = s; s = (lo + hi) / 2; }
      return s;
    };
    return u => (u <= 0 ? 0 : u >= 1 ? 1 : sy(solve(u)));
  }

  const tween = (t, t0, t1, curve = ease.expoOut) => curve(seg(t, t0, t1));

  function t80(curve, frac = 0.8, steps = 4000) {
    for (let i = 0; i <= steps; i++) { const u = i / steps; if (curve(u) >= frac) return u; }
    return 1;
  }

  // Damped spring step response 0 → 1 from rest. zeta < 1 overshoots (.4 bouncy … .8 firm), 1 is critical.
  function spring(tau, zeta = 0.6, omega = 20) {
    if (tau <= 0) return 0;
    if (zeta < 1) { const wd = omega * Math.sqrt(1 - zeta * zeta); return 1 - Math.exp(-zeta * omega * tau) * (Math.cos(wd * tau) + (zeta * omega / wd) * Math.sin(wd * tau)); }
    if (zeta === 1) return 1 - Math.exp(-omega * tau) * (1 + omega * tau);
    const q = omega * Math.sqrt(zeta * zeta - 1), r1 = -zeta * omega + q, r2 = -zeta * omega - q;
    return 1 - (r2 * Math.exp(r1 * tau) - r1 * Math.exp(r2 * tau)) / (r2 - r1);
  }

  // d/dtau of spring(): progress per second. Use it for squash-from-velocity.
  function springVel(tau, zeta = 0.6, omega = 20) {
    if (tau <= 0) return 0;
    if (zeta < 1) { const s = Math.sqrt(1 - zeta * zeta); return (omega / s) * Math.exp(-zeta * omega * tau) * Math.sin(omega * s * tau); }
    if (zeta === 1) return omega * omega * tau * Math.exp(-omega * tau);
    const q = omega * Math.sqrt(zeta * zeta - 1), r1 = -zeta * omega + q, r2 = -zeta * omega - q;
    return omega * omega * (Math.exp(r1 * tau) - Math.exp(r2 * tau)) / (r1 - r2);
  }

  // Decaying oscillation around 0 — a click, a landing, a wobble that rings out.
  function ring(tau, decay = 9, omega = 26) { return tau <= 0 ? 0 : Math.exp(-decay * tau) * Math.sin(omega * tau); }

  // Seconds until spring() stays within eps of 1 — for planning how long a beat must hold.
  function settle(zeta = 0.6, omega = 20, eps = 0.02) {
    let last = 0;
    for (let i = 1; i <= 20000; i++) { const t = i / 1000; if (Math.abs(1 - spring(t, zeta, omega)) > eps) last = t; }
    return last;
  }

  // Hermite curve through {t, x, y} knots — the hand path.
  function spline(knots, t) {
    if (t <= knots[0].t) return [knots[0].x, knots[0].y];
    const L = knots.length; if (t >= knots[L - 1].t) return [knots[L - 1].x, knots[L - 1].y];
    let i = 0; while (knots[i + 1].t < t) i++;
    const k0 = knots[i], k1 = knots[i + 1], h = k1.t - k0.t, u = (t - k0.t) / h, km = knots[Math.max(0, i - 1)], kp = knots[Math.min(L - 1, i + 2)];
    const m0x = (k1.x - km.x) / (k1.t - km.t) * h, m0y = (k1.y - km.y) / (k1.t - km.t) * h, m1x = (kp.x - k0.x) / (kp.t - k0.t) * h, m1y = (kp.y - k0.y) / (kp.t - k0.t) * h;
    const h00 = 2 * u ** 3 - 3 * u ** 2 + 1, h10 = u ** 3 - 2 * u ** 2 + u, h01 = -2 * u ** 3 + 3 * u ** 2, h11 = u ** 3 - u ** 2;
    return [h00 * k0.x + h10 * m0x + h01 * k1.x + h11 * m1x, h00 * k0.y + h10 * m0y + h01 * k1.y + h11 * m1y];
  }

  // xorshift32 — for layout jitter decided once in setup, never on the render path.
  function rng(seed = 1) {
    let s = (seed >>> 0) || 1;
    return () => { s ^= s << 13; s ^= s >>> 17; s ^= s << 5; return (s >>> 0) / 4294967296; };
  }

  // ─────────────────────────────── enter ───────────────────────────────
  // MW · a word lands: spring rise + a little scale. Opacity leads the spring so it never reads as a fade.
  function wordRise(t, t0, { zeta = 0.6, omega = 22, dist = 26, s0 = 0.94, ds = 0.06, fade = 1.5 } = {}) {
    const k = spring(t - t0, zeta, omega);
    return { k, op: clamp(k * fade, 0, 1), y: (1 - k) * dist, s: s0 + ds * k };
  }

  // MW · wordmark letter i drops in; speed flattens it (sy) and widens it (sx), recovering as it settles.
  function letterDrop(t, t0, i, { stagger = 0.055, zeta = 0.5, omega = 26, dist = 46, squash = 0.0075, max = 0.22, widen = 0.6, fade = 1.6, h = 0.012 } = {}) {
    const tau = t - t0 - i * stagger;
    const k = spring(tau, zeta, omega), dk = (spring(tau, zeta, omega) - spring(tau - h, zeta, omega)) / h;
    const sq = clamp(Math.abs(dk) * squash, 0, max);
    return { k, sq, op: clamp(k * fade, 0, 1), y: (1 - k) * dist, sx: 1 + sq * widen, sy: 1 - sq };
  }

  // MW · card entrance: spring rise with scale.
  function popIn(t, t0, { zeta = 0.62, omega = 18, rise = 36, s0 = 0.94, ds = 0.06, fade = 1.5 } = {}) {
    const k = spring(t - t0, zeta, omega);
    return { k, op: clamp(k * fade, 0, 1), s: s0 + ds * k, dy: (1 - k) * rise };
  }

  // MW · card exit: lifts, grows a touch and blurs away over `dur`.
  function liftOut(t, t1, { dur = 0.22, dir = -1, dist = 90, blur = 10, grow = 0.03 } = {}) {
    const k = ssstep(t1, t1 + dur, t);
    return { k, op: 1 - k, dy: dir * k * dist, blur: k * blur, s: 1 + grow * k };
  }

  // PW · line i rises into place from behind a clip mask. y is a fraction of `dist` (pass the line height).
  function maskRise(t, t0, i = 0, { stagger = 0.13, zeta = 0.47, omega = 17, dist = 1 } = {}) {
    const k = spring(t - t0 - i * stagger, zeta, omega);
    return { k, y: (1 - k) * dist, visible: k > 0 };
  }

  // MW · typed prompt: characters at cps, caret solid while typing, blinking after.
  function typeOn(t, t0, text, { cps = 38, blink = 2.4 } = {}) {
    const n = clamp(Math.floor((t - t0) * cps), 0, text.length);
    return { n, str: text.slice(0, n), done: n >= text.length, caret: (n < text.length || Math.floor(t * blink) % 2 === 0) ? 1 : 0 };
  }

  // MW · checkbox tick at tl: pops from .8 with a spring.
  function tick(t, tl, { zeta = 0.5, omega = 28 } = {}) {
    const on = t >= tl, k = spring(t - tl, zeta, omega);
    return { on, k, s: on ? (0.8 + 0.2 * k + 0.25 * (1 - k)) : 1 };
  }

  // MW · a screen flies in tilted from the right, holds, flies out left. For CSS:
  // translate(x) perspective(2200px) rotateY(rotY) rotateX(rotX) scale(s), filter blur(blur).
  function flyThrough(t, t0, hold, { from = 1500, to = 0, exit = -1700, zeta = 0.78, omega = 14, out = 0.28,
    blurIn = 10, blurOut = 12, rotY0 = -18, rotY1 = -9, rotOut = 10, rotX = 4, s0 = 0.92, pre = 0.02, post = 0.35 } = {}) {
    const t1 = t0 + hold, visible = t >= t0 - pre && t < t1 + post;
    const kin = spring(t - t0, zeta, omega), kout = ssstep(t1, t1 + out, t), kc = Math.min(1, kin);
    return { visible, kin, kout, x: lerp(from, to, kin) + kout * exit, blur: Math.max((1 - kc) * blurIn, kout * blurOut),
      rotY: lerp(rotY0, rotY1, kc) + kout * rotOut, rotX, s: lerp(s0, 1, kc), op: 1 - kout };
  }

  // ─────────────────────────────── carry — the next shot grows out of this one ───────────────────────────────
  // PW · container transform: rect A (a card, a button) becomes rect B (the page). {x, y, w, h, r?}, x/y top-left.
  function morphRect(t, t0, t1, A, B, { curve = ease.expoOut, spring: sp = null } = {}) {
    const k = sp ? spring(t - t0, sp.zeta ?? 0.7, sp.omega ?? 16) : curve(seg(t, t0, t1));
    const x = lerp(A.x, B.x, k), y = lerp(A.y, B.y, k), w = lerp(A.w, B.w, k), h = lerp(A.h, B.h, k);
    return { k, x, y, w, h, r: lerp(A.r ?? 0, B.r ?? 0, k), cx: x + w / 2, cy: y + h / 2 };
  }

  // PW · a circular stage opens from the subject at (cx, cy) until it covers the whole frame.
  function iris(t, t0, t1, cx, cy, { W = 1920, H = 1080, curve = ease.expoOut, r0 = 0 } = {}) {
    const k = curve(seg(t, t0, t1));
    const far = Math.max(Math.hypot(cx, cy), Math.hypot(W - cx, cy), Math.hypot(cx, H - cy), Math.hypot(W - cx, H - cy)) + 2;
    return { k, cx, cy, r: lerp(r0, far, k), covered: k >= 1 };
  }

  // Camera pushes into `target` {x, y, w, h} until it fills the frame; its inside becomes the next scene.
  // screen = world·s + (tx, ty) → CSS matrix(...matrix) with transform-origin 0 0, or ctx.setTransform(...matrix).
  function zoomThrough(t, t0, t1, target, { W = 1920, H = 1080, curve = ease.expoInOut, fit = 'cover' } = {}) {
    const k = curve(seg(t, t0, t1));
    const sEnd = fit === 'contain' ? Math.min(W / target.w, H / target.h) : Math.max(W / target.w, H / target.h);
    const s = Math.exp(Math.log(sEnd) * k);                       // log space: the zoom reads as one speed
    const tcx = target.x + target.w / 2, tcy = target.y + target.h / 2;
    const px = lerp(tcx, W / 2, k), py = lerp(tcy, H / 2, k);      // the target's centre travels to the frame centre
    const tx = px - s * tcx, ty = py - s * tcy;
    return { k, s, tx, ty, matrix: [s, 0, 0, s, tx, ty] };
  }

  // PW · the subject hops between slots on an arc.
  function hop(t, t0, t1, from, to, { height = 200, curve = ease.smoother } = {}) {
    const k = curve(seg(t, t0, t1));
    return { k, x: lerp(from.x, to.x, k), y: lerp(from.y, to.y, k) - Math.sin(k * Math.PI) * height };
  }

  // PW · item i of n travels on an arc to its new place, fanning by index; stagger per item.
  function gather(t, t0, t1, i, n, from, to, { stagger = 0.08, arc = 120, spin = 0.4, curve = ease.smoother } = {}) {
    const k = curve(seg(t, t0 + i * stagger, t1 + i * stagger)), o = i - (n - 1) / 2, bump = Math.sin(k * Math.PI);
    return { k, x: lerp(from.x, to.x, k), y: lerp(from.y, to.y, k) - bump * arc, rot: bump * o * spin };
  }

  // PW · an elastic rail of panels. Each switch time advances `shift` by one with a ring-out; text lags behind.
  // Panel j sits at x = centre + (j − shift)·width + wobble.
  function ribbon(t, switches, { dur = 0.35, amp = 55, decay = 7, omega = 22, tilt = 0.08, stretchX = 0.24, stretchY = 0.15, lag = 1.8, curve = ease.smoother } = {}) {
    let shift = 0, r = 0;
    for (const ts of switches) { shift += curve(seg(t, ts, ts + dur)); r += ring(t - ts, decay, omega); }
    const stretch = Math.abs(r);
    return { shift, index: Math.round(shift), wobble: r * amp, rot: r * tilt, sx: 1 + stretch * stretchX, sy: 1 - stretch * stretchY, textDx: -r * amp * lag };
  }

  // PW · the cast folds into a brand seal: a disc grows and turns.
  function seal(t, t0, t1, { r = 235, turns = 1, curve = ease.smoother } = {}) {
    const k = curve(seg(t, t0, t1));
    return { k, r: r * k, rot: k * turns * Math.PI * 2 };
  }

  // MW · staccato hits: the word whose time has come. list = [[t, word], …]. Hard cuts, in a burst.
  function staccato(t, list) {
    let word = '', i = -1;
    for (let j = 0; j < list.length; j++) if (t >= list[j][0]) { word = list[j][1]; i = j; }
    return { word, i };
  }

  // ─────────────────────────────── contact — one thing causes another ───────────────────────────────
  // PW · the ring of a landing. sx/sy squash the lander; feed r into whatever it lands on.
  function impact(t, tHit, { decay = 7, omega = 22, sqx = 0.13, sqy = 0.16 } = {}) {
    const r = ring(t - tHit, decay, omega);
    return { r, sx: 1 + r * sqx, sy: 1 - r * sqy };
  }

  // PW · a landing at cx splits the headline: the glyph at x is pushed apart, bounces by its distance, rejoins.
  function impactSplit(t, tHit, x, cx, { width = 600, spread = 65, bounce = 65, rot = 0.18, falloff = 3,
    open = [-0.01, 0.48], close = [0.63, 0.98], decay = 7, omega = 22, curve = ease.smoother } = {}) {
    const d = (x - cx) / width, r = ring(t - tHit, decay, omega);
    const apart = curve(seg(t, tHit + open[0], tHit + open[1])) * (1 - curve(seg(t, tHit + close[0], tHit + close[1])));
    return { dx: Math.sign(d) * apart * spread, dy: r * bounce * Math.exp(-d * d * falloff), rot: r * d * rot };
  }

  // MW · a button pressed at tc: rings in scale, `active` for the colour flash.
  function press(t, tc, { depth = 0.16, decay = 10, omega = 30, flash = 0.4 } = {}) {
    const cl = t - tc, sq = cl > 0 ? ring(cl, decay, omega) * depth : 0;
    return { s: 1 + sq, sq, down: cl > 0, active: cl > 0 && cl < flash };
  }

  // MW · the hand: spline through knots, dips to `down` for `hold` s at each click.
  function cursor(t, knots, clicks = [], { down = 0.84, hold = 0.14 } = {}) {
    const p = spline(knots, t); let s = 1;
    for (const c of clicks) { const d = t - c; if (d >= 0 && d < hold) s = down; }
    return { x: p[0], y: p[1], s };
  }

  // MW · stretch along the direction of travel, thin across it (velocity in px/s).
  function squash(vx, vy, { k = 0.0012, max = 0.45, kY = 0.0008, maxY = 0.3 } = {}) {
    const sp = Math.hypot(vx, vy);
    return { speed: sp, ang: Math.atan2(vy, vx), sx: 1 + clamp(sp * k, 0, max), sy: 1 - clamp(sp * kY, 0, maxY) };
  }

  // MW · live mechanisms inside a card, driven by the hand. card = {t, out, x, y} (top-left, 460×270 space);
  // the sim runs t … out + 0.3 once and `at(t)` samples it. Drawing stays in the composition.
  const SDT = 1 / 240;
  const sampler = (st, t0, per) => t => st[clamp(Math.floor((t - t0) / per), 0, st.length - 1)];
  const sim = {
    SDT,
    magnet(card, hand, { B = { x: 230, y: 158 }, R = 150, pull = 0.36, K = 120, damp = 0.85 } = {}) {
      const D = Math.pow(damp, SDT * 60); let x = 0, y = 0, vx = 0, vy = 0; const st = [];
      for (let t = card.t; t <= card.out + 0.3; t += SDT) {
        const h = hand(t); const dx = h[0] - (card.x + B.x), dy = h[1] - (card.y + B.y), d = Math.hypot(dx, dy); let tx = 0, ty = 0;
        if (d < R) { const f = pull * (1 - (d / R) ** 2); tx = dx * f; ty = dy * f; }
        vx += (tx - x) * K * SDT; vy += (ty - y) * K * SDT; vx *= D; vy *= D; x += vx * SDT; y += vy * SDT; st.push([x, y]);
      }
      return { st, per: SDT, B, at: sampler(st, card.t, SDT) };
    },
    follow(card, hand, { K = 70, damp = 0.88, home = [230, 140], box = [30, 430, 50, 240], reach = [40, 500, 40, 310] } = {}) {
      const D = Math.pow(damp, SDT * 60); let x = home[0], y = home[1], vx = 0, vy = 0; const st = [];
      for (let t = card.t; t <= card.out + 0.3; t += SDT) {
        const h = hand(t); let tx = clamp(h[0] - card.x, box[0], box[1]), ty = clamp(h[1] - card.y, box[2], box[3]);
        const inside = h[0] > card.x - reach[0] && h[0] < card.x + reach[1] && h[1] > card.y - reach[2] && h[1] < card.y + reach[3];
        if (!inside) { tx = home[0]; ty = home[1]; }
        vx += (tx - x) * K * SDT; vy += (ty - y) * K * SDT; vx *= D; vy *= D; x += vx * SDT; y += vy * SDT; st.push([x, y, vx, vy]);
      }
      return { st, per: SDT, at: sampler(st, card.t, SDT) };
    },
    // ring of radial springs with neighbour coupling, dented where the hand touches the surface
    jelly(card, hand, { N = 48, C = { x: 230, y: 150 }, R0 = 78, K = 42, CP = 1800, damp = 0.962, reach = 60, dent = 14 } = {}) {
      const D = Math.pow(damp, SDT * 60); const r = new Float32Array(N), v = new Float32Array(N); const st = []; let step = 0;
      for (let t = card.t; t <= card.out + 0.3; t += SDT, step++) {
        const h = hand(t); const hx = h[0] - (card.x + C.x), hy = h[1] - (card.y + C.y);
        for (let i = 0; i < N; i++) {
          const th = i / N * Math.PI * 2; const px = Math.cos(th) * R0 * (1 + r[i]), py = Math.sin(th) * R0 * (1 + r[i]); const d = Math.hypot(hx - px, hy - py);
          let push = 0; if (d < reach) { push = -(1 - d / reach) * dent; }
          const lap = r[(i + N - 1) % N] + r[(i + 1) % N] - 2 * r[i]; v[i] += (-r[i] * K + lap * CP + push) * SDT; v[i] *= D;
        }
        for (let i = 0; i < N; i++) r[i] += v[i] * SDT;
        if (step % 4 === 0) st.push(Float32Array.from(r));
      }
      return { st, per: SDT * 4, N, C, R0, at: sampler(st, card.t, SDT * 4) };
    },
    // N nodes hanging from (ax, ay), pushed aside by the hand; samples are [x0, y0, x1, y1, …]
    verlet(card, hand, { N = 16, L = 13, ax = 230, ay = 40, damp = 0.985, gravity = 1400, reach = 34, push = 2.2, iters = 3 } = {}) {
      const px = new Float32Array(N), py = new Float32Array(N), ox = new Float32Array(N), oy = new Float32Array(N);
      for (let i = 0; i < N; i++) { px[i] = ox[i] = ax; py[i] = oy[i] = ay + i * L; }
      const st = []; let step = 0;
      for (let t = card.t; t <= card.out + 0.3; t += SDT, step++) {
        const h = hand(t); const hx = h[0] - card.x, hy = h[1] - card.y;
        for (let i = 1; i < N; i++) {
          let vx = (px[i] - ox[i]) * damp, vy = (py[i] - oy[i]) * damp; ox[i] = px[i]; oy[i] = py[i]; px[i] += vx; py[i] += vy + gravity * SDT * SDT;
          const dx = px[i] - hx, dy = py[i] - hy, d = Math.hypot(dx, dy); if (d < reach && d > 0.01) { const f = (reach - d) / reach * push; px[i] += dx / d * f; py[i] += dy / d * f; }
        }
        for (let it = 0; it < iters; it++) {
          px[0] = ax; py[0] = ay;
          for (let i = 0; i < N - 1; i++) {
            const dx = px[i + 1] - px[i], dy = py[i + 1] - py[i], d = Math.hypot(dx, dy) || 1e-6, c = (d - L) / d * 0.5;
            if (i === 0) { px[1] -= dx * c * 2; py[1] -= dy * c * 2; } else { px[i] += dx * c; py[i] += dy * c; px[i + 1] -= dx * c; py[i + 1] -= dy * c; }
          }
        }
        if (step % 4 === 0) { const s = new Float32Array(N * 2); for (let i = 0; i < N; i++) { s[i * 2] = px[i]; s[i * 2 + 1] = py[i]; } st.push(s); }
      }
      return { st, per: SDT * 4, N, at: sampler(st, card.t, SDT * 4) };
    },
  };

  // ─────────────────────────────── camera ───────────────────────────────
  // Keys {t, x, y, zoom?, rot?, curve?}; (x, y) is the world point at the frame centre. Zoom interpolates in log space.
  function camera(t, keys, { curve = ease.cubicInOut, W = 1920, H = 1080 } = {}) {
    const pick = k => ({ x: k.x ?? W / 2, y: k.y ?? H / 2, zoom: k.zoom ?? 1, rot: k.rot ?? 0 });
    if (!keys.length) return { x: W / 2, y: H / 2, zoom: 1, rot: 0 };
    if (t <= keys[0].t) return pick(keys[0]);
    const L = keys.length; if (t >= keys[L - 1].t) return pick(keys[L - 1]);
    let i = 0; while (keys[i + 1].t < t) i++;
    const A = pick(keys[i]), B = pick(keys[i + 1]), k = (keys[i + 1].curve || curve)(seg(t, keys[i].t, keys[i + 1].t));
    return { x: lerp(A.x, B.x, k), y: lerp(A.y, B.y, k), zoom: Math.exp(lerp(Math.log(A.zoom), Math.log(B.zoom), k)), rot: lerp(A.rot, B.rot, k) };
  }

  // Affine matrix [a, b, c, d, e, f] for a layer at `depth` seen through `cam`: CSS matrix(...) / ctx.setTransform(...).
  // depth 0 = focus plane; > 0 farther (moves and zooms less); < 0 nearer (moves more).
  function view(cam, { W = 1920, H = 1080, depth = 0 } = {}) {
    const f = 1 / (1 + Math.max(-0.9, depth));
    const cx = W / 2 + (cam.x - W / 2) * f, cy = H / 2 + (cam.y - H / 2) * f;
    const z = Math.exp(Math.log(cam.zoom) * f), c = Math.cos(cam.rot * f) * z, s = Math.sin(cam.rot * f) * z;
    return [c, s, -s, c, W / 2 - (c * cx - s * cy), H / 2 - (s * cx + c * cy)];
  }

  // Depth-of-field blur in px for a layer at `depth` when the camera focuses at `focus`.
  const dof = (depth, focus = 0, { k = 10, max = 14 } = {}) => Math.min(max, Math.abs(depth - focus) * k);

  // A whip: all of `dist` in `dur` on an expo in-out. Only reads with shutter blur (render.py --shutter).
  function whip(t, t0, dur, dist, { curve = ease.expoInOut } = {}) {
    const k = curve(seg(t, t0, t0 + dur));
    return { k, d: dist * k };
  }

  // Camera shake after a hit: decaying, deterministic, starts from zero.
  function shake(t, tHit, { amp = 12, decay = 9, freq = 19, seed = 1 } = {}) {
    const tau = t - tHit; if (tau <= 0) return { x: 0, y: 0, rot: 0 };
    const r = rng(seed), fx = freq * (1 + 0.1 * r()), fy = freq * (1.31 + 0.1 * r()), fr = freq * (0.77 + 0.1 * r());
    const e = amp * Math.exp(-decay * tau), w = 2 * Math.PI * tau;
    return { x: e * Math.sin(w * fx), y: 0.7 * e * Math.sin(w * fy), rot: 0.0015 * e * Math.sin(w * fr) };
  }

  // MW · slow push during a hold: scale 1 → 1 + amount across t0 … t1.
  const drift = (t, t0, t1, amount = 0.07) => 1 + amount * seg(t, t0, t1);

  // Through a view() matrix M: world → screen, screen → world, and a world box's bounds on screen.
  const project = (M, x, y) => [M[0] * x + M[2] * y + M[4], M[1] * x + M[3] * y + M[5]];
  const unproject = (M, x, y) => { const d = M[0] * M[3] - M[1] * M[2], u = x - M[4], v = y - M[5]; return [(M[3] * u - M[2] * v) / d, (M[0] * v - M[1] * u) / d]; };
  function projectBox(M, b) {
    const P = [[b.x, b.y], [b.x + b.w, b.y], [b.x, b.y + b.h], [b.x + b.w, b.y + b.h]].map(p => project(M, p[0], p[1]));
    const xs = P.map(p => p[0]), ys = P.map(p => p[1]), x0 = Math.min(...xs), y0 = Math.min(...ys);
    return { x: x0, y: y0, w: Math.max(...xs) - x0, h: Math.max(...ys) - y0, op: b.op };
  }

  // How far the frame's corners move on screen between cameras c0 and c1 (following the world points under them at
  // cMid): the camera's share of a page's window.__motion, from which render.py sizes each frame's shutter.
  function screenTravel(c0, c1, cMid, { W = 1920, H = 1080, depth = 0 } = {}) {
    const M0 = view(c0, { W, H, depth }), M1 = view(c1, { W, H, depth }), Mm = view(cMid, { W, H, depth });
    let d = 0;
    for (const [sx, sy] of [[0, 0], [W, 0], [0, H], [W, H]]) {
      const [wx, wy] = unproject(Mm, sx, sy), p = project(M0, wx, wy), r = project(M1, wx, wy);
      d = Math.max(d, Math.hypot(p[0] - r[0], p[1] - r[1]));
    }
    return d;
  }

  // OD · an operator, not keyframes. want(t) → {x, y, zoom, w}: what to frame, how tight, how fast to chase (rad/s).
  // A spring per axis chases it — position ζ .8; zoom in log space, ζ .95 at .8 w — integrated once at `hz` and
  // sampled, so moves lag, lean and settle while every frame stays a function of t. hits [[t, px, decay], …] shake.
  // Output is quantised below what shows (1/16 px, 0.05 % zoom): a settled camera repeats its frame exactly and
  // render.py skips the shutter. A snap faster than the spring outruns it: want the landing point ~0.15 s before
  // the snap rather than chasing it (the one-dot film's first camera render lost its dot that way).
 
  // OD · a far grid seen through `cam`: under ctx.setTransform(...matrix), a dot of radius r at every lattice point from
  // (x0, y0) to (x1, y1) in steps of `spacing` — dots stay `px` on screen whatever the zoom. On an empty ground a
  // camera move doesn't read without something farther back to slide against (one-dot: 48, depth 1.2, 1.4 px).
  function lattice(cam, { depth = 1.2, spacing = 48, px = 1.4, W = 1920, H = 1080 } = {}) {
    const M = view(cam, { W, H, depth }), c = [[0, 0], [W, 0], [0, H], [W, H]].map(p => unproject(M, p[0], p[1]));
    const xs = c.map(p => p[0]), ys = c.map(p => p[1]);
    return { matrix: M, spacing, r: px / Math.hypot(M[0], M[1]),
      x0: Math.floor(Math.min(...xs) / spacing) * spacing, x1: Math.max(...xs), y0: Math.floor(Math.min(...ys) / spacing) * spacing, y1: Math.max(...ys) };
  }

  // ─────────────────────────────── fluid (FL · ebb) ───────────────────────────────
  // SwiftUI's named springs: Spring(duration d, bounce b) is ζ = 1 − b, ω = 2π / d. .smooth b 0, .snappy .15, .bouncy .3.
  const SWIFT = { smooth: 0, snappy: 0.15, bouncy: 0.3 };
  function swiftSpring(tau, kind = 'smooth', { duration = 0.5, bounce = null } = {}) {
    const b = bounce ?? SWIFT[kind] ?? 0;
    return spring(tau, 1 - b, 2 * Math.PI / duration);
  }

  // A persistent ground of light: level 0 = at rest (a low glow, horizon ≈ rest·H), 1 = the frame flooded. Returns the
  // ellipse (anchored below the frame) to fill with a radial gradient — `stops` are the reference's, warm or green — and
  // `core`, the half-radius contour where the light is bright enough to turn type white. Flood ≤ 0.4 s, drain ~1 s.
  function lightField(level, { W = 1920, H = 1080, rest = 0.84, top = -300, r0 = 660, r1 = 1500, tilt = 0.012 } = {}) {
    const ry = r0 + r1 * level, horizon = lerp(H * rest, top, level);
    return { cx: W / 2, cy: horizon + 0.62 * ry, rx: ry * 2.3, ry, tilt, horizon, core: 0.5, stops: [0, 0.36, 0.6, 0.8, 1] };
  }

  // A flood that drains as concentric rings: n radii leaving a point, `stagger` apart, each crossing the frame in `dur`.
  // Fill the flood outside ring 0, alternate two tints between the rings, and the world shows through the innermost.
  function ripple(t, t0, { n = 3, stagger = 0.16, dur = 1.25, rMax = 1160, curve = ease.smoother } = {}) {
    const r = []; for (let k = 0; k < n; k++) r.push(rMax * curve(seg(t, t0 + k * stagger, t0 + k * stagger + dur)));
    return { r, done: t >= t0 + (n - 1) * stagger + dur };
  }

  // silk — the "native MeshGradient" look: domain-warped value noise, two octaves, on a tiny grid, contrast-stretched and
  // ramped. Returns RGBA for gx × gy; putImageData it into a gx × gy canvas and draw that up to the card with blur(28 px at
  // 520 wide). A ramp whose lightness is not monotonic (a dark fold between two brights) is what reads as cloth.
  function silkHash(x, y, s) { let h = (x * 374761393 + y * 668265263 + s * 1442695041) | 0; h = Math.imul(h ^ (h >>> 13), 1274126177); return ((h ^ (h >>> 16)) >>> 0) / 4294967296; }
  function silkNoise(x, y, s) {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi, u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    const a = silkHash(xi, yi, s), b = silkHash(xi + 1, yi, s), c = silkHash(xi, yi + 1, s), d = silkHash(xi + 1, yi + 1, s);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  }
  const silkFbm = (x, y, s) => 0.5 * silkNoise(x, y, s) + 0.25 * silkNoise(x * 2.02, y * 2.02, s);
  function silkRamp(stops, k) {
    k = clamp(k, 0, 1);
    for (let i = 1; i < stops.length; i++) if (k <= stops[i][0]) { const [a, A] = stops[i - 1], [b, B] = stops[i], u = (k - a) / (b - a); return A.map((v, j) => v + (B[j] - v) * u); }
    return stops[stops.length - 1][1];
  }
  const SILK = {
    ember: [[0, [200, 120, 24]], [0.22, [236, 170, 34]], [0.42, [122, 96, 26]], [0.54, [160, 94, 32]], [0.74, [240, 74, 92]], [1, [252, 210, 198]]],
    peach: [[0, [240, 150, 92]], [0.24, [252, 204, 148]], [0.44, [190, 104, 66]], [0.58, [236, 124, 108]], [0.8, [250, 186, 172]], [1, [255, 240, 228]]],
    dusk: [[0, [118, 58, 94]], [0.24, [226, 98, 112]], [0.44, [88, 44, 68]], [0.58, [176, 74, 98]], [0.8, [246, 150, 122]], [1, [255, 224, 204]]],
  };
  function silk(tau, seed = 3, stops = SILK.peach, { gx = 16, gy = 20, contrast = 3.4, out = null } = {}) {
    const d = out || new Uint8ClampedArray(gx * gy * 4);
    for (let j = 0; j < gy; j++) for (let i = 0; i < gx; i++) {
      const u = i / gx * 1.1, v = j / gy * 1.4;
      const qx = silkFbm(u + 0.11 * tau, v - 0.07 * tau, seed), qy = silkFbm(u + 5.2 - 0.09 * tau, v + 1.3 + 0.05 * tau, seed);
      const k = 0.5 + (silkFbm(u + 1.8 * qx + 0.04 * tau, v + 1.8 * qy, seed) - 0.375) * contrast;
      const c = silkRamp(stops, k), n = (i + j * gx) * 4;
      d[n] = c[0]; d[n + 1] = c[1]; d[n + 2] = c[2]; d[n + 3] = 255;
    }
    return d;
  }
  silk.ramps = SILK; silk.ramp = silkRamp;

  // A belt that never rests until it is told to: position and a slowed clock, integrated once so the start (a .smooth
  // swiftSpring over `rampDur`) and the stop (a smoothstep over `stop`) stay pure functions of t. at(t) → {x, tau}: x in
  // px travelled at `speed` px/s, tau the clock to drive every card's own loop (silk, typing) so they slow with the belt.
  function carouselLoop({ dur, start = 0, speed = 204, rampDur = 1.0, stop = null, hz = 240 } = {}) {
    const n = Math.ceil(dur * hz) + 1, X = new Float64Array(n), TA = new Float64Array(n);
    let x = 0, tau = 0;
    for (let i = 0; i < n; i++) {
      const t = i / hz, k = stop ? 1 - ease.smooth(seg(t, stop[0], stop[1])) : 1;
      x += speed * swiftSpring(t - start, 'smooth', { duration: rampDur }) * k / hz; tau += k / hz; X[i] = x; TA[i] = tau;
    }
    return { at(t) { const f = clamp(t * hz, 0, n - 1), i = Math.floor(f), j = Math.min(n - 1, i + 1), u = f - i; return { x: lerp(X[i], X[j], u), tau: lerp(TA[i], TA[j], u) }; } };
  }

  const OM = {
    version: '1.1.0-lite', lineage: 'otk-7f3e1c',
    clamp, lerp, seg, sstep, ssstep, ease, bezier, tween, t80, spring, springVel, ring, settle, spline, rng,
    wordRise, letterDrop, popIn, liftOut, maskRise, typeOn, tick, flyThrough,
    morphRect, iris, zoomThrough, hop, gather, ribbon, seal, staccato,
    impact, impactSplit, press, cursor, squash, sim,
    camera, view, dof, whip, shake, drift, lattice, project, unproject, projectBox, screenTravel,
    swiftSpring, lightField, ripple, silk, carouselLoop,
  };
  root.OM = OM;
  if (typeof module === 'object' && module.exports) module.exports = OM;
})(typeof window !== 'undefined' ? window : globalThis);
