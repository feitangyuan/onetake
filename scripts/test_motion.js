#!/usr/bin/env node
// onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
// test_motion.js — the library's math, checked before any film leans on it.
//
//   node scripts/test_motion.js
//
// Endpoints and the t80 table the docs quote, the bezier solver against brute force, springs against their
// own derivative and across zeta = 1, bit-identity with the template's original spr(), the carry geometry
// (iris covers, zoomThrough fills, view() centres and parallaxes), sim determinism, project ∘ unproject, finite outputs everywhere.
'use strict';
const path = require('path');
const OM = require(path.join(__dirname, '..', 'lib', 'motion.js'));

let fails = 0;
const ok = (name, cond, detail = '') => { console.log(`  ${cond ? 'PASS' : 'FAIL'}  ${name}${detail ? '  ' + detail : ''}`); if (!cond) fails++; };
const near = (a, b, e = 1e-6) => Math.abs(a - b) <= e;
const finite = o => Object.values(o).every(v => typeof v !== 'number' || Number.isFinite(v));

// 1 · curves
const curves = Object.entries(OM.ease).filter(([, f]) => typeof f(0.5) === 'number');
const badEnds = curves.filter(([, f]) => !(near(f(0), 0, 1e-9) && near(f(1), 1, 1e-9))).map(([n]) => n);
ok('every ease maps 0 → 0 and 1 → 1', badEnds.length === 0, badEnds.join(', '));
const T80 = { linear: 0.8, smooth: 0.713, smoother: 0.674, quadOut: 0.553, cubicOut: 0.415, quartOut: 0.331, quintOut: 0.275, expoOut: 0.232 };
for (const [n, v] of Object.entries(T80)) { const got = OM.t80(OM.ease[n]); ok(`t80 ${n} = ${v}`, near(got, v, 0.002), got.toFixed(3)); }

const brute = (x1, y1, x2, y2, x) => {
  let best = 0, bd = 1e9;
  for (let i = 0; i <= 200000; i++) { const s = i / 200000, bx = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s * s * x2 + s ** 3, d = Math.abs(bx - x); if (d < bd) { bd = d; best = s; } }
  return 3 * (1 - best) ** 2 * best * y1 + 3 * (1 - best) * best * best * y2 + best ** 3;
};
let worst = 0;
for (const b of [[0.25, 0.1, 0.25, 1], [0.16, 1, 0.3, 1], [0.7, 0, 0.84, 0], [0.34, 1.56, 0.64, 1]]) {
  const f = OM.bezier(...b);
  for (const x of [0.05, 0.2, 0.5, 0.8, 0.95]) worst = Math.max(worst, Math.abs(f(x) - brute(...b, x)));
}
ok('bezier solver matches brute force', worst < 2e-4, `max err ${worst.toExponential(1)}`);

// 2 · springs
for (const z of [0.3, 0.6, 0.95, 1, 1.4]) {
  ok(`spring settles to 1 (zeta ${z})`, near(OM.spring(8, z, 20), 1, 1e-4));
  const h = 1e-5; let e = 0;
  for (const t of [0.02, 0.1, 0.3, 0.7]) e = Math.max(e, Math.abs((OM.spring(t + h, z, 20) - OM.spring(t - h, z, 20)) / (2 * h) - OM.springVel(t, z, 20)));
  ok(`springVel is the derivative of spring (zeta ${z})`, e < 1e-3, `max err ${e.toExponential(1)}`);
}
ok('spring is continuous across zeta = 1', [0.05, 0.2, 0.5].every(t => near(OM.spring(t, 0.9999, 20), OM.spring(t, 1, 20), 1e-3) && near(OM.spring(t, 1.0001, 20), OM.spring(t, 1, 20), 1e-3)));
const spr = (tau, z = 0.6, w = 20) => { if (tau <= 0) return 0; const wd = w * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w * tau) * (Math.cos(wd * tau) + (z * w / wd) * Math.sin(wd * tau)); };
const ts = []; for (let t = -0.1; t < 3; t += 0.0137) ts.push(t);
ok('spring() is bit-identical to the template spr()', ts.every(t => OM.spring(t, 0.6, 22) === spr(t, 0.6, 22) && OM.spring(t, 0.78, 14) === spr(t, 0.78, 14)));
const st = OM.settle(0.6, 22); ok('settle() gives a usable hold length', st > 0.1 && st < 1, `${st.toFixed(3)} s for zeta .6 omega 22`);

