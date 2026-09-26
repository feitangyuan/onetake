# Sound — a palette in a room

The first pass gave every visual event its own synthesised tone: sine pops for words, noise ticks for
letters, a "boing" for jelly. Rejected within a minute as 低劣. What was wrong is instructive:

- **raw sines** read as a chiptune; real objects have partials and a noise transient;
- **no space** — nothing shared a room, so the sounds sat on top of the picture instead of in it;
- **one sound per event** — 40 typing ticks plus 10 letter ticks plus 26 confetti pops is a
  slot machine;
- **flat dynamics** — everything at the same level, no rests.

## The palette (`scripts/sfx_palette.py`)

| material | how it is made | used for |
|---|---|---|
| `air(dur, f0, f1, q, shape)` | noise → resonant band-pass whose centre glides f0→f1, low-passed at 5.5 k, sine-shaped envelope | whooshes: cards in/out, screens flying (pan it with the picture) |
| `glass(f, dur, bright)` | fundamental + inharmonic partials (2.76 f, 5.4 f) with faster decays + a 2 k noise transient | ticks up a scale, PASS chord, word touches |
| `wood(f, dur)` | low body knock with a pitch drop + a 3.2 k filtered snap | keys (one in three, random velocity), mouse down/up as two hits 60 ms apart |
| `sub(f, dur)` | sine with a pitch drop, tanh-saturated, felt transient | hard-cut hits, landings; the deep one under black |
| `bubble(f, dur)` | a resonance rising as it "closes" + tiny noise | rounded pop when a card lands |
| `wobble(f, dur)` | FM'd tone, 8.5 Hz vibrato decaying | the one jelly flick |

`pan_of(x)` maps a screen x to ±0.6; `place(sig, t, gain, pan, send, pan_to)` puts a sound at a time
with an optional pan sweep, and sends a share to the room.

## The room

One synthetic impulse response for everything: 1.1 s T60, 12 ms pre-delay, three early reflections,
low-passed decorrelated stereo. Sent at 15–70 % depending on how far the object is (a key: 0.15; a
long air breath: 0.6). The room is what makes disparate sounds one film.

## Levels

- Palette: soft ceiling `tanh(1.3·x)` then normalise to **−8 dBFS peak**: loud enough alone, room for music.
- Mastered score.py (every accepted film since one-dot): **−16 LUFS integrated**, true-peak ceiling −3.5 dBTP, dropped
  to −4 when the AAC render reads above verify's −3 dBFS (overlap v4: −2.7 at −3.5, −3.8 at −4.0).
- Dynamics follow the picture's energy map: the quiet hold is *silent* after its one breath; the
  hits are the loudest thing in the film.
- Check with `verify_promo.py`: it reports peak, clipping, and the fraction of quiet frames.

## Scoring

`templates/sfx_score.example.py` is the motion-web score: import the palette, `place()` each event
at the composition's own constants (copy them; do not retype numbers), `write()`. Fewer events than
beats. If two sounds would land within 40 ms, keep one.

**Score from the comp, not from retyped times** (knockon, clearing, unbroken). The comp exports what the sound needs:

- `window.__events()` → `{T, events: [{t, kind, pan, v}]}`: every contact, its screen x through the camera at that
  instant as a pan from −1 to 1, and a strength;
- a continuous curve wherever a sound must follow the picture: the marble's speed (`__marbleSpeed`), the zoom's
  d log zoom / dt (`__zoomVel`), each brush's speed × pressure (`__brush` → `[left, right]`).

`dump_events.py` (Playwright) writes `events.json` and the curve at 240 Hz; `score.py` reads both, so a retimed beat
takes its sound with it. The recorded-palette `score.py` from one-dot splits into sources, shaping, synthesis, buses and
master, which each new film copies unchanged, plus the score itself (~60 lines).

Curves that became instruments:

- **the camera's air** (clearing): noise in three bands (150–600 Hz, 0.6–2.4 kHz, 2.4–9 kHz) crossfaded by depth
  `log(zoom) / log(300)`, so closer is brighter, and scaled by `|d log zoom / dt| ^ 1.3`;
- **hair on paper** (unbroken): a 1.8–7.5 kHz rasp over a 350–1,100 Hz body, each scaled by the brush's energy, with
  ~30 Hz fibre flutter; one per side of the split.

**Find mud per window.** knockon's first mix put 41.6 % of its energy in 100–300 Hz, and thinning the obvious suspect
(the rumble) changed nothing. Band shares per 0.5 s window found the cause: 95 % low-mid at 4.5 s, from a marimba run
starting on F3 whose 1.8 s tails piled up. An octave up with 0.7 s notes brought that window to 6 % and the mix to 32 %.
Keep pitched runs at F4 and above, and cut their tails.

**Judge the arc by K-weighted loudness per beat**, not by RMS. The landing has to read louder than the move into it:
clearing's second dive and its landing both measured −14 LUFS until the dive came down 4 dB.

**Current launch-film sound direction** (user correction, 2026-09-24). The Adventure and Getaway cuts were rejected:
the music was intrusive and the action sounds effectively inaudible. The earlier indie-dance / funk / future-house
recommendation is superseded for this film. The user wants the feel of Apple motion/product films; an exact reference
has not yet been supplied, so do not treat a genre label or a loudness target as proof of matching that taste.
Build the action score first: tactile contacts, paper/ink/brush detail, camera air driven by motion, and deliberate
rests. Use restrained music that leaves these sounds audible; avoid a full-density track playing continuously over
everything. Compare music and SFX in their actual event windows and shared frequency bands, then audition the mix.
In the rejected v3, SFX were 26.8–35.0 dB below music by event-window RMS and 17–23 dB below it at 800–4500 Hz;
normalising the whole mix to −19 LUFS did not repair that balance. Do not reuse whole case mixes and their repeated
end chords when combining films: reuse the independent sources, timing curves and material identities instead.

**Retired ending: the vibraphone chord + crotale shimmer.** three earlier films all resolved on it; the user
heard it as the stock ending 「好多视频都是这个音效」. End on the music's own cadence, or a hit that belongs to the film.
