// onetake · © 2026 Patrick (github.com/feitangyuan) · PolyForm Noncommercial 1.0.0 · lineage otk-7f3e1c
/* ui_kit.js — helpers for films that show a product's UI without a screen recording: the UI rebuilt in HTML,
 * placed on the composition's plane, highlighted from its own DOM, narrated, and cut in more than one language.
 * → window.UIK (or module.exports under node). Pure functions and small factories; no look is baked in —
 * colours, sizes and timings are always arguments. See references/product-demo.md.
 */
(function (root) {
  'use strict';
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, k) => a + (b - a) * k;
  const seg = (t, a, b) => clamp((t - a) / (b - a));

  // ── the replica on the plane ──────────────────────────────────────────────────────────────────────────────────────
  // A replica is laid out in its reference's own pixel frame (e.g. a recording's 1918 × 1080) and shown scaled by `s`
  // inside a window at (x, y) on the plane, under a chrome bar `chrome` px tall. place(lx, ly) → plane point;
  // box(r) → plane rect for a replica-local rect.
  function stage({ x, y, s, chrome = 0 }) {
    const place = (lx, ly) => ({ x: x + lx * s, y: y + chrome + ly * s });
    const box = r => ({ x: x + r.x * s, y: y + chrome + r.y * s, w: r.w * s, h: r.h * s });
    return { place, box, s };
  }
  // An element's rect in the replica's own frame, by the offset chain up to `rootClass`. Not getBoundingClientRect:
  // that one already includes the camera's transform and changes every frame.
  function domLocal(el, rootClass) {
    let x = 0, y = 0, e = el;
    while (e && !(e.classList && e.classList.contains(rootClass))) { x += e.offsetLeft; y += e.offsetTop; e = e.offsetParent; }
    return { x, y, w: el.offsetWidth, h: el.offsetHeight };
  }
  // Remembers each key's last measured rect, so a highlight can keep fading out after its element is hidden.
  function rectCache() {
    const m = {};
    return (key, measure) => { const r = measure && measure(); if (r && r.w > 0) m[key] = r; return m[key] || null; };
  }
  // Lays items out left to right by their measured width (for strings whose width changes with the language);
  // a replica keeps the reference's fixed lefts for its source language and flows for every other one.
  function flow(items, x0, gap) { let x = x0; items.forEach(e => { e.style.left = x + 'px'; x += e.offsetWidth + gap; }); return x; }

  // ── highlight: a rounded rect hugging the content, drawn on, a soft glow, then out ────────────────────────────────
  // g: a 2D context already in plane coordinates · r: {x, y, w, h} · col: any CSS colour · zoom: the camera's, so the
  // line keeps its screen width. spring(t) is optional (pass OM.spring for a small pop). Returns nothing when off.
  function glowRing(g, r, t, t0, t1, col, { pad = 8, zoom = 1, out = 0.3, draw = 0.45, layers = [[10, 0.35, 14], [4, 0.6, 6], [2.4, 1, 0]], fill = 0.07, pop = null } = {}) {
    const o = 1 - clamp((t - t1) / out); if (t < t0 || o <= 0) return;
    const k = 1 - Math.pow(2, -10 * seg(t, t0, t0 + draw));                            // expo-out draw-on
    const x = r.x - pad, y = r.y - pad, w = r.w + 2 * pad, h = r.h + 2 * pad, q = Math.min(12, h / 3, w / 3);
    const per = 2 * (w + h) - (8 - 2 * Math.PI) * q, sc = pop ? pop(t - t0) : 1;
    g.save(); g.translate(x + w / 2, y + h / 2); g.scale(sc, sc); g.translate(-(x + w / 2), -(y + h / 2));
    g.beginPath(); g.roundRect(x, y, w, h, q);
    if (fill) { g.globalAlpha = fill * k * o; g.fillStyle = col; g.fill(); }
    g.setLineDash([per * k, per + 10]); g.lineCap = 'round'; g.strokeStyle = col;
    layers.forEach(([lw, op, blur]) => { g.globalAlpha = op * o * clamp(k * 3); g.lineWidth = lw / zoom; g.shadowColor = blur ? col : 'transparent'; g.shadowBlur = blur; g.stroke(); });
    g.setLineDash([]); g.shadowColor = 'transparent'; g.restore();
  }
  // How big a replica's text is on screen: font px × replica scale × camera zoom. Aim ≥ 26 for anything the VO names.
  const screenPx = (fontPx, s, zoom) => fontPx * s * zoom;
  const zoomFor = (fontPx, s, targetPx = 26) => targetPx / (fontPx * s);

  // ── languages ─────────────────────────────────────────────────────────────────────────────────────────────────────
  // tr(lang)({en: '…', ja: '…'}) → that language's string, falling back to en; a plain string passes through.
  const tr = lang => o => (o == null || typeof o !== 'object' ? o : (o[lang] ?? o.en));
  // Registers a local font file only for the languages that need it and resolves when it has loaded (await it in
  // __ready). Keep the source language's page untouched: nothing is added when need is false.
  function loadFont(family, url, { weight = '100 900', need = true } = {}) {
    if (!need || typeof FontFace === 'undefined') return Promise.resolve();
    const f = new FontFace(family, `url(${url})`, { weight }); document.fonts.add(f); return f.load();
  }

  // ── time: one authored timeline, several narrations ───────────────────────────────────────────────────────────────
  // Beats, camera, hand and events are authored once, on the source VO. Another language's film maps its own clock onto
  // that authoring clock through knots [[filmT, authorT], …], set on words that mean the same thing (not just line
  // starts: word order moves). Linear between knots, 1:1 before the first and after the last. U: film → authoring,
  // Ui: authoring → film. Seek draws at U(t); subtitles and __meta.dur are film time; __events() maps back with Ui.
  function timeWarp(knots) {
    const K = [...knots].sort((p, q) => p[0] - q[0]);
    for (let i = 1; i < K.length; i++) if (!(K[i][0] > K[i - 1][0] && K[i][1] > K[i - 1][1])) throw new Error(`timeWarp: knots must rise on both clocks (at ${i})`);
    const map = (t, a, b) => {
      if (!K.length) return t; if (t <= K[0][a]) return K[0][b] + t - K[0][a];
      for (let i = 0; i < K.length - 1; i++) if (t < K[i + 1][a]) return K[i][b] + (t - K[i][a]) * (K[i + 1][b] - K[i][b]) / (K[i + 1][a] - K[i][a]);
      const q = K[K.length - 1]; return q[b] + t - q[a];
    };
    // slopes: authoring seconds per film second, per stretch — < 0.5 is slow motion, > 1.4 is a rush; check before rendering
    const slopes = K.slice(1).map((q, i) => ({ film: [K[i][0], q[0]], rate: (q[1] - K[i][1]) / (q[0] - K[i][0]) }));
    return { U: t => map(t, 0, 1), Ui: t => map(t, 1, 0), slopes };
  }
  const identity = { U: t => t, Ui: t => t, slopes: [] };

  // ── subtitles ─────────────────────────────────────────────────────────────────────────────────────────────────────
  // subs: [[t0, t1, text], …] in film time (scripts/vo_tools.py subs). → {text, a} with short fades, or null.
  function subAt(subs, t, fade = 0.08) {
    for (const q of subs) if (t >= q[0] && t < q[1]) return { text: q[2], a: clamp((t - q[0]) / fade) * clamp((q[1] - t) / fade) };
    return null;
  }

  const UIK = { stage, domLocal, rectCache, flow, glowRing, screenPx, zoomFor, tr, loadFont, timeWarp, identity, subAt, lerp };
  if (typeof module !== 'undefined' && module.exports) module.exports = UIK; else root.UIK = UIK;
})(typeof window !== 'undefined' ? window : globalThis);
