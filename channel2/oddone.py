#!/usr/bin/env python3
"""Brain Warp Lab — "Find the odd one out" Shorts, fully generated (emoji grid + timer + reveal + voice).
Every seed gives a new video: 3 levels (easy / medium / hard), each a grid of one emoji with a single
look-alike hidden in it, a countdown with ticks, then the answer is circled.
  python3 -I channel2/oddone.py SEED OUT.mp4
Emoji art: Noto Color Emoji (SIL Open Font License). Voice: Kokoro (Apache 2.0), offline."""
import sys, os, math, random, subprocess, numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SEED, OUT = int(sys.argv[1]), sys.argv[2]
W, H, FPS, SR = 1080, 1920, 30, 24000
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
KOKORO = os.environ.get('KOKORO_DIR', '/tmp/claude-0/-home-user/d825807f-e0e5-55ce-ac85-8ebee4d46dbb/scratchpad/kokoro')
FB = 'Inter Black'
rnd = random.Random(SEED)

PAIRS = {   # (majority, odd) look-alikes, grouped by how hard they are to tell apart
    'easy':   ['❤️🧡', '🔵🟣', '🍊🍑', '🌕🌝', '📕📙', '⚽🏐', '🐻🐨', '🐮🐷', '🐟🐠', '🍓🍒', '🚗🚕', '💙💜', '🍏🍎', '🐝🐞', '🍋🍊'],
    'medium': ['🍎🍅', '🦁🐯', '⭐🌟', '🌻🌼', '😴😪', '🐸🐢', '🍩🥯', '🐶🐕', '🌲🌳', '🙂🙃', '🐭🐹', '😆😂', '🙄😒'],
    'hard':   ['😀😃', '😄😁', '😐😑', '🙈🙊', '😺😸', '😮😯', '😟🙁', '😊🙂', '😃😄', '🌙🌛', '😗😙', '😶😐'],
}
LEVELS = [('easy', 5, 7, 5.0, (90, 220, 120)), ('medium', 6, 9, 6.0, (255, 205, 60)), ('hard', 7, 11, 7.0, (255, 80, 90))]
REVEAL, END = 1.7, 2.6
GRID = (90, 470, 990, 1420)          # x0, y0, x1, y1 — clear of the Shorts buttons and caption


def split2(s):                       # a pair string -> two emoji (some carry a variation selector)
    import unicodedata
    out, cur = [], ''
    for ch in s:
        if cur and unicodedata.category(ch) not in ('Mn', 'Cf') and ord(ch) not in (0xFE0F, 0x200D):
            out.append(cur); cur = ''
        cur += ch
    out.append(cur); return out


_cache = {}
def glyph(e, size):
    if (e, size) not in _cache:
        f = ImageFont.truetype(EMOJI, 109)
        im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((80, 80), e, font=f, embedded_color=True, anchor='mm')
        im = im.crop(im.getbbox()).resize((size, size), Image.LANCZOS)
        _cache[(e, size)] = im
    return _cache[(e, size)]


import functools
@functools.lru_cache(None)
def font(name, s): return ImageFont.truetype(subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout, s)


def background():
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(-1, 1, W)[None, :]
    top, bot = np.array([22, 14, 48]), np.array([52, 20, 84])
    g = top + (bot - top) * y[..., None]
    v = 1 - 0.35 * (x ** 2 + (y - 0.45) ** 2)[..., None]
    return Image.fromarray(np.clip(g * v, 0, 255).astype(np.uint8))


BG = background()


