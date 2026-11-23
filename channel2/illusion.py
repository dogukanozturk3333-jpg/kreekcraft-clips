#!/usr/bin/env python3
"""Brain Warp Lab — optical-illusion Shorts (classic perception effects, our own designs and code).
  python3 -I channel2/illusion.py TYPE OUT.mp4 [--photo IMG]
TYPE:
  spiral     motion aftereffect: stare at a spinning spiral for 15 s, then a still photo seems to melt
  lilac      the "lilac chaser": stare at the cross, the pink dots vanish and a green dot runs around
  troxler    Troxler fading: stare at the dot and the soft colours disappear
  afterimage stare at a colour-inverted photo, then the black-and-white photo looks coloured
Voice: Kokoro (Apache 2.0, offline). Music/sounds: generated here."""
import sys, os, math, argparse, functools, subprocess, numpy as np, soundfile as sf, cv2
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

ap = argparse.ArgumentParser(); ap.add_argument('type'); ap.add_argument('out')
ap.add_argument('--photo', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ambient', 'img', 'short-fireplace.jpg'))
A = ap.parse_args()
W, H, FPS, SR = 1080, 1920, 30, 44100
KOKORO = os.environ.get('KOKORO_DIR', '/tmp/claude-0/-home-user/d825807f-e0e5-55ce-ac85-8ebee4d46dbb/scratchpad/kokoro')
HERE = os.path.dirname(os.path.abspath(__file__))
ACCENT, YEL = (46, 230, 214), (255, 214, 60)
CX, CY = W // 2, 930


@functools.lru_cache(None)
def font(name, s):
    return ImageFont.truetype(subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout, s)

def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2

@functools.lru_cache(None)
def logo():
    lg = Image.open(os.path.join(HERE, '..', 'studio', 'art', 'brainwarplab-logo.png')).convert('RGBA').resize((240, 240), Image.LANCZOS)
    m = Image.new('L', (240, 240), 0); ImageDraw.Draw(m).ellipse([0, 0, 239, 239], fill=255); lg.putalpha(m); return lg

@functools.lru_cache(None)
def text_layer(lines, dark=False):
    """lines: tuple of (y, text, size, colour). Cached RGBA overlay with a soft shadow."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    for y, txt, s, col in lines:
        f = font('Inter Black', s)
        ds.text((W // 2 + 3, y + 4), txt, font=f, fill=(0, 0, 0, 0 if dark else 150), anchor='mm')
        d.text((W // 2, y), txt, font=f, fill=col, anchor='mm')
    sh = sh.filter(ImageFilter.GaussianBlur(6)); sh.alpha_composite(im); return sh

def over(base, layer):
    a = np.asarray(layer, np.float32)[..., 3:4] / 255.0
    return (base * (1 - a) + np.asarray(layer, np.float32)[..., :3] * a)

def brand(base, dark=False):
    l = text_layer(((120, 'BRAIN WARP LAB', 30, (60, 50, 90) if dark else (210, 200, 255)),), dark); return over(base, l)

def ring(base, frac, left, dark=False):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); cx, cy, R = W // 2, 1660, 62
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(20, 12, 44, 220))
    d.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + 360 * frac, fill=YEL, width=11)
    d.text((cx, cy + 2), str(left), font=font('Inter Black', 58), fill=YEL, anchor='mm')
    return over(base, im)

def fix_dot(base, cross=False):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if cross:
        d.rectangle([CX - 26, CY - 4, CX + 26, CY + 4], fill=(0, 0, 0)); d.rectangle([CX - 4, CY - 26, CX + 4, CY + 26], fill=(0, 0, 0))
    else:
        d.ellipse([CX - 18, CY - 18, CX + 18, CY + 18], fill=(255, 255, 255)); d.ellipse([CX - 12, CY - 12, CX + 12, CY + 12], fill=(0, 0, 0))
    return over(base, im)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
RR = np.sqrt((xx - CX) ** 2 + (yy - CY) ** 2) + 1e-3; TH = np.arctan2(yy - CY, xx - CX)
BG = np.zeros((H, W, 3), np.float32) + np.array([16, 10, 36], np.float32)


# ------------------------------------------------------------------ scenes: list of (dur, kind, data)
voice_lines, sfx_marks = [], []
if A.type == 'spiral':
    STARE = 15.0
    photo = np.asarray(Image.open(A.photo).convert('RGB').resize((W, H)), np.float32)
    plan = [(STARE + 1.0, 'spiral'), (6.5, 'photo'), (3.2, 'end')]
    voice_lines = [(0.2, 'Stare at the center of the spiral for fifteen seconds. Do not look away.'),
                   (STARE + 1.15, 'Now look at the picture! It is moving!')]
    title = ((300, 'STARE AT THE CENTER', 74, (255, 255, 255)), (390, 'FOR 15 SECONDS', 54, YEL))
    title2 = ((300, 'NOW LOOK HERE!', 84, (255, 255, 255)), (395, 'is the picture moving?', 50, YEL))
    disk = (RR < 500).astype(np.float32)[..., None]
    edge = np.clip((500 - RR) / 6, 0, 1)[..., None]
elif A.type == 'lilac':
    plan = [(24.0, 'lilac'), (3.2, 'end')]
    voice_lines = [(0.2, 'Stare at the black cross in the middle. Do not move your eyes.'),
                   (9.0, 'Keep staring...'),
                   (14.5, 'Do you see a green dot running around? And where did the pink dots go?')]
    GRAYV = np.array([196, 196, 196], np.float32)
    spr = np.zeros((241, 241), np.float32); cv2.circle(spr, (120, 120), 52, 1.0, -1); spr = cv2.GaussianBlur(spr, (0, 0), 17)
    LIL = np.array([214, 112, 222], np.float32)
elif A.type == 'troxler':
    plan = [(24.0, 'troxler'), (3.2, 'end')]
    voice_lines = [(0.2, 'Stare at the black dot. Do not move your eyes, and try not to blink.'),
                   (10.0, 'Keep going...'), (17.0, 'Are the colours fading away?')]
    rng = np.random.default_rng(5); field = np.zeros((H, W, 3), np.float32) + 150
    for _ in range(14):
        x, y, r = rng.uniform(0, W), rng.uniform(300, 1600), rng.uniform(160, 320)
        col = np.array(rng.choice([[255, 150, 170], [150, 200, 255], [170, 255, 190], [255, 225, 140], [210, 170, 255]]), np.float32)
        m = np.exp(-(((xx - x) ** 2 + (yy - y) ** 2) / (r ** 2)))[..., None]; field = field * (1 - 0.7 * m) + col * 0.7 * m
    field = cv2.GaussianBlur(field, (0, 0), 60)
elif A.type == 'afterimage':
    STARE = 15.0
    img = Image.open(A.photo).convert('RGB').resize((W, H))
    neg = np.asarray(ImageOps.invert(img), np.float32); gray = np.asarray(ImageOps.grayscale(img).convert('RGB'), np.float32)
    plan = [(STARE + 1.0, 'neg'), (6.5, 'gray'), (3.2, 'end')]
    voice_lines = [(0.2, 'Stare at the dot for fifteen seconds. Do not move your eyes.'),
                   (STARE + 1.15, 'Keep looking at the dot. What colours do you see?'),
                   (STARE + 5.0, 'This picture is black and white.')]
else:
    sys.exit('unknown type')

T = sum(d for d, _ in plan); segs, t = [], 0.0
for d, k in plan: segs.append((k, t, t + d)); t += d


def end_screen(t, a, b):
    u = (t - a) / (b - a); im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    k = ease_out_back(u * 4)
    d.text((W // 2, 700), 'DID IT WORK?', font=font('Inter Black', max(10, int(112 * k))), fill=(255, 255, 255), anchor='mm')
    for n, (lab, col) in enumerate((('YES', (88, 220, 130)), ('NO', (255, 80, 100)))):
        kk = ease_out_back((t - a - 0.35 - n * 0.2) * 4)
        if kk > 0.02:
            cx, cy, w2, h2 = W // 2 - 170 + n * 340, 900, 140 * kk, 64 * kk
            d.rounded_rectangle([cx - w2, cy - h2, cx + w2, cy + h2], int(h2), fill=col)
            d.text((cx, cy + 2), lab, font=font('Inter Black', max(10, int(70 * kk))), fill=(20, 12, 40), anchor='mm')
    if u > 0.3:
        d.text((W // 2, 1060), 'Tell us in the comments', font=font('Inter Display SemiBold', 46), fill=ACCENT, anchor='mm')
        lg = logo().copy(); lg.putalpha(lg.getchannel('A').point(lambda v: int(v * min(1, (u - .3) * 4)))); im.alpha_composite(lg, (W // 2 - 120, 1220))
    base = BG.copy() + np.array([20, 6, 40], np.float32) * (yy / H)[..., None]
    return brand(over(base, im))


def frame(t):
    kind, a, b = next(s for s in segs if s[1] <= t < s[2] or s is segs[-1]); u = t - a
    if kind == 'end': return end_screen(t, a, b)
    if kind == 'spiral':
        v = np.sin(2 * TH + 9 * np.log(RR) - t * 6.0)                      # log spiral: rotation reads as endless expansion
        band = (np.clip(v * 6, -1, 1)[..., None] + 1) / 2
        sp = np.array([150, 60, 255], np.float32) * band + np.array([46, 230, 214], np.float32) * (1 - band)
        f = BG * (1 - edge) + sp * edge
        f = over(f, text_layer(title)); f = fix_dot(f)
        if u > 1.0: f = ring(f, 1 - (u - 1.0) / STARE, math.ceil(STARE - (u - 1.0)))
    elif kind == 'photo':
        f = over(photo.copy(), text_layer(title2)); f = fix_dot(f)
    elif kind == 'lilac':
        f = np.zeros((H, W, 3), np.float32) + GRAYV
        miss = int(t / 0.105) % 12; acc = np.zeros((H, W), np.float32)
        for k in range(12):
            if k == miss: continue
            ang = k / 12 * 2 * math.pi - math.pi / 2; x, y = int(CX + 330 * math.cos(ang)), int(CY + 330 * math.sin(ang))
            acc[y - 120:y + 121, x - 120:x + 121] = np.maximum(acc[y - 120:y + 121, x - 120:x + 121], spr)
        f = f * (1 - acc[..., None]) + LIL * acc[..., None]
        lines = ((300, 'STARE AT THE CROSS', 74, (40, 24, 70)), (390, "don't move your eyes", 52, (90, 60, 140))) if t < 14 else \
                ((300, 'A GREEN DOT?', 84, (40, 24, 70)), (390, 'where did the pink go?', 52, (90, 60, 140)))
        f = over(f, text_layer(lines, dark=True)); f = fix_dot(f, cross=True); f = brand(f, dark=True)
        return f
    elif kind == 'troxler':
        f = field.copy()
        f = over(f, text_layer(((300, 'STARE AT THE DOT', 74, (40, 24, 70)), (390, "don't blink", 52, (90, 60, 140))), dark=True))
        f = fix_dot(f); f = brand(f, dark=True)
        if u > 1.0: f = ring(f, 1 - (u - 1.0) / 22.0, max(0, math.ceil(22.0 - (u - 1.0))))
        return f
    elif kind == 'neg':
        f = neg.copy(); band = np.clip(1 - np.abs(np.arange(H) - 345) / 170, 0, 1)[:, None, None] ** 0.6
        f = f * (1 - 0.6 * band)                                      # dark band keeps the title readable on the light negative
        f = over(f, text_layer(((300, 'STARE AT THE DOT', 74, (255, 255, 255)), (390, 'FOR 15 SECONDS', 54, YEL))))
        f = fix_dot(f)
        if u > 1.0: f = ring(f, 1 - (u - 1.0) / STARE, math.ceil(STARE - (u - 1.0)))
    elif kind == 'gray':
        lines = ((300, 'KEEP LOOKING AT THE DOT', 64, (255, 255, 255)),) if u < 3.8 else \
                ((300, 'THIS PHOTO IS', 70, (255, 255, 255)), (395, 'BLACK & WHITE', 84, YEL))
        f = over(gray.copy(), text_layer(lines)); f = fix_dot(f)
    return brand(f)


# ------------------------------------------------------------------ audio
mix = np.zeros(int((T + 1) * SR), np.float32)
def put(at, s, g=1.0):
    i = int(at * SR); j = min(len(mix), i + len(s)); mix[i:j] += g * s[:j - i]
tt = np.arange(len(mix)) / SR
end_a = segs[-1][1]
drone = (np.sin(2 * np.pi * 110 * tt) + 0.6 * np.sin(2 * np.pi * 164.8 * tt + 1) + 0.4 * np.sin(2 * np.pi * 220.5 * tt + 2))
drone *= (0.6 + 0.4 * np.sin(2 * np.pi * tt / 7)) * np.clip(tt / 2, 0, 1) * np.clip((end_a + 0.5 - tt) / 1.0, 0, 1) * 0.035
mix += drone.astype(np.float32)
def shimmer():
    n = int(1.6 * SR); x = np.arange(n) / SR
    return sum(np.sin(2 * np.pi * f * x) * np.exp(-x * 2.5) / (i + 1) for i, f in enumerate((1318, 1760, 2093, 2637))) * 0.12
for k, a, b in segs:
    if k in ('photo', 'gray', 'end'): put(a, shimmer())
from kokoro_onnx import Kokoro
kk = Kokoro(f'{KOKORO}/kokoro.onnx', f'{KOKORO}/voices.bin')
for at, txt in voice_lines + [(end_a + 0.1, 'Did it work? Tell us in the comments!')]:
    s, sr = kk.create(txt, voice='am_michael', speed=1.02, lang='en-us')
    s = cv2.resize(s.astype(np.float32)[None, :], (int(len(s) * SR / sr), 1), interpolation=cv2.INTER_LINEAR)[0]; put(at, s)
mix = mix / max(1.0, np.abs(mix).max() / 0.5)
wav = A.out + '.wav'; sf.write(wav, np.stack([mix, mix], 1)[:int(T * SR)], SR, subtype='FLOAT')

enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                        '-i', '-', '-i', wav, '-af', 'loudnorm=I=-14:TP=-2:LRA=9,aresample=48000,alimiter=limit=0.7:level=false',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', A.out], stdin=subprocess.PIPE)
for n in range(int(T * FPS)):
    enc.stdin.write(np.clip(frame(n / FPS), 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); os.remove(wav); print('illusion', A.type, A.out, round(T, 1), 's')
