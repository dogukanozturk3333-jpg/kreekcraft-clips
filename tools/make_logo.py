#!/usr/bin/env python3
"""Draws the Zeipan logo (assets/logo.png) from brand.yaml colors: purple pill, yellow play mark, white wordmark."""
import os, yaml
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = yaml.safe_load(open(os.path.join(REPO, 'brand.yaml')))
col = lambda h: tuple(int(h.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
purple, yellow = col(B['frame']['color']), col(B['frame']['accent'])
name = B['channel']['name'].strip().upper()

S = 4                                   # supersample for smooth edges
H = 170 * S
font = ImageFont.truetype('/usr/share/fonts/opentype/inter/Inter-BlackItalic.otf', 112 * S)
tw = font.getbbox(name)[2] - font.getbbox(name)[0]
icon = 120 * S
W = 36 * S + icon + 28 * S + tw + 48 * S
img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([0, 0, W - 1, H - 1], radius=H // 2 - 6 * S, fill=purple + (255,), outline=(255, 255, 255, 255), width=7 * S)
# play mark: yellow rounded square with a dark triangle
x0, y0 = 30 * S, (H - icon) // 2
d.rounded_rectangle([x0, y0, x0 + icon, y0 + icon], radius=30 * S, fill=yellow + (255,))
cx, cy = x0 + icon // 2 + 6 * S, y0 + icon // 2
r = 34 * S
d.polygon([(cx - r * 0.75, cy - r), (cx - r * 0.75, cy + r), (cx + r, cy)], fill=(24, 16, 40, 255))
bb = font.getbbox(name)
d.text((x0 + icon + 26 * S - bb[0], (H - (bb[3] - bb[1])) // 2 - bb[1]), name, font=font, fill=(255, 255, 255, 255))
img = img.resize((W // S, H // S), Image.LANCZOS)
out = os.path.join(REPO, 'assets', 'logo.png')
img.save(out)
print(out, img.size)
