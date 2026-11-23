#!/usr/bin/env python3
"""Brain Warp Lab — "Find the odd one out" v2 (motion-designed).
Animated background, title drop, emoji grid popping in, circular countdown with a heartbeat in the last
3 seconds, card slides between levels, the answer zooms out of the grid with a drawn ring and sparkles,
an end screen with 1/2/3 buttons — plus an original music bed composed here (no samples, no licences).
  python3 -I channel2/oddone2.py SEED OUT.mp4 [MODE]
MODE: emoji (default) | text (hidden letter/number, e.g. 81 among 18s) | color (one tile a slightly different shade)
Emoji art: Noto Color Emoji (SIL OFL). Voice: Kokoro (Apache 2.0), offline."""
import sys, os, math, random, functools, subprocess, unicodedata, numpy as np, soundfile as sf, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SEED, OUT = int(sys.argv[1]), sys.argv[2]
MODE = sys.argv[3] if len(sys.argv) > 3 else 'emoji'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import brandmark
import colorsys
W, H, FPS, SR = 1080, 1920, 30, 44100
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
KOKORO = os.environ.get('KOKORO_DIR', '/tmp/claude-0/-home-user/d825807f-e0e5-55ce-ac85-8ebee4d46dbb/scratchpad/kokoro')
rnd = random.Random(SEED)

PAIRS = {
    'easy':   ['❤️🧡', '🔵🟣', '🍊🍑', '🌕🌝', '📕📙', '⚽🏐', '🐻🐨', '🐮🐷', '🐟🐠', '🍓🍒', '🚗🚕', '💙💜', '🍏🍎', '🐝🐞', '🍋🍊'],
    'medium': ['🍎🍅', '🦁🐯', '⭐🌟', '🌻🌼', '😴😪', '🐸🐢', '🍩🥯', '🐶🐕', '🌲🌳', '🙂🙃', '🐭🐹', '😆😂', '🙄😒'],
    'hard':   ['😀😃', '😄😁', '😐😑', '🙈🙊', '😺😸', '😮😯', '😟🙁', '😊🙂', '😃😄', '🌙🌛', '😗😙', '😶😐'],
}
TEXT_PAIRS = {   # (majority, odd) in Inter Black
    'easy':   ['OQ', 'EF', 'PR', '8B', 'CG', 'MW', 'KX', 'VY', '5S', 'IT', 'UV', 'HN'],
    'medium': ['81|18', '69|96', 'NM', '38', '2Z', 'bd', 'pq', '17|71', 'DO', 'Ww', 'CO', '6b'],
    'hard':   ['O0', 'rn|m', 'VV|W', 'cl|d', '1l', 'nm', 'ce', 'il|li', 'ij', 'B8', 'S5', 'G6'],
}
LEVELS = [('easy', 5, 7, 5.0, (88, 220, 130)), ('medium', 6, 9, 6.0, (255, 200, 60)), ('hard', 7, 11, 7.0, (255, 80, 100))]
if MODE == 'text':
    LEVELS = [('easy', 6, 8, 5.0, (88, 220, 130)), ('medium', 7, 10, 6.0, (255, 200, 60)), ('hard', 8, 12, 7.0, (255, 80, 100))]
COLOR_DELTA = {'easy': 0.16, 'medium': 0.085, 'hard': 0.045}   # lightness gap of the odd tile
TITLE = {'emoji': 'FIND THE ODD ONE OUT', 'text': 'FIND THE ODD ONE OUT', 'color': 'FIND THE DIFFERENT COLOR'}[MODE]
TITLE_SIZE = 76 if MODE != 'color' else 66
INTRO, REVEAL, SWAP, END = 0.9, 1.9, 0.45, 3.0
CARD = (70, 450, 1010, 1400)                      # card box; the grid sits inside with a margin
ACCENT, MAGENTA = (46, 230, 214), (255, 60, 200)
_lp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'studio', 'art', 'brainwarplab-logo.png')
LOGO = Image.open(_lp).convert('RGBA').resize((260, 260), Image.LANCZOS)
_m = Image.new('L', (260, 260), 0); ImageDraw.Draw(_m).ellipse([0, 0, 259, 259], fill=255); LOGO.putalpha(_m)


