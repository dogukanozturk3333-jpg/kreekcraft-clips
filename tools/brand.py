#!/usr/bin/env python3
"""ZEIPAN brand kit: logo, animated logo bug, branded end card, sound stings, intros, channel art.

  python3 tools/brand.py build                      # (re)generate everything in brand/
  python3 tools/brand.py apply IN.mp4 OUT.mp4 [--seam 800] [--end 2.5]
                                                    # brand an already-rendered clip

render.py imports this module and adds the same layers while rendering.

Brand layers on every short:
  * 0.0-1.7 s  logo bug pops in on the facecam/gameplay seam, the ZEIPAN name slides out
               of it and tucks back in (with a soft pop/whoosh), content starts on frame 1
  * whole clip small Z badge stays on the seam (ownership mark, anti-reupload)
  * end card   big logo + name on top, animated FOLLOW @handle button that gets "tapped",
               chime; the campaign's twitch link block stays in the middle untouched
"""
import json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND = os.path.join(ROOT, 'brand')
BUILD = os.path.join(BRAND, 'build')           # generated frame sequences (not committed)
CFG = json.load(open(os.path.join(BRAND, 'brand.json')))
FPS = 30
W, H = 1080, 1920
SS = 3                                          # supersampling for clean edges

def rgb(h, a=255):
    h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)

Y, DK, WH = rgb(CFG['colors']['primary']), rgb(CFG['colors']['dark']), rgb(CFG['colors']['light'])
NAME, HANDLE = CFG['name'], CFG['handle'].upper()

def font(px, upright=False):
    return ImageFont.truetype(CFG['font_upright' if upright else 'font'], max(1, int(px)))

# ---------------------------------------------------------------- easing
def clamp(x): return max(0.0, min(1.0, x))
def prog(f, a, b): return clamp((f - a) / float(b - a))
def out_cubic(x): return 1 - (1 - x) ** 3
def in_cubic(x): return x ** 3
def out_back(x, k=1.9): x -= 1; return 1 + (k + 1) * x ** 3 + k * x ** 2

# ---------------------------------------------------------------- elements
def text_w(txt, f, track=0):
    return sum(f.getlength(c) for c in txt) + track * (len(txt) - 1)

def draw_text(d, x, y, txt, f, fill, track=0, stroke=0, stroke_fill=None):
    """Draw tracked text with (x, y) = left / vertical centre."""
    for c in txt:
        d.text((x, y), c, font=f, fill=fill, anchor='lm', stroke_width=stroke, stroke_fill=stroke_fill)
        x += f.getlength(c) + track

