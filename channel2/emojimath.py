#!/usr/bin/env python3
"""Brain Warp Lab — emoji math puzzle Short (the "🍎+🍎+🍎=30" format).
Three clue equations pop in, the final line mixes + and × (order of operations is the trap), an 8-second
countdown, then the solution is worked out step by step.
  python3 -I channel2/emojimath.py SEED OUT.mp4"""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bwlkit import *
from PIL import Image, ImageDraw

SEED, OUT = int(sys.argv[1]), sys.argv[2]
rnd = random.Random(SEED * 31 + 7)
POOL = ['🍎', '🍌', '🍇', '🍩', '🍕', '🐱', '🐶', '⭐', '⚽', '🎁', '🍔', '🍓', '🦊', '🌵', '🍉', '🧁', '🐸', '🚗', '🎈', '🍪']
NAMES = {'🍎': 'apple', '🍌': 'banana', '🍇': 'grapes', '🍩': 'donut', '🍕': 'pizza', '🐱': 'cat', '🐶': 'dog', '⭐': 'star',
         '⚽': 'ball', '🎁': 'gift', '🍔': 'burger', '🍓': 'strawberry', '🦊': 'fox', '🌵': 'cactus', '🍉': 'melon',
         '🧁': 'cupcake', '🐸': 'frog', '🚗': 'car', '🎈': 'balloon', '🍪': 'cookie'}
A, B, C = rnd.sample(POOL, 3)
a = rnd.randint(4, 15); b = rnd.randint(2, 9); c = rnd.randint(1, 5)
while b == c or a == b: b = rnd.randint(2, 9)
variant = rnd.randrange(3)
clues = [([A, '+', A, '+', A], 3 * a), ([A, '+', B, '+', B], a + 2 * b), ([B, '+', C, '+', C], b + 2 * c)]
if variant == 0:   final, ans, work = [A, '+', B, '×', C], a + b * c, f'{a} + {b} × {c} = {a} + {b * c} = {a + b * c}'
elif variant == 1: final, ans, work = [C, '+', A, '×', B], c + a * b, f'{c} + {a} × {b} = {c} + {a * b} = {c + a * b}'
else:              final, ans, work = [B, '×', C, '+', A], b * c + a, f'{b} × {c} + {a} = {b * c} + {a} = {b * c + a}'
mult_first = 'Multiply first!'

CARD_BOX = (60, 420, 1020, 1390)
ROW_Y = [540, 740, 940, 1170]
INTRO, SHOW, THINK, SOLVE, END = 0.5, 3.2, 8.0, 7.5, 3.0
t_rows = [INTRO + 0.15 + i * 0.75 for i in range(4)]
t_think = INTRO + SHOW; t_solve = t_think + THINK; t_end = t_solve + SOLVE; T = t_end + END
VAL_T = [t_solve + 0.4 + i * 1.0 for i in range(3)]; FINAL_T = t_solve + 3.6


def row_tokens(tokens, rhs, y, d, im, k=1.0, rhs_col=INK):
    parts = []
    for tk in tokens:
        if tk in ('+', '×', '-'): parts.append(('op', tk, 70))
        else: parts.append(('em', tk, 128))
    parts.append(('op', '=', 76)); parts.append(('num', str(rhs), int(d.textlength(str(rhs), font=font('Inter Black', 104))) + 10))
    total = sum(p[2] for p in parts); x = W / 2 - total / 2
    for kind, v, w in parts:
        cx = x + w / 2
        if kind == 'em':
            g = emoji(v, max(4, int(112 * k))); im.alpha_composite(g, (int(cx - g.width / 2), int(y - g.height / 2)))
        elif kind == 'op':
            d.text((cx, y), v, font=font('Inter Black', max(10, int(84 * k))), fill=(120, 100, 170), anchor='mm')
        else:
            d.text((cx, y + 2), v, font=font('Inter Black', max(10, int(104 * k))), fill=rhs_col, anchor='mm')
        x += w