# ---------------------------------------------------------------- helpers
def split2(s):
    out, cur = [], ''
    for ch in s:
        if cur and unicodedata.category(ch) not in ('Mn', 'Cf') and ord(ch) not in (0xFE0F, 0x200D):
            out.append(cur); cur = ''
        cur += ch
    return out + [cur]

@functools.lru_cache(None)
def font(name, s):
    return ImageFont.truetype(subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout, s)

@functools.lru_cache(None)
def glyph(e, size):
    if MODE == 'text':
        f = font('Inter Black', 200); im = Image.new('RGBA', (520, 260), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((260, 130), e, font=f, fill=(44, 26, 84, 255), anchor='mm')
        im = im.crop(im.getbbox()); k = size / max(im.width, im.height)
        return im.resize((max(2, int(im.width * k)), max(2, int(im.height * k))), Image.LANCZOS)
    if MODE == 'color':
        rgb = tuple(int(v) for v in e.split(','))
        im = Image.new('RGBA', (4 * size, 4 * size), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle([0, 0, 4 * size - 1, 4 * size - 1], int(0.9 * size), fill=rgb + (255,))
        return im.resize((max(2, size), max(2, size)), Image.LANCZOS)
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), e, font=f, embedded_color=True, anchor='mm')
    return im.crop(im.getbbox()).resize((max(2, size), max(2, size)), Image.LANCZOS)

