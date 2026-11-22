import numpy as np, subprocess, sys, os, math
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import soundfile as sf
from kokoro_onnx import Kokoro
D, M = sys.argv[1], sys.argv[2]
W, H, FPS = 1080, 1920, 30
FB = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
# --- a colourful scene drawn in code (no outside images)
def scene(w=900, h=1200):
    im = Image.new('RGB', (w, h)); d = ImageDraw.Draw(im)
    for y in range(h):                      # sky gradient
        t = y / h; d.line([(0, y), (w, y)], fill=(int(40 + 60*t), int(120 + 80*t), int(235 - 20*t)))
    d.ellipse([600, 120, 820, 340], fill=(255, 205, 40))                        # sun
    d.polygon([(0, 700), (250, 520), (520, 700)], fill=(120, 120, 135))           # mountains
    d.polygon([(300, 700), (620, 470), (900, 700)], fill=(140, 140, 150))
    d.ellipse([-300, 620, 600, 1300], fill=(60, 175, 70))                        # hills
    d.ellipse([350, 650, 1250, 1350], fill=(40, 150, 55))
    d.rectangle([0, 1000, w, h], fill=(50, 160, 60))
    d.rectangle([140, 760, 420, 980], fill=(215, 40, 40))                       # red house
    d.polygon([(110, 770), (280, 630), (450, 770)], fill=(120, 60, 30))
    d.rectangle([250, 880, 310, 980], fill=(90, 50, 20))
    for cx in (640, 760):                                                    # trees
        d.rectangle([cx - 12, 860, cx + 12, 960], fill=(110, 70, 30))
        d.ellipse([cx - 70, 740, cx + 70, 880], fill=(30, 120, 40))
    for i, c in enumerate([(230, 50, 50), (250, 150, 30), (250, 230, 40), (60, 170, 70), (50, 110, 230), (140, 60, 200)]):
        d.arc([60 - i*22, 260 - i*22, 560 + i*22, 760 + i*22], 200, 340, fill=c, width=22)   # rainbow
    return im
sc = scene(); neg = ImageOps.invert(sc); gray = ImageOps.grayscale(sc).convert('RGB')
def font(s): return ImageFont.truetype(FB, s)
def ctext(d, y, txt, s, fill=(255, 255, 255), stroke=0, sf_=(0, 0, 0)):
    f = font(s); d.text((W / 2, y), txt, font=f, fill=fill, anchor='mm', stroke_width=stroke, stroke_fill=sf_)
STARE, GRAY, END = 16.0, 7.0, 3.5
T = 1.2 + STARE + GRAY + END
IX, IY = (W - 900) // 2, 420
def frame(t):
    c = Image.new('RGB', (W, H), (12, 12, 16)); d = ImageDraw.Draw(c)
    if t < 1.2 + STARE:
        c.paste(neg, (IX, IY))
        ctext(d, 200, 'THIS WILL TRICK', 84, (255, 229, 0)); ctext(d, 300, 'YOUR BRAIN', 84, (255, 229, 0))
        left = max(0, math.ceil(1.2 + STARE - t))
        ctext(d, 1730, 'STARE AT THE DOT', 64)
        ctext(d, 1820, f'{left}', 72, (255, 229, 0))
    elif t < 1.2 + STARE + GRAY:
        c.paste(gray, (IX, IY))
        ctext(d, 250, 'KEEP LOOKING', 84, (255, 229, 0))
        ctext(d, 1730, 'WHAT COLOURS', 64); ctext(d, 1810, 'DO YOU SEE?', 64)
    else:
        c.paste(gray, (IX, IY))
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 150)); c.paste(ov, (0, 0), ov); d = ImageDraw.Draw(c)
        ctext(d, 900, 'THIS PICTURE IS', 80); ctext(d, 1010, 'BLACK & WHITE', 96, (255, 229, 0))
        ctext(d, 1150, 'your brain added the colours', 44)
    if t < 1.2 + STARE + GRAY:                                   # the dot
        r = 14; cx, cy = W // 2, IY + 600
        d.ellipse([cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4], fill=(255, 255, 255))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 0, 0))
    return c
# --- voice (Kokoro, offline)
k = Kokoro(f'{M}/kokoro.onnx', f'{M}/voices.bin')
lines = [(0.2, "This will trick your brain. Stare at the black dot, and don't move your eyes."),
         (1.2 + STARE + 0.3, "Now keep looking. What colours do you see?"),
         (1.2 + STARE + GRAY + 0.2, "This picture is black and white.")]
SR = 24000; mix = np.zeros(int((T + 1) * SR), np.float32)
for at, txt in lines:
    s, sr = k.create(txt, voice='am_michael', speed=1.05, lang='en-us'); i = int(at * SR)
    mix[i:i + len(s)] += s[:len(mix) - i]
for sec in range(int(1.2 + STARE)):                              # soft clock tick each second of the stare
    if sec >= 4:
        n = int(0.04 * SR); tt = np.arange(n) / SR
        i = int((sec + 0.0) * SR); mix[i:i + n] += 0.12 * np.sin(2 * np.pi * 2000 * tt) * np.exp(-tt * 90)
sf.write(f'{D}/vo.wav', mix[:int(T * SR)], SR)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', f'{D}/vo.wav', '-af', 'loudnorm=I=-14:TP=-1.5,aresample=48000', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', f'{D}/illusion.mp4'], stdin=subprocess.PIPE)
last = None; lastimg = None
for i in range(int(T * FPS)):
    t = i / FPS
    key = (t < 1.2 + STARE, t < 1.2 + STARE + GRAY, max(0, math.ceil(1.2 + STARE - t)))
    if key != last: lastimg = frame(t).tobytes(); last = key
    enc.stdin.write(lastimg)
enc.stdin.close(); enc.wait(); print('done', T)
