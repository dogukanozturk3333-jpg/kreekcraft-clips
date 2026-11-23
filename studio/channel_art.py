#!/usr/bin/env python3
"""Profile pictures (800x800) and banners (2560x1440, text inside the 1546x423 safe area)
for Brain Warp Lab and Lantern Rain Room, drawn in code at 2x and downsampled.
  python3 -I studio/channel_art.py OUTDIR"""
import sys, os, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)


def F(name, s): return ImageFont.truetype(subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout, s)


def grad(w, h, c0, c1, cx=0.5, cy=0.45, r=0.9):
    y, x = np.mgrid[0:h, 0:w]; d = np.sqrt(((x / w - cx) * w / h) ** 2 + (y / h - cy) ** 2) / r
    d = np.clip(d, 0, 1)[..., None]
    return Image.fromarray((np.array(c0) * (1 - d) + np.array(c1) * d).astype(np.uint8))


def spiral(w, h, cx, cy, turns=7, cols=((46, 230, 214), (155, 60, 255))):
    """Hypnotic two-colour spiral (the optical-illusion 'warp')."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32); dx, dy = x - cx, y - cy
    r = np.sqrt(dx ** 2 + dy ** 2) + 1e-3; a = np.arctan2(dy, dx)
    v = np.sin(a * 2 + np.log(r) * turns)            # logarithmic spiral bands
    t = (np.clip(v * 3, -1, 1) + 1)[..., None] / 2
    img = np.array(cols[0]) * t + np.array(cols[1]) * (1 - t)
    return Image.fromarray(img.astype(np.uint8))


def text_grad(size, txt, fnt, c0, c1, spacing=0):
    m = Image.new('L', size, 0); ImageDraw.Draw(m).text((size[0] // 2, size[1] // 2), txt, font=fnt, fill=255, anchor='mm')
    g = Image.fromarray(np.linspace(c0, c1, size[0]).astype(np.uint8)[None, :, :].repeat(size[1], 0))
    out = Image.new('RGBA', size, (0, 0, 0, 0)); out.paste(g, (0, 0), m); return out


# ---------------- Brain Warp Lab
S = 1600
BG0 = grad(S, S, (70, 30, 140), (14, 8, 36), r=0.75).convert('RGBA')
bg = Image.new('RGBA', (S, S), (0, 0, 0, 0))
# almond eye shape from two circle arcs
R = 1150; off = 820
a = Image.new('L', (S, S), 0); ImageDraw.Draw(a).ellipse([S / 2 - R, S / 2 - off - R, S / 2 + R, S / 2 - off + R], fill=255)
b = Image.new('L', (S, S), 0); ImageDraw.Draw(b).ellipse([S / 2 - R, S / 2 + off - R, S / 2 + R, S / 2 + off + R], fill=255)
eye = Image.fromarray(np.minimum(np.array(a), np.array(b)))
white = Image.new('RGBA', (S, S), (245, 242, 255, 255))
glow = eye.filter(ImageFilter.GaussianBlur(40))
bg.paste(Image.new('RGBA', (S, S), (46, 230, 214, 255)), (0, 0), glow.point(lambda v: v * 0.55))
bg.paste(white, (0, 0), eye)
iris = Image.new('L', (S, S), 0); ImageDraw.Draw(iris).ellipse([S / 2 - 330, S / 2 - 330, S / 2 + 330, S / 2 + 330], fill=255)
iris = Image.fromarray(np.minimum(np.array(iris), np.array(eye)))
bg.paste(spiral(S, S, S / 2, S / 2, turns=6), (0, 0), iris)
d = ImageDraw.Draw(bg)
d.ellipse([S / 2 - 95, S / 2 - 95, S / 2 + 95, S / 2 + 95], fill=(14, 8, 36, 255))
d.ellipse([S / 2 + 20, S / 2 - 80, S / 2 + 75, S / 2 - 25], fill=(255, 255, 255, 255))
k = int(S * 0.74); small = bg.resize((k, k), Image.LANCZOS)
BG0.alpha_composite(small, ((S - k) // 2, (S - k) // 2))
BG0.convert('RGB').resize((800, 800), Image.LANCZOS).save(f'{OUT}/brainwarplab-logo.png')

W2, H2 = 2560, 1440
bn = grad(W2, H2, (48, 20, 98), (10, 6, 26), cy=0.5, r=1.1).convert('RGBA')
sp = spiral(W2, H2, W2 / 2, H2 / 2, turns=4, cols=((70, 40, 150), (22, 12, 52)))
bn = Image.blend(bn, sp.convert('RGBA'), 0.35)
vign = grad(W2, H2, (0, 0, 0), (0, 0, 0)).convert('L')
title = text_grad((1546, 260), 'BRAIN WARP LAB', F('Inter Black', 150), (46, 230, 214), (190, 110, 255))
sh = Image.new('RGBA', (1546, 260), (0, 0, 0, 0)); sh.paste((0, 0, 0, 170), (0, 0), title.getchannel('A').filter(ImageFilter.GaussianBlur(14)))
bn.alpha_composite(sh, (W2 // 2 - 773, H2 // 2 - 175)); bn.alpha_composite(title, (W2 // 2 - 773, H2 // 2 - 180))
ImageDraw.Draw(bn).text((W2 // 2, H2 // 2 + 120), 'DAILY PUZZLES  ·  OPTICAL ILLUSIONS  ·  CAN YOU BEAT LEVEL 3?',
                        font=F('Inter Display SemiBold', 54), fill=(230, 222, 255), anchor='mm')
bn.convert('RGB').save(f'{OUT}/brainwarplab-banner.png')

# ---------------- Lantern Rain Room
S = 1600
bg = grad(S, S, (34, 48, 78), (8, 12, 24), cy=0.55, r=0.8).convert('RGBA')
rng = np.random.default_rng(3)
rain = Image.new('RGBA', (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(rain)
for _ in range(260):
    x, y, L = rng.uniform(-200, S), rng.uniform(-100, S), rng.uniform(60, 180)
    dr.line([x, y, x + L * 0.25, y + L], fill=(170, 200, 255, int(rng.uniform(40, 110))), width=int(rng.uniform(3, 6)))
bg.alpha_composite(rain.filter(ImageFilter.GaussianBlur(1.5)))
cx, cy = S / 2, S / 2 + 60
glow = Image.new('L', (S, S), 0); ImageDraw.Draw(glow).ellipse([cx - 420, cy - 420, cx + 420, cy + 420], fill=255)
bg.paste(Image.new('RGBA', (S, S), (255, 170, 70, 255)), (0, 0), glow.filter(ImageFilter.GaussianBlur(160)).point(lambda v: v * 0.6))
d = ImageDraw.Draw(bg); metal = (28, 22, 18)
d.arc([cx - 90, cy - 470, cx + 90, cy - 300], 180, 360, fill=metal, width=34)          # handle
d.polygon([(cx - 210, cy - 250), (cx + 210, cy - 250), (cx + 120, cy - 360), (cx - 120, cy - 360)], fill=metal)   # cap
d.rounded_rectangle([cx - 240, cy - 270, cx + 240, cy - 220], 20, fill=metal)
d.rounded_rectangle([cx - 200, cy - 220, cx + 200, cy + 250], 40, fill=(255, 196, 92))                             # glass
inner = Image.new('L', (S, S), 0); ImageDraw.Draw(inner).ellipse([cx - 120, cy - 150, cx + 120, cy + 190], fill=255)
bg.paste(Image.new('RGBA', (S, S), (255, 246, 214, 255)), (0, 0), inner.filter(ImageFilter.GaussianBlur(50)))
d = ImageDraw.Draw(bg)
d.polygon([(cx, cy - 60), (cx + 46, cy + 50), (cx, cy + 120), (cx - 46, cy + 50)], fill=(255, 255, 240))           # flame
for x in (cx - 70, cx + 70):
    d.rectangle([x - 14, cy - 220, x + 14, cy + 250], fill=metal)                                                   # frame bars
d.rounded_rectangle([cx - 250, cy + 240, cx + 250, cy + 300], 22, fill=metal)                                       # base
bg.convert('RGB').resize((800, 800), Image.LANCZOS).save(f'{OUT}/lanternrainroom-logo.png')

bn = grad(W2, H2, (30, 42, 70), (6, 9, 18), cy=0.62, r=1.0).convert('RGBA')
rain = Image.new('RGBA', (W2, H2), (0, 0, 0, 0)); dr = ImageDraw.Draw(rain)
for _ in range(900):
    x, y, L = rng.uniform(-300, W2), rng.uniform(-100, H2), rng.uniform(50, 150)
    dr.line([x, y, x + L * 0.22, y + L], fill=(170, 200, 255, int(rng.uniform(25, 80))), width=int(rng.uniform(2, 4)))
bn.alpha_composite(rain.filter(ImageFilter.GaussianBlur(1.2)))
glow = Image.new('L', (W2, H2), 0); ImageDraw.Draw(glow).ellipse([W2 / 2 - 900, H2 / 2 - 260, W2 / 2 + 900, H2 / 2 + 420], fill=255)
bn.paste(Image.new('RGBA', (W2, H2), (255, 165, 70, 255)), (0, 0), glow.filter(ImageFilter.GaussianBlur(220)).point(lambda v: v * 0.45))
d = ImageDraw.Draw(bn)
d.text((W2 // 2, H2 // 2 - 40), 'LANTERN RAIN ROOM', font=F('Inter Display Light', 150), fill=(255, 240, 220), anchor='mm')
d.text((W2 // 2, H2 // 2 + 95), 'Rain  ·  Fire  ·  Calm   —   ambience for sleep, study and slow evenings',
       font=F('Inter Display Light', 46), fill=(215, 205, 190), anchor='mm')
bn.convert('RGB').save(f'{OUT}/lanternrainroom-banner.png')
print('art ->', OUT)