def header(d, lvl_name, color, idx):
    d.text((W // 2, 170), 'BRAIN WARP LAB', font=font('Inter Display Medium', 30), fill=(200, 190, 255), anchor='mm')
    d.text((W // 2, 280), 'FIND THE ODD ONE OUT', font=font(FB, 70), fill=(255, 255, 255), anchor='mm')
    t = f'LEVEL {idx + 1}  ·  {lvl_name.upper()}'
    f = font(FB, 44); w = d.textlength(t, font=f)
    d.rounded_rectangle([W // 2 - w / 2 - 30, 340, W // 2 + w / 2 + 30, 410], 35, fill=color)
    d.text((W // 2, 376), t, font=f, fill=(20, 12, 40), anchor='mm')


def level_frame(lv, idx, cells, odd, reveal):
    name, cols, rows, dur, color = lv
    im = BG.copy(); d = ImageDraw.Draw(im); header(d, name, color, idx)
    x0, y0, x1, y1 = GRID
    d.rounded_rectangle([x0 - 34, y0 - 30, x1 + 34, y1 + 30], 44, fill=(240, 235, 252))   # light card: every emoji reads clearly
    cw = (x1 - x0) / cols; ch = (y1 - y0) / rows; s = int(min(cw, ch) * 0.8)
    for r in range(rows):
        for c in range(cols):
            e = cells[r][c]; g = glyph(e, s)
            if reveal and (r, c) != odd:
                g = g.copy(); g.putalpha(g.getchannel('A').point(lambda a: a * 0.18))
            im.paste(g, (int(x0 + c * cw + (cw - s) / 2), int(y0 + r * ch + (ch - s) / 2)), g)
    if reveal:
        r, c = odd; cx, cy = x0 + (c + .5) * cw, y0 + (r + .5) * ch; R = s * 0.75
        for k, a in ((10, 90), (6, 255)):
            d.ellipse([cx - R - k, cy - R - k, cx + R + k, cy + R + k], outline=(255, 60, 200, a), width=k)
        d.text((W // 2, 1500), 'FOUND IT?', font=font(FB, 64), fill=color, anchor='mm')
    return im


def end_frame():
    im = BG.copy(); d = ImageDraw.Draw(im)
    d.text((W // 2, 170), 'BRAIN WARP LAB', font=font('Inter Display Medium', 30), fill=(200, 190, 255), anchor='mm')
    d.text((W // 2, 760), 'HOW MANY', font=font(FB, 110), fill=(255, 255, 255), anchor='mm')
    d.text((W // 2, 880), 'DID YOU FIND?', font=font(FB, 110), fill=(255, 255, 255), anchor='mm')
    d.text((W // 2, 1030), 'Comment 1, 2 or 3', font=font('Inter Display SemiBold', 58), fill=(46, 230, 214), anchor='mm')
    return im


# ---- build the three puzzles
puzzles = []
for idx, lv in enumerate(LEVELS):
    name, cols, rows = lv[:3]
    order = PAIRS[name][:]; random.Random(4242 + idx).shuffle(order)   # fixed order: consecutive seeds never repeat a pair
    a, b = split2(order[(SEED - 1) % len(order)])
    if rnd.random() < 0.5: a, b = b, a
    odd = (rnd.randrange(1, rows - 1), rnd.randrange(cols - 1))   # never the right column: the Shorts buttons sit there
    cells = [[b if (r, c) == odd else a for c in range(cols)] for r in range(rows)]
    puzzles.append((lv, idx, cells, odd))

# ---- timeline
segs, t = [], 0.0
for p in puzzles:
    segs.append(('play', t, t + p[0][3], p)); t += p[0][3]
    segs.append(('reveal', t, t + REVEAL, p)); t += REVEAL
segs.append(('end', t, t + END, None)); T = t + END

# ---- audio: voice + ticks + reveal chime (all generated here)
from kokoro_onnx import Kokoro
k = Kokoro(f'{KOKORO}/kokoro.onnx', f'{KOKORO}/voices.bin')
mix = np.zeros(int((T + 1) * SR), np.float32)
def put(at, s, g=1.0):
    i = int(at * SR); mix[i:i + len(s)] += g * s[:len(mix) - i]
def say(at, txt):
    s, _ = k.create(txt, voice='am_michael', speed=1.12, lang='en-us'); put(at, s)
def tone(f, dur, decay, g):
    tt = np.arange(int(dur * SR)) / SR; return g * np.sin(2 * np.pi * f * tt) * np.exp(-tt * decay)
lines = {0: 'Find the odd one out!', 1: 'Level two.', 2: 'Level three. Only a few people find this one.'}
for kind, a, b, p in segs:
    if kind == 'play':
        say(a + 0.1, lines[p[1]])
        for s in range(1, int(b - a)):
            last = (b - a) - s <= 3
            put(a + s, tone(1500 if last else 1100, 0.05, 80, 0.20 if last else 0.12))
    elif kind == 'reveal':
        put(a, tone(880, 0.6, 6, 0.25) + tone(1320, 0.6, 7, 0.15))
    elif kind == 'end':
        say(a + 0.1, 'How many did you find? Tell me in the comments.')
wav = OUT + '.wav'; sf.write(wav, mix[:int(T * SR)], SR)

# ---- video
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                        '-i', '-', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1.5,aresample=48000',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
base_cache = {}
for i in range(int(T * FPS)):
    t = i / FPS
    kind, a, b, p = next(s for s in segs if s[1] <= t < s[2] or s is segs[-1])
    key = (kind, id(p))
    if key not in base_cache:
        base_cache[key] = np.array(end_frame() if kind == 'end' else level_frame(*p, reveal=(kind == 'reveal')))
    fr = base_cache[key]
    if kind == 'play':                               # shrinking timer bar + seconds left
        fr = fr.copy(); frac = 1 - (t - a) / (b - a); left = math.ceil(b - t)
        col = np.array(p[0][4]) if left > 3 else np.array([255, 70, 80])
        bx0, by0, bw, bh = 140, 1480, 800, 26
        fr[by0:by0 + bh, bx0:bx0 + bw] = (fr[by0:by0 + bh, bx0:bx0 + bw] * 0.4 + 30).astype(np.uint8)
        fr[by0:by0 + bh, bx0:bx0 + int(bw * frac)] = col
        im = Image.fromarray(fr); ImageDraw.Draw(im).text((W // 2, 1570), str(left), font=font(FB, 72), fill=tuple(int(c) for c in col), anchor='mm')
        fr = np.array(im)
    enc.stdin.write(fr.tobytes())
enc.stdin.close(); enc.wait(); os.remove(wav)
print('oddone', OUT, round(T, 1), 's', [(p[0][0], ''.join(sorted({p[2][0][0], p[2][p[3][0]][p[3][1]]}))) for p in puzzles])