// 3 · carry geometry
const ir = OM.iris(1, 0, 1, 300, 200);
ok('iris covers the farthest corner at k = 1', ir.r >= Math.hypot(1920 - 300, 1080 - 200));
const tg = { x: 600, y: 400, w: 320, h: 180 }, zt = OM.zoomThrough(1, 0, 1, tg), mp = (x, y) => [x * zt.s + zt.tx, y * zt.s + zt.ty];
const [ax, ay] = mp(tg.x, tg.y), [bx, by] = mp(tg.x + tg.w, tg.y + tg.h);
ok('zoomThrough fills the frame with the target at k = 1', near(ax, 0) && near(ay, 0) && near(bx, 1920) && near(by, 1080));
const z0 = OM.zoomThrough(0, 0, 1, tg); ok('zoomThrough starts at identity', near(z0.s, 1) && near(z0.tx, 0) && near(z0.ty, 0));
const apply = (m, x, y) => [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]];
ok('view() is identity for a centred camera', OM.view({ x: 960, y: 540, zoom: 1, rot: 0 }).every((v, i) => near(v, [1, 0, 0, 1, 0, 0][i])));
const c2 = apply(OM.view({ x: 1060, y: 540, zoom: 2, rot: 0.3 }), 1060, 540);
ok('view() puts the camera point at the frame centre', near(c2[0], 960) && near(c2[1], 540));
ok('view() parallax: a layer at depth 1 moves half as far', near(apply(OM.view({ x: 1060, y: 540, zoom: 1, rot: 0 }, { depth: 1 }), 960, 540)[0], 910));
const lat = OM.lattice({ x: 960, y: 540, zoom: 2, rot: 0 }, { depth: 0, spacing: 48, px: 1.4 });
ok('lattice() dots stay px on screen', near(lat.r * 2, 1.4));
ok('lattice() covers the frame', lat.x0 <= 480 && lat.x1 >= 1440 && lat.y0 <= 270 && lat.y1 >= 810);
const Mv = OM.view({ x: 1060, y: 500, zoom: 1.7, rot: 0.2 }), pr = OM.project(Mv, 321, 654), un = OM.unproject(Mv, pr[0], pr[1]);
ok('unproject() inverts project()', near(un[0], 321, 1e-9) && near(un[1], 654, 1e-9));
const still = { x: 960, y: 540, zoom: 1.4, rot: 0 };
ok('screenTravel() is 0 for a still camera', OM.screenTravel(still, still, still) === 0);
ok('screenTravel() of a 10 px pan at zoom 2 is 20 px', near(OM.screenTravel({ x: 960, y: 540, zoom: 2, rot: 0 }, { x: 970, y: 540, zoom: 2, rot: 0 }, { x: 965, y: 540, zoom: 2, rot: 0 }), 20, 1e-9));
const g1 = OM.gather(2, 0, 1, 0, 3, { x: 0, y: 0 }, { x: 100, y: 50 });
ok('gather lands on its target', near(g1.x, 100) && near(g1.y, 50) && near(g1.rot, 0));
const rb = OM.ribbon(5, [1, 2]); ok('ribbon settles on the last panel', near(rb.shift, 2) && rb.index === 2 && Math.abs(rb.wobble) < 1e-6);
const sp0 = OM.impactSplit(3, 0.87, 400, 960); ok('impactSplit rejoins after the hit', near(sp0.dx, 0) && Math.abs(sp0.dy) < 1e-3);
const ty = OM.typeOn(1, 0, 'hello', { cps: 3 }); ok('typeOn types at cps', ty.n === 3 && ty.str === 'hel' && ty.caret === 1);
ok('drift pushes by amount across the hold', near(OM.drift(5, 1, 2), 1.07) && near(OM.drift(1.5, 1, 2), 1.035));