def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_in_out(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- animated background (rendered small, upscaled)
bw, bh = 135, 240
yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
BASE_T, BASE_B = np.array([18, 10, 44], np.float32), np.array([44, 16, 78], np.float32)
basegrad = BASE_T + (BASE_B - BASE_T) * (yy / bh)[..., None]
def background(t):
    img = basegrad.copy()
    for (cx, cy, r, col, sp, ph) in ((0.25, 0.25, 0.55, (110, 50, 210), 0.11, 0), (0.8, 0.7, 0.6, (20, 150, 170), 0.08, 2),
                                     (0.6, 0.15, 0.4, (200, 50, 160), 0.13, 4)):
        px = (cx + 0.12 * math.sin(t * sp * 6.28 + ph)) * bw; py = (cy + 0.08 * math.cos(t * sp * 5.1 + ph)) * bh
        g = np.exp(-(((xx - px) / (r * bw)) ** 2 + ((yy - py) / (r * bw)) ** 2))[..., None]
        img += np.array(col, np.float32) * 0.45 * g
    return cv2.resize(np.clip(img, 0, 255).astype(np.uint8), (W, H), interpolation=cv2.INTER_CUBIC)


# ---------------------------------------------------------------- puzzles
puzzles = []
for idx, lv in enumerate(LEVELS):
    name, cols, rows = lv[:3]
    if MODE == 'color':
        h = random.Random(SEED * 7 + idx).random(); sat = 0.55 + 0.25 * rnd.random(); v = 0.62 + 0.18 * rnd.random()
        base = colorsys.hsv_to_rgb(h, sat, v); oddc = colorsys.hsv_to_rgb(h, sat * 0.92, min(1, v + COLOR_DELTA[name]))
        a, b = ','.join(str(int(c * 255)) for c in base), ','.join(str(int(c * 255)) for c in oddc)
    else:
        src = TEXT_PAIRS if MODE == 'text' else PAIRS
        order = src[name][:]; random.Random(4242 + idx).shuffle(order); pick = order[(SEED - 1) % len(order)]
        a, b = (pick.split('|') if '|' in pick else list(pick)) if MODE == 'text' else split2(pick)
    if rnd.random() < 0.5: a, b = b, a
    odd = (rnd.randrange(1, rows - 1), rnd.randrange(cols - 1))
    x0, y0, x1, y1 = CARD[0] + 40, CARD[1] + 40, CARD[2] - 40, CARD[3] - 40
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows; s = int(min(cw, ch) * (0.86 if MODE == 'color' else 0.8))
    cells = [((x0 + (c + .5) * cw, y0 + (r + .5) * ch), b if (r, c) == odd else a, (r, c) == odd) for r in range(rows) for c in range(cols)]
    puzzles.append(dict(lv=lv, idx=idx, cells=cells, size=s, odd=next(p for p, e, o in cells if o), a=a, b=b))


# ---------------------------------------------------------------- foreground layers
def header(d, p, swap_in=1.0):
    name, color, idx = p['lv'][0], p['lv'][4], p['idx']
    d.text((W // 2, 150), 'BRAIN WARP LAB', font=font('Inter Display SemiBold', 30), fill=(200, 190, 255), anchor='mm')
    t = f'LEVEL {idx + 1}  ·  {name.upper()}'; f = font('Inter Black', 42); w = d.textlength(t, font=f)
    d.rounded_rectangle([W // 2 - w / 2 - 32, 330, W // 2 + w / 2 + 32, 396], 33, fill=color)
    d.text((W // 2, 364), t, font=f, fill=(20, 12, 40), anchor='mm')
    for k in range(3):                                                    # progress dots
        cx = W // 2 - 50 + k * 50; fill = color if k <= idx else (90, 80, 130)
        d.ellipse([cx - 9, 418, cx + 9, 436], fill=fill)

def title_layer(scale=1.0, alpha=255):
    im = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((W // 2 + 4, 108), TITLE, font=font('Inter Black', TITLE_SIZE), fill=(0, 0, 0, 110), anchor='mm')
    d.text((W // 2, 104), TITLE, font=font('Inter Black', TITLE_SIZE), fill=(255, 255, 255, alpha), anchor='mm')
    if scale != 1.0:
        im = im.resize((int(W * scale), int(200 * scale)), Image.LANCZOS)
        out = Image.new('RGBA', (W, 200), (0, 0, 0, 0)); out.alpha_composite(im, ((W - im.width) // 2, (200 - im.height) // 2)); im = out
    return im

@functools.lru_cache(None)
def card_base():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).rounded_rectangle([CARD[0], CARD[1] + 18, CARD[2], CARD[3] + 18], 48, fill=150)
    im.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(26)))
    d.rounded_rectangle(CARD, 48, fill=(242, 238, 252, 255))
    return im

def draw_tiles(im, p, pop=None, dim=1.0, skip_odd=False):
    s = p['size']
    for i, ((cx, cy), e, o) in enumerate(p['cells']):
        if skip_odd and o: continue
        k = 1.0 if pop is None else pop(i, cx, cy)
        if k <= 0.02: continue
        g = glyph(e, max(2, int(s * k)))
        if dim < 1.0:
            g = g.copy(); g.putalpha(g.getchannel('A').point(lambda v: int(v * dim)))
        im.alpha_composite(g, (int(cx - g.width / 2), int(cy - g.height / 2)))

@functools.lru_cache(None)
def tiles_static(i):
    im = card_base().copy(); draw_tiles(im, puzzles[i]); return im

def timer(d, frac, left, color, t):
    cx, cy, R = W // 2, 1520, 70
    pulse = 1 + (0.08 * max(0, math.sin((t % 1) * math.pi)) if left <= 3 else 0)
    r = R * pulse
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(24, 14, 50, 235))
    d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * frac, fill=color, width=12)
    d.text((cx, cy + 2), str(left), font=font('Inter Black', int(64 * pulse)), fill=color, anchor='mm')

def ring_and_sparkles(im, p, u):
    cx, cy = p['odd']; s = p['size']; d = ImageDraw.Draw(im)
    R = s * 0.95 * (0.6 + 0.4 * ease_out_back(u * 2.2))
    ang = 360 * ease_in_out(u * 2.5)
    for wdt, col in ((16, MAGENTA + (90,)), (8, MAGENTA + (255,))):
        d.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + ang, fill=col, width=wdt)
    if u < 0.6:
        rr = random.Random(int(cx * 7 + cy))
        for k in range(14):
            a = k / 14 * 6.283 + rr.uniform(-.2, .2); dist = R * (1.1 + 1.6 * ease_in_out(u / 0.6))
            x, y = cx + math.cos(a) * dist, cy + math.sin(a) * dist; z = 9 * (1 - u / 0.6)
            col = (ACCENT if k % 2 else (255, 230, 90)) + (int(255 * (1 - u / 0.6)),)
            d.polygon([(x, y - z * 2), (x + z, y), (x, y + z * 2), (x - z, y)], fill=col)


# ---------------------------------------------------------------- timeline
segs, t = [], 0.0
for i, p in enumerate(puzzles):
    if i == 0: segs.append(('intro', t, t + INTRO, i)); t += INTRO
    else: segs.append(('swap', t, t + SWAP, i)); t += SWAP
    segs.append(('play', t, t + p['lv'][3], i)); t += p['lv'][3]
    segs.append(('reveal', t, t + REVEAL, i)); t += REVEAL
segs.append(('end', t, t + END, None)); T = t + END


def frame(t):
    return brandmark.apply_pil(_frame(t))


def _frame(t):
    kind, a, b, i = next(s for s in segs if s[1] <= t < s[2] or s is segs[-1]); u = (t - a) / (b - a)
    bg = Image.fromarray(background(t)).convert('RGBA')
    if kind == 'end':
        d = ImageDraw.Draw(bg)
        d.text((W // 2, 150), 'BRAIN WARP LAB', font=font('Inter Display SemiBold', 30), fill=(200, 190, 255), anchor='mm')
        k = ease_out_back(u * 4)
        for j, line in enumerate(('HOW MANY', 'DID YOU FIND?')):
            f = font('Inter Black', max(10, int(108 * k)))
            d.text((W // 2, 640 + j * 125), line, font=f, fill=(255, 255, 255), anchor='mm')
        for n in range(3):
            kk = ease_out_back((t - a - 0.45 - n * 0.22) * 4)
            if kk <= 0.02: continue
            cx, cy, r = W // 2 - 220 + n * 220, 1010, 78 * kk
            col = [LEVELS[n][4]][0]
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
            d.text((cx, cy + 3), str(n + 1), font=font('Inter Black', max(10, int(84 * kk))), fill=(20, 12, 40), anchor='mm')
        if u > 0.2:
            lg = LOGO.copy(); lg.putalpha(lg.getchannel('A').point(lambda v: int(v * min(1, (u - .2) * 4))))
            bg.alpha_composite(lg, (W // 2 - LOGO.width // 2, 1300)); d = ImageDraw.Draw(bg)
        if u > 0.35:
            d.text((W // 2, 1200), 'Comment your score  ·  new puzzle every day', font=font('Inter Display SemiBold', 44),
                   fill=ACCENT + (int(255 * min(1, (u - .35) * 5)),), anchor='mm')
        return bg

    p = puzzles[i]; color = p['lv'][4]
    fg = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if kind == 'intro':
        tk = ease_out_back(u * 2.2)
        fg.alpha_composite(title_layer(scale=0.6 + 0.4 * tk), (0, 160))
        header(ImageDraw.Draw(fg), p)
        fg.alpha_composite(card_base())
        ccx, ccy = (CARD[0] + CARD[2]) / 2, (CARD[1] + CARD[3]) / 2
        draw_tiles(fg, p, pop=lambda n, cx, cy: ease_out_back((t - 0.15 - math.hypot(cx - ccx, cy - ccy) / 2200) * 4))
    else:
        fg.alpha_composite(title_layer(), (0, 160)); header(ImageDraw.Draw(fg), p)
        if kind == 'play':
            fg.alpha_composite(tiles_static(i))
            left = math.ceil(b - t); tc = color if left > 3 else (255, 70, 90)
            timer(ImageDraw.Draw(fg), 1 - u, left, tc, t)
        elif kind == 'swap':
            fg.alpha_composite(tiles_static(i))
        elif kind == 'reveal':
            fg.alpha_composite(card_base())
            dim = 1 - 0.82 * ease_in_out(u * 4)
            draw_tiles(fg, p, dim=dim, skip_odd=True)
            cx, cy = p['odd']; k = 1 + 0.55 * ease_out_back(u * 3)
            g = glyph(p['b'], int(p['size'] * k)); fg.alpha_composite(g, (int(cx - g.width / 2), int(cy - g.height / 2)))
            ring_and_sparkles(fg, p, u)
            if u > 0.25:
                kk = ease_out_back((u - .25) * 5)
                ImageDraw.Draw(fg).text((W // 2, 1520), 'FOUND IT?', font=font('Inter Black', max(10, int(72 * kk))), fill=color, anchor='mm')
    if kind == 'swap':                                     # old card leaves left, new one enters from the right
        prev = Image.new('RGBA', (W, H), (0, 0, 0, 0)); prev.alpha_composite(title_layer(), (0, 160))
        header(ImageDraw.Draw(prev), puzzles[i - 1]); prev.alpha_composite(tiles_static(i - 1))
        e = ease_in_out(u); out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        out.alpha_composite(prev.crop((int(e * W), 0, W, H)), (0, 0))
        nx = int((1 - e) * W); out.alpha_composite(fg.crop((0, 0, W - nx, H)), (nx, 0)); fg = out
    bg.alpha_composite(fg); return bg


# ---------------------------------------------------------------- audio: original music bed + voice + sfx
def note(f, dur, kind='marimba', g=0.2):
    n = int(dur * SR); tt = np.arange(n) / SR
    if kind == 'marimba':
        s = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 9) + 0.35 * np.sin(2 * np.pi * f * 4 * tt) * np.exp(-tt * 30)
    elif kind == 'bass':                                    # Karplus-Strong pluck
        N = int(SR / f); buf = np.random.default_rng(int(f)).uniform(-1, 1, N); s = np.zeros(n)
        for k in range(n):
            s[k] = buf[k % N]; buf[k % N] = 0.5 * (buf[k % N] + buf[(k + 1) % N]) * 0.996
        s *= np.exp(-tt * 3)
    elif kind == 'pad':
        s = sum(np.sin(2 * np.pi * f * m * tt + m) / m for m in (1, 2, 3)) * np.minimum(1, tt / 0.3) * np.exp(-tt * 0.8)
    return g * s

mix = np.zeros(int((T + 1) * SR), np.float32); music = np.zeros_like(mix); sfx = np.zeros_like(mix)
def put(buf, at, s, g=1.0):
    i = int(at * SR); j = min(len(buf), i + len(s)); buf[i:j] += g * s[:j - i]

BPM = 112; beat = 60 / BPM
prog = [(60, 64, 67), (57, 60, 64), (53, 57, 60), (55, 59, 62)]   # C  Am  F  G
mf = lambda m: 440 * 2 ** ((m - 69) / 12)
end_t = segs[-1][1]
nb = int(end_t / beat)
for k in range(nb):
    bar, pos = divmod(k, 4); chord = prog[bar % 4]; at = k * beat
    hard = at >= next(s for s in segs if s[0] == 'play' and s[3] == 2)[1]
    if pos == 0:
        put(music, at, note(mf(chord[0] - 24), beat * 2, 'bass', 0.32))
        put(music, at, note(mf(chord[0] - 12), beat * 4, 'pad', 0.05))
    if pos == 2: put(music, at, note(mf(chord[0] - 24 + 7), beat * 2, 'bass', 0.22))
    for half in (0, 1):                                       # marimba arpeggio in eighths
        m = chord[(pos * 2 + half) % 3] + (12 if (pos * 2 + half) % 4 == 3 else 0)
        put(music, at + half * beat / 2, note(mf(m), 0.5, 'marimba', 0.11))
    shaker = np.random.default_rng(k).uniform(-1, 1, int(0.04 * SR)) * np.exp(-np.arange(int(0.04 * SR)) / SR * 90)
    for q in ((0.5,) if not hard else (0.25, 0.5, 0.75)):
        put(music, at + q * beat, shaker, 0.05)
put(music, end_t, note(mf(48), 2.5, 'bass', 0.3)); put(music, end_t, note(mf(72), 1.5, 'marimba', 0.14))
put(music, end_t + 0.05, note(mf(76), 1.5, 'marimba', 0.12)); put(music, end_t + 0.1, note(mf(79), 1.5, 'marimba', 0.12))

def tone(f, dur, decay, g):
    tt = np.arange(int(dur * SR)) / SR; return g * np.sin(2 * np.pi * f * tt) * np.exp(-tt * decay)
def whoosh(dur=0.45, g=0.35):
    n = int(dur * SR); x = np.random.default_rng(1).normal(0, 1, n); env = np.sin(np.linspace(0, np.pi, n)) ** 2
    y = np.convolve(x, np.ones(12) / 12, 'same') * env; return g * y / np.abs(y).max()
def pop(g=0.25):
    n = int(0.08 * SR); tt = np.arange(n) / SR; f = 500 + 900 * tt / 0.08
    return g * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 40)
def heartbeat(g=0.5):
    return tone(55, 0.18, 18, g) + np.concatenate([np.zeros(int(0.14 * SR)), tone(50, 0.16, 20, g * 0.7)])[:int(0.18 * SR)]

from kokoro_onnx import Kokoro
kk = Kokoro(f'{KOKORO}/kokoro.onnx', f'{KOKORO}/voices.bin')
voice = np.zeros_like(mix)
def say(at, txt):
    s, sr = kk.create(txt, voice='am_michael', speed=1.1, lang='en-us')
    s = cv2.resize(s.astype(np.float32)[None, :], (int(len(s) * SR / sr), 1), interpolation=cv2.INTER_LINEAR)[0]
    put(voice, at, s, 1.0)
lines = {0: 'Find the odd one out!', 1: 'Level two.', 2: 'Level three. This one is tricky.'}
if MODE == 'color': lines = {0: 'Find the different color!', 1: 'Level two. Harder.', 2: 'Level three. Only sharp eyes see this one.'}
for kind, a, b, i in segs:
    if kind == 'intro':
        say(a + 0.15, lines[0]); put(sfx, a, whoosh(0.5, 0.3))
        for n in range(6): put(sfx, a + 0.2 + n * 0.07, pop(0.08))
    elif kind == 'swap':
        put(sfx, a, whoosh(0.45, 0.35)); say(a + 0.25, lines[i])
    elif kind == 'play':
        for s_ in range(1, int(b - a)):
            last = (b - a) - s_ <= 3
            put(sfx, a + s_, heartbeat(0.55) if last else tone(1200, 0.04, 90, 0.09))
    elif kind == 'reveal':
        put(sfx, a, tone(880, 0.7, 5, 0.22) + tone(1320, 0.7, 6, 0.14) + tone(1760, 0.7, 8, 0.07))
    elif kind == 'end':
        say(a + 0.1, 'How many did you find? Comment your score!')
        for n in range(3): put(sfx, a + 0.45 + n * 0.22, pop(0.2))
env = np.convolve(np.abs(voice), np.ones(int(0.25 * SR)) / int(0.25 * SR), 'same')
duck = 1 - 0.55 * np.clip(env / (env.max() + 1e-9) * 4, 0, 1)             # music dips under the voice
mix = music * duck * 0.9 + voice + sfx
mix = mix / max(1.0, np.abs(mix).max() / 0.5)                           # headroom before loudness/limiter
wav = OUT + '.wav'; sf.write(wav, np.stack([mix, mix], 1)[:int(T * SR)].astype(np.float32), SR, subtype='FLOAT')

# ---------------------------------------------------------------- encode
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                        '-i', '-', '-i', wav, '-af', 'loudnorm=I=-14:TP=-2:LRA=9,aresample=48000,alimiter=limit=0.7:attack=1:release=40:level=false',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for n in range(int(T * FPS)):
    enc.stdin.write(frame(n / FPS).convert('RGB').tobytes())
enc.stdin.close(); enc.wait(); os.remove(wav)
print('oddone2', MODE, OUT, round(T, 1), 's', [(p['lv'][0], p['a'], p['b']) for p in puzzles])
