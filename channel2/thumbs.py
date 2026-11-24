#!/usr/bin/env python3
"""Brain Warp Lab thumbnails (1280x720, < 2 MB) built from REAL frames of the videos.
  python3 -I channel2/thumbs.py episode N OUT.jpg          # collage of the episode's puzzles + big hook
  python3 -I channel2/thumbs.py short VIDEO.mp4 KIND OUT.jpg [--line1 ..] [--line2 ..]
Shorts thumbnails keep the important part inside the centre 405 px (YouTube crops Shorts to 9:16)."""
import sys, os, subprocess, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bwlkit import font, logo, background, YEL, ACCENT, RED, MAGENTA
from PIL import Image, ImageDraw, ImageFilter, ImageOps

W, H = 1280, 720
SCR = os.environ.get('BWL_SCRATCH', '/tmp/claude-0/-home-user/d825807f-e0e5-55ce-ac85-8ebee4d46dbb/scratchpad/episodes')


def grab(video, t, box=None):
    tmp = tempfile.mktemp(suffix='.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(t), '-i', video, '-frames:v', '1', tmp], check=True)
    im = Image.open(tmp).convert('RGB'); os.remove(tmp)
    return im.crop(box) if box else im


def outlined(d, xy, text, f, fill, stroke=10, anchor='mm'):
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(10, 6, 24))


def arrow(d, x0, y0, x1, y1, col=RED, w=22):
    import math
    d.line([(x0, y0), (x1, y1)], fill=col, width=w)
    a = math.atan2(y1 - y0, x1 - x0); L = 60
    for s in (-0.5, 0.5):
        d.line([(x1, y1), (x1 - L * math.cos(a + s), y1 - L * math.sin(a + s))], fill=col, width=w)


def card(im, angle, size):
    im = im.resize(size, Image.LANCZOS)
    b = Image.new('RGBA', (size[0] + 24, size[1] + 24), (255, 255, 255, 255)); b.paste(im, (12, 12))
    sh = Image.new('RGBA', b.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([0, 0, *b.size], fill=(0, 0, 0, 160))
    return b.rotate(angle, expand=True, resample=Image.BICUBIC), sh.rotate(angle, expand=True).filter(ImageFilter.GaussianBlur(14))


def episode(n, out):
    work = os.path.join(SCR, f'ep{n:02d}'); base = 100 * n
    bg = background(4.0).resize((W, int(W * 1920 / 1080))).crop((0, 400, W, 400 + H)).convert('RGBA')
    picks = [(f'odd-{base + 3}.mp4', 12.0), (f'col-{base + 2}.mp4', 5.5), (f'diff-{base + 1}.mp4', 6.0), (f'math-{base + 1}.mp4', 6.0)]   # before any answer is shown
    box = (60, 420, 1020, 1420)
    spots = [((690, -10), -6), ((930, 140), 5), ((700, 330), 4), ((960, 420), -5)]
    for (name, t), ((x, y), ang) in zip(picks, spots):
        p = os.path.join(work, name)
        if not os.path.exists(p): continue
        c, s = card(grab(p, t, box), ang, (300, 312))
        bg.alpha_composite(s, (x + 10, y + 16)); bg.alpha_composite(c, (x, y))
    d = ImageDraw.Draw(bg)
    outlined(d, (40, 70), f'EPISODE {n}', font('Inter Black', 46), ACCENT, 8, 'lm')
    outlined(d, (40, 185), '30 BRAIN', font('Inter Black', 150), (255, 255, 255), 12, 'lm')
    outlined(d, (40, 335), 'PUZZLES', font('Inter Black', 150), YEL, 12, 'lm')
    d.rounded_rectangle([40, 440, 600, 530], 45, fill=RED)
    d.text((320, 486), 'CAN YOU SCORE 74?', font=font('Inter Black', 50), fill=(255, 255, 255), anchor='mm')
    arrow(d, 560, 600, 700, 520)
    bg.alpha_composite(logo(110), (40, 585))
    bg.convert('RGB').save(out, quality=90); print('thumb', out)


def short(video, kind, out, line1=None, line2=None):
    presets = {'flag': ('STARE AT', 'THE DOT', 6.0), 'hermann': ('COUNT THE', 'BLACK DOTS', 6.0), 'lines': ('WHICH IS', 'LONGER?', 3.0),
               'lilac': ('A GREEN', 'DOT?!', 8.0), 'math': ('CAN YOU', 'SOLVE IT?', 6.0), 'diff': ('FIND 3', 'DIFFERENCES', 8.0),
               'odd': ('FIND THE', 'ODD ONE', 3.0), 'checker': ('A OR B?', 'WHICH IS DARKER', 4.0),
               'cafe': ('ARE THEY', 'STRAIGHT?', 4.0), 'ebbinghaus': ('WHICH ONE IS', 'BIGGER?', 4.0), 'col': ('FIND THE', 'COLOR', 3.0), 'txt': ('FIND THE', 'ODD LETTER', 3.0)}
    a, b, t = presets.get(kind, ('CAN YOU', 'SEE IT?', 5.0))
    a, b = line1 or a, line2 or b
    fr = grab(video, t)                                       # 1080x1920
    bg = ImageOps.fit(fr, (W, H), centering=(0.5, 0.5)).filter(ImageFilter.GaussianBlur(18)).convert('RGBA')
    bg = Image.blend(bg, Image.new('RGBA', (W, H), (14, 8, 36, 255)), 0.45)
    mid = fr.resize((405, 720), Image.LANCZOS).convert('RGBA')
    bg.alpha_composite(mid, (W // 2 - 202, 0))
    shade = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(shade)
    for y in range(0, 200): sd.line([(0, y), (W, y)], fill=(10, 6, 24, int(235 * (1 - y / 200) ** 0.6)))
    for y in range(540, H): sd.line([(0, y), (W, y)], fill=(10, 6, 24, int(235 * ((y - 540) / 180) ** 0.6)))
    bg.alpha_composite(shade)
    d = ImageDraw.Draw(bg)
    outlined(d, (W // 2, 122), a, font('Inter Black', 78), (255, 255, 255), 10)
    outlined(d, (W // 2, 640), b, font('Inter Black', 78 if len(b) < 10 else 62), YEL, 10)
    # brand: logo badge + name inside the 9:16 band, so every thumbnail reads as Brain Warp Lab
    bg.alpha_composite(logo(46), (W // 2 - 128, 12))
    d.text((W // 2 - 74, 35), 'BRAIN WARP LAB', font=font('Inter Black', 26), fill=(255, 255, 255), anchor='lm',
           stroke_width=4, stroke_fill=(10, 6, 24))
    bg.alpha_composite(logo(96), (24, H - 120))
    bg.convert('RGB').save(out, quality=90); print('thumb', out)


if __name__ == '__main__':
    if sys.argv[1] == 'episode':
        episode(int(sys.argv[2]), sys.argv[3])
    else:
        args = sys.argv[2:]; kw = {}
        for k in ('--line1', '--line2'):
            if k in args: i = args.index(k); kw[k[2:]] = args[i + 1]; del args[i:i + 2]
        short(args[0], args[1], args[2], **kw)