// 4 · sims
const hand = t => [960 + 230 * Math.sin(t * 3), 540 + 90 * Math.cos(t * 2)], card = { t: 0, out: 1.2, x: 760, y: 420 };
for (const k of ['magnet', 'follow', 'jelly', 'verlet']) {
  const a = OM.sim[k](card, hand), b = OM.sim[k](card, hand), sa = Array.from(a.at(0.73)), sb = Array.from(b.at(0.73));
  ok(`sim.${k} is deterministic and finite`, JSON.stringify(sa) === JSON.stringify(sb) && sa.every(Number.isFinite));
}

// 5 · every move, everywhere
const calls = t => [OM.wordRise(t, 0.2), OM.letterDrop(t, 0.2, 3), OM.popIn(t, 0.2), OM.liftOut(t, 1), OM.maskRise(t, 0.2, 1), OM.tick(t, 0.5), OM.flyThrough(t, 0.2, 0.9),
  OM.morphRect(t, 0.2, 0.8, { x: 0, y: 0, w: 10, h: 10 }, { x: 5, y: 5, w: 100, h: 50, r: 8 }), OM.morphRect(t, 0.2, 0.8, { x: 0, y: 0, w: 10, h: 10 }, { x: 5, y: 5, w: 100, h: 50 }, { spring: { zeta: 0.6 } }),
  OM.iris(t, 0.2, 0.8, 900, 500), OM.zoomThrough(t, 0.2, 1, { x: 100, y: 100, w: 200, h: 120 }), OM.hop(t, 0, 1, { x: 0, y: 0 }, { x: 1, y: 1 }),
  OM.gather(t, 0, 1, 2, 3, { x: 0, y: 0 }, { x: 1, y: 1 }), OM.ribbon(t, [0.3, 0.9]), OM.seal(t, 0, 1), OM.impact(t, 0.3), OM.impactSplit(t, 0.3, 700, 960),
  OM.press(t, 0.4), OM.squash(300 * t, -200), OM.camera(t, [{ t: 0, x: 960, y: 540 }, { t: 1, x: 1200, y: 600, zoom: 1.6, rot: 0.1 }]),
  OM.whip(t, 0.2, 0.3, 1800), OM.shake(t, 0.5), { d: OM.dof(t, 0.5), p: OM.drift(t, 0, 1) },
  OM.lattice({ x: 960 + 100 * t, y: 540, zoom: 1.5 + 0.2 * Math.sin(t), rot: 0.1 * t })];
let bad = 0; for (let t = -1; t <= 4; t += 0.01) for (const o of calls(t)) if (!finite(o)) bad++;
ok('every move returns finite numbers from t = -1 to 4', bad === 0, bad ? `${bad} non-finite results` : '');