def frame(t):
    if t >= t_end:
        return end_screen(t, t_end, T, headline=('DID YOU', 'GET IT?'), buttons=(('YES', GREEN), ('NO', RED)),
                          line='Comment your answer  ·  new puzzle every day')
    im = background(t); d = ImageDraw.Draw(im); brand_top(d)
    tk = ease_out_back(t * 2.4); title(d, 'CAN YOU SOLVE IT?', 80, scale=0.6 + 0.4 * tk)
    pill(d, 'EMOJI MATH  ·  ' + ('TRICKY' if variant < 2 else 'HARD'), 350, AMBER if variant < 2 else RED)
    im.alpha_composite(card(CARD_BOX)); d = ImageDraw.Draw(im)
    d.line([(150, 1060), (930, 1060)], fill=(205, 195, 230), width=4)
    for i, (toks, rhs) in enumerate(clues + [(final, '?')]):
        if t < t_rows[i] or (i == 3 and t >= FINAL_T): continue
        k = ease_out_back((t - t_rows[i]) * 4)
        row_tokens(toks, rhs, ROW_Y[i], d, im, k, rhs_col=MAGENTA if rhs == '?' else INK)
    if t_think <= t < t_solve:
        u = (t - t_think) / THINK; left = math.ceil(t_solve - t)
        timer(d, 1 - u, left, AMBER if left > 3 else RED, t)
        if t - t_think < 2.5:
            d.text((W // 2, 1640), 'pause & comment your answer', font=font('Inter Display SemiBold', 40), fill=(220, 210, 255), anchor='mm')
    if t >= t_solve:                                         # solution panel slides over the bottom
        u = t - t_solve
        sol = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sol)
        sd.rounded_rectangle([60, 1405, 1020, 1628], 40, fill=(24, 14, 50, 235))
        for i, (e_, v) in enumerate(((A, a), (B, b), (C, c))):
            if t < VAL_T[i]: continue
            kk = ease_out_back((t - VAL_T[i]) * 4); cx = 220 + i * 320
            g = emoji(e_, max(4, int(86 * kk))); sol.alpha_composite(g, (int(cx - 85 - g.width / 2), int(1462 - g.height / 2)))
            sd.text((cx + 40, 1464), f'= {v}', font=font('Inter Black', max(10, int(70 * kk))), fill=(255, 255, 255), anchor='mm')
        if t >= FINAL_T:
            kk = ease_out_back((t - FINAL_T) * 3)
            sd.text((W // 2, 1538), work, font=font('Inter Black', max(10, int(58 * kk))), fill=ACCENT, anchor='mm')
            pill(sd, mult_first, 1596, YEL, size=32)
        im.alpha_composite(sol)
        if t >= FINAL_T:                                     # the '?' becomes the answer
            d = ImageDraw.Draw(im); y = ROW_Y[3]
            row_tokens(final, ans, y, d, im, 1.0, rhs_col=(40, 170, 90))
            e = ease_out_back((t - FINAL_T) * 3); hw, hh = 440 * min(1, e), 88 * min(1, e)
            for wdt, col in ((14, (40, 170, 90, 90)), (7, (40, 170, 90, 255))):
                d.rounded_rectangle([W // 2 - hw, y - hh, W // 2 + hw, y + hh], int(hh), outline=col, width=wdt)
    return im


au = Audio(T)
au.music_bed(t_end, intense_from=t_think + THINK - 3)
au.sfx_at(0, whoosh(0.5, 0.3)); au.say(0.15, 'Can you solve this? Watch the last line.')
for tt in t_rows: au.sfx_at(tt, pop(0.18))
au.say(t_think + 0.1, 'You have eight seconds. Comment your answer!', speed=1.15)
for s_ in range(1, int(THINK)):
    au.sfx_at(t_think + s_, heartbeat(0.55) if THINK - s_ <= 3 else tick())
au.sfx_at(t_solve, whoosh(0.4, 0.3))
au.say(t_solve + 0.3, f'The {NAMES[A]} is {a}, the {NAMES[B]} is {b}, and the {NAMES[C]} is {c}.', speed=1.15)
for vt in VAL_T: au.sfx_at(vt, pop(0.2))
au.sfx_at(FINAL_T, chime())
au.say(FINAL_T + 0.2, f"{mult_first} The answer is {ans}.", speed=1.1)
au.say(t_end + 0.1, 'Did you get it right?')
encode(frame, T, au, OUT)
print('emojimath', OUT, round(T, 1), 's', A, a, B, b, C, c, 'final', ''.join(final), '=', ans)
