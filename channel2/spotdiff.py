#!/usr/bin/env python3
"""Brain Warp Lab — "Find 3 differences" Short. Two emoji scenes stacked; the bottom one has one item
missing, one swapped for a look-alike and one shrunk. 12-second countdown, then the
differences are circled one by one on both pictures.
  python3 -I channel2/spotdiff.py SEED OUT.mp4 [--preview]"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bwlkit import *
from PIL import Image, ImageDraw

SEED, OUT = int(sys.argv[1]), sys.argv[2]; PREVIEW = '--preview' in sys.argv
rnd = random.Random(SEED * 101 + 3)
THEMES = [
    ('GARDEN', (214, 240, 200), '🌸🌳🐝🦋🍄🐞🌻🐌🌷🐦', {'🌸': '🌺', '🐝': '🐞', '🌻': '🌼', '🌷': '🌹', '🐦': '🐤', '🍄': '🌰'}),
    ('OCEAN', (196, 226, 250), '🐠🐙🐚🦀🐳🐟🦑🐡🐬🌊', {'🐠': '🐟', '🐙': '🦑', '🐳': '🐋', '🐡': '🐠', '🐬': '🐳', '🦀': '🦞'}),
    ('SPACE', (40, 30, 80), '🚀🪐⭐🌙👽☄️🛸🌍✨🌟', {'⭐': '🌟', '🌙': '🌛', '🚀': '🛸', '👽': '👾', '🌍': '🌎', '🪐': '🌕'}),
    ('KITCHEN', (250, 236, 214), '🍳🥕🍅🧀🥖🍰🥚🍋🥛🍓', {'🍅': '🍎', '🍋': '🍊', '🍓': '🍒', '🧀': '🍰', '🥚': '🍳', '🥕': '🌶️'}),
    ('FARM', (226, 240, 196), '🐄🐔🐷🌾🚜🏠🐑🐴🌽🐓', {'🐔': '🐓', '🐷': '🐗', '🐄': '🐮', '🐑': '🐐', '🌽': '🌾', '🐴': '🦄'}),
]
name, bgc, pool, swaps = THEMES[(SEED - 1) % len(THEMES)]
pool = split_emoji(pool)

PW, PH = 940, 560
TOP = (70, 410); BOT = (70, 1000)                    # top-left corners of the two panels
items = []                                           # (x, y, size, emoji, angle) in panel coordinates
tries = 0
while len(items) < 15 and tries < 4000:
    tries += 1
    s = rnd.choice((80, 92, 104, 118)); x = rnd.uniform(60, PW - 60); y = rnd.uniform(60, PH - 60)
    if all(math.hypot(x - i[0], y - i[1]) > (s + i[2]) * 0.62 for i in items):
        items.append((x, y, s, rnd.choice(pool), rnd.uniform(-15, 15)))
# choose 3 differences, kept away from the right edge (Shorts buttons) and from each other
cand = [k for k, it in enumerate(items) if it[0] < PW - 150]
rnd.shuffle(cand); diffs = []
for k in cand:
    if all(math.hypot(items[k][0] - items[j][0], items[k][1] - items[j][1]) > 200 for j in diffs): diffs.append(k)
    if len(diffs) == 3: break
kinds = ['missing', 'swap', 'shrink']; rnd.shuffle(kinds)
bottom = list(items)
for k, kind in zip(diffs, kinds):
    x, y, s, e, a = items[k]
    if kind == 'missing': bottom[k] = None
    elif kind == 'swap':
        alt = swaps.get(e) or rnd.choice([p for p in pool if p != e]); bottom[k] = (x, y, s, alt, a)
    else: bottom[k] = (x, y, int(s * 0.55), e, a)          # shrink: visible even on symmetric emoji


def panel(its, dark):
    im = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, PW - 1, PH - 1], 40, fill=bgc + (255,))
    for it in its:
        if it is None: continue
        x, y, s, e, a = it; g = emoji(e, s).rotate(a, expand=True, resample=Image.BICUBIC)
        im.alpha_composite(g, (int(x - g.width / 2), int(y - g.height / 2)))
    return im

P_TOP, P_BOT = panel(items, False), panel(bottom, False)
INTRO, THINK, REVEAL, END = 0.8, 12.0, 4.6, 3.0
t_think = INTRO; t_rev = INTRO + THINK; t_end = t_rev + REVEAL; T = t_end + END
REV_T = [t_rev + 0.5 + i * 1.2 for i in range(3)]


def frame(t):
    if t >= t_end:
        return end_screen(t, t_end, T)
    im = background(t); d = ImageDraw.Draw(im); brand_top(d)
    title(d, 'FIND 3 DIFFERENCES', 74, scale=0.6 + 0.4 * ease_out_back(t * 2.4))
    found = sum(1 for rt in REV_T if t >= rt)
    pill(d, f'{name}  ·  {found}/3', 350, AMBER if found < 3 else GREEN)
    for (px, py), P, delay in ((TOP, P_TOP, 0.0), (BOT, P_BOT, 0.15)):
        k = ease_out_back((t - delay) * 3)
        if k <= 0.02: continue
        sh = Image.new('RGBA', (PW + 60, PH + 60), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([30, 44, PW + 30, PH + 44], 40, fill=(0, 0, 0, 120))
        if k < 0.999:
            Pk = P.resize((max(2, int(PW * k)), max(2, int(PH * k))), Image.LANCZOS)
            im.alpha_composite(Pk, (int(px + PW / 2 - Pk.width / 2), int(py + PH / 2 - Pk.height / 2)))
        else:
            im.alpha_composite(P, (px, py))
    d = ImageDraw.Draw(im)
    if t_think <= t < t_rev:
        u = (t - t_think) / THINK; left = math.ceil(t_rev - t)
        timer(d, 1 - u, left, AMBER if left > 3 else RED, t, cx=W // 2, cy=1645, R=58)
    for i, k in enumerate(diffs):
        if t < REV_T[i]: continue
        x, y, s = items[k][:3]
        for (px, py) in (TOP, BOT):
            ring(d, px + x, py + y, s * 0.85, (t - REV_T[i]) / 1.2, col=MAGENTA)
    return im


if PREVIEW:
    frame(t_rev + 4.0).convert('RGB').save(OUT); print('preview', OUT, name, kinds); sys.exit()
au = Audio(T)
au.music_bed(t_end, intense_from=t_rev - 4)
au.sfx_at(0, whoosh(0.5, 0.3)); au.sfx_at(0.2, pop(0.15)); au.sfx_at(0.35, pop(0.15))
au.say(0.15, 'Find three differences before the time runs out!')
for s_ in range(1, int(THINK)):
    au.sfx_at(t_think + s_, heartbeat(0.55) if THINK - s_ <= 3 else tick())
au.say(t_rev + 0.05, "Time's up!", speed=1.15)
for rt in REV_T: au.sfx_at(rt, chime(0.8))
au.say(t_end + 0.1, 'How many did you find? Comment your score!')
encode(frame, T, au, OUT)
print('spotdiff', OUT, round(T, 1), 's', name, kinds)