// fluid · the moves from the ebb film
ok('swiftSpring: .smooth is critically damped at ω 2π/d', near(OM.swiftSpring(0.3, 'smooth'), OM.spring(0.3, 1, 2 * Math.PI / 0.5)) && near(OM.swiftSpring(0.3, 'bouncy', { duration: 0.6 }), OM.spring(0.3, 0.7, 2 * Math.PI / 0.6)));
{ const a = OM.lightField(0), b = OM.lightField(1);
  ok('lightField: rest horizon at 0.84 H, flood above the frame', near(a.horizon, 1080 * 0.84) && b.horizon < 0 && b.cy - b.ry < 0 && b.rx > 1920); }
{ const r = OM.ripple(5.8, 5.25), e = OM.ripple(9, 5.25);
  ok('ripple: rings lead in order and all leave the frame', r.r[0] > r.r[1] && r.r[1] > r.r[2] && e.done && e.r.every(v => near(v, 1160))); }
{ const a = OM.silk(4.2, 3), b = OM.silk(4.2, 3), c = OM.silk(4.3, 3);
  ok('silk: 16×20 RGBA, deterministic, drifts with tau', a.length === 16 * 20 * 4 && a.every((v, i) => v === b[i]) && a.some((v, i) => v !== c[i]));
  const L = x => 0.3 * x[0] + 0.59 * x[1] + 0.11 * x[2], ramp = OM.silk.ramps.ember;
  ok('silk: the ember ramp has its dark fold between two brights', L(OM.silk.ramp(ramp, 0.42)) < L(OM.silk.ramp(ramp, 0.22)) && L(OM.silk.ramp(ramp, 0.42)) < L(OM.silk.ramp(ramp, 0.74))); }
{ const B = OM.carouselLoop({ dur: 6, start: 1, speed: 200, stop: [4, 4.5] }), s0 = B.at(0.9), m1 = B.at(3), m2 = B.at(3.1), e1 = B.at(5), e2 = B.at(5.5);
  ok('carouselLoop: still before start, ~speed in the run, stopped after', near(s0.x, 0) && Math.abs((m2.x - m1.x) / 0.1 - 200) < 3 && near(e1.x, e2.x) && near(e1.tau, e2.tau)); }

// ui_kit · the time warp between a narration and the authored timeline, languages, subtitles, the replica stage
{
const UIK = require(path.join(__dirname, '..', 'lib', 'ui_kit.js'));
const tw = UIK.timeWarp([[0, 0], [0.5, 0.5], [2.9, 2.88], [13.04, 12.49], [20.14, 18.3], [46.06, 42.76]]);
let twErr = 0; for (let t = -1; t < 60; t += 0.017) twErr = Math.max(twErr, Math.abs(tw.Ui(tw.U(t)) - t));
ok('timeWarp: Ui(U(t)) = t', twErr < 1e-9, twErr.toExponential(1));
ok('timeWarp: knots hit, 1:1 after the last', near(tw.U(20.14), 18.3) && near(tw.U(50), 46.7) && near(tw.Ui(46), 49.3));
let threw = false; try { UIK.timeWarp([[0, 0], [2, 3], [3, 2]]); } catch (e) { threw = true; }
ok('timeWarp: refuses knots that go back in time', threw);
ok('timeWarp: slopes report slow and fast stretches', tw.slopes.length === 5 && tw.slopes.every(q => q.rate > 0));
const trJ = UIK.tr('ja'); ok('tr: picks the language, falls back to en, passes strings', trJ({ en: 'a', ja: 'b' }) === 'b' && trJ({ en: 'a' }) === 'a' && trJ('c') === 'c');
const su = [[1, 2, 'x']]; ok('subAt: inside, fades, outside', UIK.subAt(su, 1.5).a === 1 && near(UIK.subAt(su, 1.04).a, 0.5) && UIK.subAt(su, 2) === null);
const stg = UIK.stage({ x: 100, y: 50, s: 0.5, chrome: 35 }); const bx = stg.box({ x: 20, y: 10, w: 40, h: 8 });
ok('stage: replica-local → plane', near(bx.x, 110) && near(bx.y, 90) && near(bx.w, 20) && near(stg.place(0, 0).y, 85));
ok('zoomFor: 13 px text at 0.75 needs ×2.67 for 26 px', near(UIK.zoomFor(13, 0.75), 2.6667, 1e-3) && near(UIK.screenPx(13, 0.75, 2.6667), 26, 1e-3));
}

console.log(fails ? `\n${fails} FAILED` : '\nALL PASS');
process.exit(fails ? 1 : 0);