def badge(size, shine=None, shadow=True, angle=0.0, alpha=1.0):
    """Yellow rounded-square Z monogram. Returned image is centred on the badge."""
    size = max(4, int(size))
    S = size * SS; pad = int(S * 0.3)
    im = Image.new('RGBA', (S + 2 * pad, S + 2 * pad), (0, 0, 0, 0))
    box = [pad, pad, pad + S, pad + S]
    if shadow:
        sh = Image.new('L', im.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle([box[0], box[1] + S * .05, box[2], box[3] + S * .05], S * .24, fill=150)
        sh = sh.filter(ImageFilter.GaussianBlur(S * .06))
        im.paste((0, 0, 0, 255), (0, 0), sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, S * .24, fill=DK)
    b = S * .05
    inner = [box[0] + b, box[1] + b, box[2] - b, box[3] - b]
    d.rounded_rectangle(inner, S * .24 - b, fill=Y)
    # speed slashes + Z
    for i, o in enumerate((0.20, 0.29)):
        x0 = pad + S * o
        d.polygon([(x0, pad + S * .30), (x0 + S * .045, pad + S * .30),
                   (x0 - S * .02, pad + S * .70), (x0 - S * .065, pad + S * .70)], fill=DK)
    f = font(S * .74)
    d.text((pad + S * .56, pad + S * .53), 'Z', font=f, fill=DK, anchor='mm')
    if shine is not None and -0.5 < shine < 1.5:   # diagonal light sweep clipped to the face
        m = Image.new('L', im.size, 0); md = ImageDraw.Draw(m)
        cx = pad - S * .4 + shine * S * 1.8
        md.polygon([(cx, pad - S * .2), (cx + S * .22, pad - S * .2),
                    (cx - S * .3, pad + S * 1.2), (cx - S * .52, pad + S * 1.2)], fill=150)
        face = Image.new('L', im.size, 0)
        ImageDraw.Draw(face).rounded_rectangle(inner, S * .24 - b, fill=255)
        m = Image.fromarray((np.asarray(m, np.uint16) * np.asarray(face) // 255).astype(np.uint8))
        im.paste((255, 255, 255, 255), (0, 0), Image.composite(m, Image.new('L', im.size, 0), m))
        # repaint the Z on top so the shine passes "under" it
        ImageDraw.Draw(im).text((pad + S * .56, pad + S * .53), 'Z', font=f, fill=DK, anchor='mm')
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=False)
    out = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    if alpha < 1:
        a = out.getchannel('A').point(lambda v: int(v * alpha)); out.putalpha(a)
    return out

def pill(w, h, fill, outline=None, ow=0):
    S = SS; im = Image.new('RGBA', (int(w * S), int(h * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if outline:
        d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], h * S / 2, fill=outline)
        d.rounded_rectangle([ow * S, ow * S, (w - ow) * S - 1, (h - ow) * S - 1], (h - 2 * ow) * S / 2, fill=fill)
    else:
        d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], h * S / 2, fill=fill)
    return im

def down(im): return im.resize((max(1, im.width // SS), max(1, im.height // SS)), Image.LANCZOS)

def paste_c(canvas, im, cx, cy):
    canvas.alpha_composite(im, (int(round(cx - im.width / 2)), int(round(cy - im.height / 2))))

def with_alpha(im, a):
    if a >= 1: return im
    im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a))); return im

# ---------------------------------------------------------------- logo bug (seam badge)
BUG_W, BUG_H = 560, 200          # canvas; its vertical centre sits on the seam line
BUG_FRAMES = 51

def bug_frame(f):
    c = Image.new('RGBA', (BUG_W, BUG_H), (0, 0, 0, 0))
    size = CFG['bug']['size']; bx = CFG['bug']['x'] + size / 2; by = BUG_H / 2
    # name pill: slides out of the badge (f5-14), holds, tucks back (f36-44)
    r = out_cubic(prog(f, 5, 14)) * (1 - in_cubic(prog(f, 36, 44)))
    if r > 0.01:
        ph = 66; fnt = font(42 * SS)
        tw = text_w(NAME, fnt, 3 * SS) / SS
        full = size / 2 + 26 + tw + 30
        p = pill(full + size / 2, ph, DK, outline=Y, ow=3)
        d = ImageDraw.Draw(p)
        draw_text(d, (size + 26) * SS, ph * SS / 2 + 2 * SS, NAME, fnt, WH, track=3 * SS)
        p = down(p)
        vis = int(size / 2 + (full) * r)
        p = p.crop((0, 0, min(p.width, vis), p.height))
        c.alpha_composite(p, (int(bx - size / 2), int(by + 14 - ph / 2)))
    s = out_back(prog(f, 0, 10)) if f < 10 else 1.0
    ang = -14 * (1 - out_cubic(prog(f, 0, 10)))
    a = 1.0 - (1 - CFG['bug']['opacity']) * prog(f, 44, 50)
    shine = (f - 12) / 10.0 if 12 <= f <= 24 else None
    if s > 0.02:
        paste_c(c, badge(size * s, shine=shine, angle=ang, alpha=a), bx, by)
    return c

# ---------------------------------------------------------------- end card
END_FRAMES = int(2.5 * FPS)
TAP = 34                          # frame the follow button gets tapped

def check(d, x, y, s, fill, w):
    d.line([(x, y), (x + s * .38, y + s * .38), (x + s, y - s * .5)], fill=fill, width=int(w), joint='curve')

def end_frame(f):
    c = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # top: badge + name + tagline
    s = out_back(prog(f, 0, 11))
    if s > 0.02:
        shine = (f - 14) / 12.0 if 14 <= f <= 30 else None
        paste_c(c, badge(210 * s, shine=shine), W / 2, 470)
    t = out_cubic(prog(f, 5, 15))
    if t > 0:
        fnt = font(88 * SS); tw = text_w(NAME, fnt, 8 * SS)
        im = Image.new('RGBA', (int(tw + 40 * SS), 130 * SS), (0, 0, 0, 0))
        draw_text(ImageDraw.Draw(im), 20 * SS, 65 * SS, NAME, fnt, WH, track=8 * SS, stroke=4 * SS, stroke_fill=DK)
        paste_c(c, with_alpha(down(im), t), W / 2, 640 + 28 * (1 - t))
    # bottom: FOLLOW @HANDLE button -> tapped -> FOLLOWING
    t = prog(f, 9, 19)
    if t > 0:
        sc = out_back(t) * (1 - 0.07 * math.sin(math.pi * prog(f, TAP - 2, TAP + 4)))
        bw, bh = 640, 116
        tapped = f >= TAP + 1
        b = pill(bw, bh, DK if tapped else Y, outline=Y if tapped else DK, ow=5)
        d = ImageDraw.Draw(b); fnt = font(50 * SS)
        if tapped:
            label = 'FOLLOWING'; lw = text_w(label, fnt, 2 * SS) + 70 * SS
            x0 = (bw * SS - lw) / 2
            check(d, x0, bh * SS / 2 + 4 * SS, 46 * SS, Y, 11 * SS)
            draw_text(d, x0 + 70 * SS, bh * SS / 2 + 3 * SS, label, fnt, Y, track=2 * SS)
        else:
            label = 'FOLLOW ' + HANDLE; lw = text_w(label, fnt, 2 * SS) + 64 * SS
            x0 = (bw * SS - lw) / 2
            pw = 13 * SS; cx0, cy0 = x0 + 22 * SS, bh * SS / 2
            d.rectangle([cx0 - 22 * SS, cy0 - pw / 2, cx0 + 22 * SS, cy0 + pw / 2], fill=DK)
            d.rectangle([cx0 - pw / 2, cy0 - 22 * SS, cx0 + pw / 2, cy0 + 22 * SS], fill=DK)
            draw_text(d, x0 + 64 * SS, bh * SS / 2 + 3 * SS, label, fnt, DK, track=2 * SS)
        b = down(b)
        b = b.resize((max(1, int(b.width * sc)), max(1, int(b.height * sc))), Image.LANCZOS)
        paste_c(c, b, W / 2, 1290)
        # tap ripple
        rp = prog(f, TAP - 1, TAP + 12)
        if 0 < rp < 1:
            R = 30 + 110 * out_cubic(rp)
            rim = Image.new('RGBA', (int(2 * R + 20) * SS,) * 2, (0, 0, 0, 0))
            ImageDraw.Draw(rim).ellipse([10 * SS, 10 * SS, (2 * R + 10) * SS, (2 * R + 10) * SS],
                                        outline=(255, 255, 255, int(230 * (1 - rp))), width=int(8 * SS))
            paste_c(c, down(rim), W / 2 + 190, 1290)
    return c

# ---------------------------------------------------------------- sound
SR = 48000

def _env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d)

def _noise_band(n, lo, hi, seed=1):
    x = np.random.default_rng(seed).standard_normal(n)
    X = np.fft.rfft(x); fr = np.fft.rfftfreq(n, 1 / SR)
    X[(fr < lo) | (fr > hi)] = 0
    y = np.fft.irfft(X, n); return y / (np.abs(y).max() + 1e-9)

def _add(buf, sig, at):
    i = int(at * SR); j = min(len(buf), i + len(sig)); buf[i:j] += sig[:j - i]

def _tone(f0, f1, dur, decay, amp):
    n = int(dur * SR); t = np.arange(n) / SR
    fr = f0 + (f1 - f0) * np.minimum(1, t / 0.06)
    return amp * np.sin(2 * np.pi * np.cumsum(fr) / SR) * _env(n, 0.003, decay)

def whoosh(dur, amp, seed=1):
    n = int(dur * SR); t = np.arange(n) / SR
    e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return amp * _noise_band(n, 400, 7000, seed) * e

def write_wav(path, x):
    x = np.clip(x, -1, 1); st = np.repeat((x * 32767).astype(np.int16)[:, None], 2, axis=1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())

def make_sounds():
    s = np.zeros(int(1.0 * SR))
    _add(s, whoosh(0.28, 0.35), 0.0)
    _add(s, _tone(70, 55, 0.3, 0.12, 0.7), 0.06)          # thump
    _add(s, _tone(700, 1500, 0.2, 0.06, 0.45), 0.06)      # pop
    for k, fq in enumerate((2637, 3520, 4186)):           # sparkle with the shine
        _add(s, _tone(fq, fq, 0.3, 0.09, 0.10), 0.40 + k * 0.045)
    write_wav(os.path.join(BRAND, 'sting.wav'), s)
    e = np.zeros(int(2.5 * SR))
    _add(e, whoosh(0.35, 0.30, 2), 0.0)
    _add(e, _tone(600, 1200, 0.2, 0.05, 0.35), 0.33)      # button pops in
    _add(e, _noise_band(int(0.03 * SR), 2000, 9000, 3) * 0.4 * _env(int(0.03 * SR), 0.001, 0.008), TAP / FPS)
    _add(e, _tone(1046.5, 1046.5, 0.9, 0.35, 0.32), TAP / FPS + 0.03)   # chime C6
    _add(e, _tone(1568, 1568, 0.9, 0.45, 0.28), TAP / FPS + 0.15)       # G6
    write_wav(os.path.join(BRAND, 'end.wav'), e)

# ---------------------------------------------------------------- intros + channel art
def bg(w, h, glow=1.0, stripes=True):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot((xx - w / 2) / w, (yy - h / 2) / h)
    g = np.clip(1 - r * 1.6, 0, 1) ** 2 * glow
    base = np.array(DK[:3], np.float32)
    col = base + (np.array(Y[:3], np.float32) - base) * (g[..., None] * 0.22)
    if stripes:
        band = ((xx + yy) // max(8, w // 48)) % 2 == 0
        col = col + band[..., None] * 4.0
    return Image.fromarray(np.clip(col, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')

def title_frame(w, h, f, n, tag=True):
    u = min(w, h)
    c = bg(w, h)
    if f < 3:   # punchy flash on the cut
        c.alpha_composite(Image.new('RGBA', (w, h), Y[:3] + (int(255 * (1 - f / 3)),)))
    s = out_back(prog(f, 0, 12))
    zoom = 1 + 0.06 * prog(f, 0, n)
    cy = h / 2 - u * 0.12
    if s > 0.02:
        paste_c(c, badge(u * 0.34 * s * zoom, shine=(f - 14) / 12 if 14 <= f <= 30 else None), w / 2, cy)
    t = out_cubic(prog(f, 6, 16))
    if t > 0:
        fnt = font(u * 0.15 * SS * zoom); tw = text_w(NAME, fnt, u * 0.012 * SS)
        im = Image.new('RGBA', (int(tw + u * .1 * SS), int(u * .25 * SS)), (0, 0, 0, 0))
        draw_text(ImageDraw.Draw(im), u * .05 * SS, u * .125 * SS, NAME, fnt, WH, track=u * 0.012 * SS)
        im = down(im); x0 = int(w / 2 - im.width / 2)      # wipe in from the left
        im = im.crop((0, 0, max(1, int(im.width * t)), im.height))
        c.alpha_composite(im, (x0, int(cy + u * 0.30 - im.height / 2)))
    t2 = out_cubic(prog(f, 12, 22))
    if tag and t2 > 0:
        fnt = font(u * 0.042 * SS, upright=True); tg = CFG['tagline']
        tw = text_w(tg, fnt, u * 0.012 * SS)
        im = Image.new('RGBA', (int(tw + 20 * SS), int(u * 0.08 * SS)), (0, 0, 0, 0))
        draw_text(ImageDraw.Draw(im), 10 * SS, u * 0.04 * SS, tg, fnt, Y, track=u * 0.012 * SS)
        paste_c(c, with_alpha(down(im), t2), w / 2, cy + u * 0.43 + 20 * (1 - t2))
    fo = prog(f, n - 5, n)          # quick dip to black into the content
    if fo > 0:
        c.alpha_composite(Image.new('RGBA', (w, h), (0, 0, 0, int(255 * fo))))
    return c.convert('RGB')

def make_intro(path, w, h, dur):
    n = int(dur * FPS); tmp = os.path.join(BUILD, f'intro_{w}x{h}'); os.makedirs(tmp, exist_ok=True)
    for f in range(n):
        title_frame(w, h, f, n).save(f'{tmp}/{f:03d}.png')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', f'{tmp}/%03d.png',
                    '-i', os.path.join(BRAND, 'sting.wav'),
                    '-filter_complex', f'[1:a]apad,atrim=0:{dur},afade=t=out:st={dur - 0.2}:d=0.2[a]',
                    '-map', '0:v', '-map', '[a]', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p',
                    '-r', str(FPS), '-c:a', 'aac', '-b:a', '192k', '-t', str(dur), '-movflags', '+faststart', path],
                   check=True)

def make_art():
    art = os.path.join(BRAND, 'art'); os.makedirs(art, exist_ok=True)
    badge(1024, shadow=False).save(os.path.join(art, 'logo.png'))
    # profile picture (all platforms crop to a circle -> keep the badge inside it)
    a = bg(800, 800, stripes=False); paste_c(a, badge(470), 400, 400); a.convert('RGB').save(os.path.join(art, 'avatar-800.png'))
    # YouTube banner 2560x1440, everything inside the 1546x423 always-visible safe area
    b = bg(2560, 1440, glow=1.3)
    fnt = font(190 * SS); tw = text_w(NAME, fnt, 14 * SS)
    nm = Image.new('RGBA', (int(tw + 40 * SS), 260 * SS), (0, 0, 0, 0))
    draw_text(ImageDraw.Draw(nm), 20 * SS, 130 * SS, NAME, fnt, WH, track=14 * SS)
    nm = down(nm)
    fnt = font(54 * SS, upright=True); tg = CFG['tagline']; tw = text_w(tg, fnt, 10 * SS)
    tl = Image.new('RGBA', (int(tw + 20 * SS), 90 * SS), (0, 0, 0, 0))
    draw_text(ImageDraw.Draw(tl), 10 * SS, 45 * SS, tg, fnt, Y, track=10 * SS)
    tl = down(tl)
    bs, gap = 320, 50                                   # badge | gap | name over tagline
    total = bs + gap + max(nm.width, tl.width)
    x0 = 1280 - total / 2
    paste_c(b, badge(bs), x0 + bs / 2, 720)
    b.alpha_composite(nm, (int(x0 + bs + gap - 20), int(675 - nm.height / 2)))
    b.alpha_composite(tl, (int(x0 + bs + gap), int(800 - tl.height / 2)))
    b.convert('RGB').save(os.path.join(art, 'youtube-banner-2560x1440.png'))
    # preview sheet of the animated pieces (for review)
    sheet = Image.new('RGBA', (BUG_W * 2, BUG_H * 2), (40, 40, 48, 255))
    for i, f in enumerate((4, 10, 24, 50)):
        sheet.alpha_composite(bug_frame(f), ((i % 2) * BUG_W, (i // 2) * BUG_H))
    sheet.convert('RGB').save(os.path.join(art, 'preview-bug.png'))

# ---------------------------------------------------------------- build / ffmpeg glue
BUG_SEQ = os.path.join(BUILD, 'bug', '%03d.png')
END_SEQ = os.path.join(BUILD, 'end', '%03d.png')

def build(force=False):
    stamp = os.path.join(BUILD, '.ok')
    src_t = max(os.path.getmtime(__file__), os.path.getmtime(os.path.join(BRAND, 'brand.json')))
    if not force and os.path.exists(stamp) and os.path.getmtime(stamp) >= src_t:
        return
    for sub, n, fn in (('bug', BUG_FRAMES, bug_frame), ('end', END_FRAMES, end_frame)):
        d = os.path.join(BUILD, sub); os.makedirs(d, exist_ok=True)
        for f in range(n):
            fn(f).save(os.path.join(d, f'{f:03d}.png'))
    make_sounds()
    make_art()
    make_intro(os.path.join(BRAND, 'intro-vertical-1080x1920.mp4'), 1080, 1920, 1.2)
    make_intro(os.path.join(BRAND, 'intro-wide-1920x1080.mp4'), 1920, 1080, 2.0)
    open(stamp, 'w').write('ok')
    print('brand kit built in', BRAND, flush=True)

def inputs():
    """Extra ffmpeg inputs, in this order: bug frames, end-card frames, sting, end sound."""
    build()
    return ['-framerate', str(FPS), '-i', BUG_SEQ, '-framerate', str(FPS), '-i', END_SEQ,
            '-i', os.path.join(BRAND, 'sting.wav'), '-i', os.path.join(BRAND, 'end.wav')]

def filters(base, vin, ain, vout, aout, D, seam):
    """Filtergraph adding the brand layers. base = index of the first input from inputs().
    D = content length (end card starts at D)."""
    y = int(seam - BUG_H / 2)
    return (f"[{base}:v]format=rgba[zb];"
            f"[{base + 1}:v]format=rgba,setpts=PTS-STARTPTS+{D:.3f}/TB[ze];"
            f"[{vin}][zb]overlay=x=0:y={y}:eof_action=repeat:enable='lt(t,{D:.3f})'[zv1];"
            f"[zv1][ze]overlay=x=0:y=0:eof_action=pass,format=yuv420p[{vout}];"
            f"[{base + 2}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.42[zs];"
            f"[{base + 3}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume=0.5,"
            f"adelay={int(D * 1000)}:all=1[zn];"
            f"[{ain}][zs][zn]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.95:level=disabled[{aout}]")

def apply(src, dst, seam=800, end=2.5):
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src],
                               capture_output=True, text=True, check=True).stdout)
    D = dur - end
    fc = filters(1, '0:v', '0:a', 'v', 'a', D, seam)
    tmp = dst + '.tmp.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src] + inputs() +
                   ['-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-t', f'{dur}',
                    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-maxrate', '11M', '-bufsize', '22M',
                    '-profile:v', 'high', '-level', '4.1', '-r', '30', '-g', '60', '-pix_fmt', 'yuv420p',
                    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', tmp], check=True)
    os.replace(tmp, dst)
    print('branded', dst, flush=True)

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] == 'build':
        build(force=True)
    elif a[0] == 'apply':
        kw = {}
        if '--seam' in a: kw['seam'] = int(a[a.index('--seam') + 1])
        if '--end' in a: kw['end'] = float(a[a.index('--end') + 1])
        apply(a[1], a[2], **kw)
    else:
        sys.exit(__doc__)
