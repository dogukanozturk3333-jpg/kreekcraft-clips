#!/usr/bin/env python3
"""Silent animated story shorts: stills -> slow camera moves, crossfades, short serif captions,
an end message and an original synthesized piano track (no outside music).
  python3 -I tools/story.py SPEC.json OUT.mp4
SPEC: {"scenes":[{"img":path,"dur":s,"caption":"...","move":"in|out|left|right|up"}...],
       "end":{"lines":["...","..."],"dur":s}, "hook":"..."}"""
import json, sys, subprocess, math, os, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
SERIF = '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'
SERIF_B = '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'
spec = json.load(open(sys.argv[1])); OUT = sys.argv[2]
XF = 0.7
scenes = spec['scenes']; end = spec['end']
imgs = [Image.open(s['img']).convert('RGB').resize((W, H), Image.LANCZOS) for s in scenes]
starts = []; t = 0
for s in scenes:
    starts.append(t); t += s['dur'] - XF
T_END0 = t + XF                      # end card begins after last scene
T = T_END0 + end['dur']

def ease(x): return 0.5 - 0.5 * math.cos(math.pi * max(0, min(1, x)))
import cv2
DEP = []
for s_ in scenes:
    dp = s_.get('depth')
    DEP.append(cv2.GaussianBlur(np.asarray(Image.open(dp).convert('L').resize((W, H)), np.float32) / 255, (0, 0), 5) if dp and os.path.exists(dp) else None)
ARR = [np.asarray(im) for im in imgs]
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
VEC = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1), 'in': (0.35, -0.25), 'out': (-0.35, 0.25)}
def cam(i, p):
    """2.5D camera: zoom plus depth-dependent shift (near things move more = parallax)."""
    m = scenes[i].get('move', 'in'); e = ease(p)
    z = (1.06 + 0.10 * e) if m != 'out' else (1.16 - 0.10 * e)
    D = DEP[i] if DEP[i] is not None else np.full((H, W), 0.5, np.float32)
    vx, vy = VEC.get(m, (0, 0)); amp = 80 * (e - 0.5)
    zd = z * (1 + 0.07 * (D - 0.3) * (e if m != 'out' else 1 - e))
    mx = W / 2 + (XX - W / 2) / zd - vx * amp * (D - 0.3)
    my = H / 2 + (YY - H / 2) / zd - vy * amp * (D - 0.3)
    out = cv2.remap(ARR[i], mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return fx(i, p, out)

def fx(i, p, a):
    """Small living details: dust motes, rain on windows, bokeh, flickering lamp light."""
    effs = scenes[i].get('fx', []); t = p * scenes[i]['dur']
    if not effs: return Image.fromarray(a)
    rng = np.random.default_rng(100 + i); f = a.astype(np.float32)
    if 'flicker' in effs:
        luma = f.mean(axis=2, keepdims=True) / 255
        f *= 1 + (0.035 * math.sin(t * 9) + 0.02 * math.sin(t * 23)) * luma ** 2
    lay = np.zeros((H, W, 3), np.float32)
    if 'dust' in effs:
        n = 70; x0 = rng.uniform(0, W, n); y0 = rng.uniform(0, H, n); sp = rng.uniform(8, 25, n); r = rng.uniform(1.5, 4, n); ph = rng.uniform(0, 6.28, n); al = rng.uniform(.25, .7, n)
        for k in range(n):
            x = (x0[k] + 18 * math.sin(t * .7 + ph[k])) % W; y = (y0[k] - sp[k] * t) % H
            cv2.circle(lay, (int(x), int(y)), int(r[k]), (255 * al[k], 230 * al[k], 180 * al[k]), -1, cv2.LINE_AA)
    if 'bokeh' in effs:
        n = 16; x0 = rng.uniform(0, W, n); y0 = rng.uniform(0, H * .7, n); r = rng.uniform(14, 40, n); ph = rng.uniform(0, 6.28, n)
        for k in range(n):
            a_ = .18 + .12 * math.sin(t * 1.3 + ph[k])
            cv2.circle(lay, (int(x0[k] + 10 * math.sin(t * .4 + ph[k])), int(y0[k] - 6 * t)), int(r[k]), (255 * a_, 190 * a_, 110 * a_), -1, cv2.LINE_AA)
    if lay.any():
        lay = cv2.GaussianBlur(lay, (0, 0), 2.2); f += lay
    for box in scenes[i].get('rain', []):
        x0b, y0b, x1b, y1b = int(box[0] * W), int(box[1] * H), int(box[2] * W), int(box[3] * H)
        rl = np.zeros((H, W, 3), np.float32); n = 140
        xs = rng.uniform(x0b, x1b, n); ys = rng.uniform(y0b, y1b, n); sp = rng.uniform(900, 1500, n)
        for k in range(n):
            y = y0b + (ys[k] - y0b + sp[k] * t) % max(1, (y1b - y0b)); x = xs[k] + 0.12 * (y - y0b)
            cv2.line(rl, (int(x), int(y)), (int(x + 4), int(y + 26)), (150, 170, 200), 1, cv2.LINE_AA)
        f[y0b:y1b, x0b:x1b] += rl[y0b:y1b, x0b:x1b] * 0.45
    return Image.fromarray(np.clip(f, 0, 255).astype(np.uint8))

def text_layer(lines, size, y, alpha, font=SERIF, spacing=1.25):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = ImageFont.truetype(font, size)
    for k, ln in enumerate(lines):
        yy = y + k * size * spacing
        d.text((W / 2 + 3, yy + 4), ln, font=f, fill=(0, 0, 0, int(170 * alpha)), anchor='mm', stroke_width=6, stroke_fill=(0, 0, 0, int(120 * alpha)))
        d.text((W / 2, yy), ln, font=f, fill=(255, 248, 235, int(255 * alpha)), anchor='mm', stroke_width=3, stroke_fill=(20, 12, 6, int(230 * alpha)))
    return lay

badge = Image.open(os.path.join(os.path.dirname(__file__), '..', 'brand', 'art', 'logo.png')).convert('RGBA').resize((64, 64), Image.LANCZOS)
badge.putalpha(badge.getchannel('A').point(lambda v: int(v * 0.55)))

def frame(t):
    if t < T_END0:
        idx = [i for i, s in enumerate(starts) if s <= t][-1]
        p = (t - starts[idx]) / scenes[idx]['dur']
        img = cam(idx, p)
        if idx + 1 < len(scenes) and t > starts[idx + 1]:
            a = (t - starts[idx + 1]) / XF
            img = Image.blend(img, cam(idx + 1, (t - starts[idx + 1]) / scenes[idx + 1]['dur']), ease(a))
            idx_cap, pc = idx + 1, (t - starts[idx + 1]) / scenes[idx + 1]['dur']
        else:
            idx_cap, pc = idx, p
        img = img.convert('RGBA')
        cap = scenes[idx_cap].get('caption')
        if cap:
            dur = scenes[idx_cap]['dur']; tt = pc * dur
            a = min(1, max(0, (tt - 0.4) / 0.4)) * min(1, max(0, (dur - XF - tt) / 0.35))
            if a > 0: img.alpha_composite(text_layer([cap], 66, 1560, a))
        if spec.get('hook') and t < 2.6:
            a = min(1, t / 0.25) * min(1, (2.6 - t) / 0.3)
            img.alpha_composite(text_layer(spec['hook'].split('|'), 70, 300, a, SERIF_B))
    else:
        te = t - T_END0
        last = cam(len(scenes) - 1, 1.0).filter(ImageFilter.GaussianBlur(min(18, te * 30)))
        img = Image.blend(last, Image.new('RGB', (W, H), (8, 6, 4)), min(0.55, te * 0.9)).convert('RGBA')
        for k, ln in enumerate(end['lines']):
            a = min(1, max(0, (te - 0.4 - k * 0.9) / 0.6))
            if a > 0: img.alpha_composite(text_layer([ln], 76 if k == 0 else 58, 860 + k * 120, a, SERIF_B if k == 0 else SERIF))
    img.alpha_composite(badge, (W - 64 - 36, 60))
    return img.convert('RGB')

# ---- original piano score (synthesized)
SR = 48000
def note(f, dur, amp):
    n = int(dur * SR); t = np.arange(n) / SR
    env = np.exp(-t * 2.2) * np.minimum(1, t / 0.005)
    s = sum(a * np.sin(2 * np.pi * f * h * t) for h, a in ((1, 1), (2, .45), (3, .2), (4, .1)))
    return amp * s * env
def midi(m): return 440 * 2 ** ((m - 69) / 12)
prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [55, 60, 64]), (55, [55, 59, 62])]   # Am F C G
beat = 60 / 72; mus = np.zeros(int((T + 2) * SR))
def add(sig, at):
    i = int(at * SR); j = min(len(mus), i + len(sig)); mus[i:j] += sig[:j - i]
t0 = 0.0; bar = 0
melody = [76, 74, 72, 71, 72, 74, 76, 79, 77, 76, 74, 72, 71, 72, 74, 72]
while t0 < T:
    root, ch = prog[bar % 4]
    add(note(midi(root - 12), beat * 4, 0.22), t0)
    for k in range(4):                             # gentle broken chord
        add(note(midi(ch[k % 3] + (12 if k == 3 else 0)), beat * 2, 0.10), t0 + k * beat)
    if bar >= 1:
        for k in range(2):
            m = melody[(bar * 2 + k) % len(melody)]
            add(note(midi(m), beat * 2.5, 0.11), t0 + k * beat * 2)
    t0 += beat * 4; bar += 1
# soft reverb-ish tail
ir = np.exp(-np.arange(int(1.2 * SR)) / SR * 4) * np.random.default_rng(1).standard_normal(int(1.2 * SR)) * 0.02
mus = mus + np.convolve(mus, ir)[:len(mus)]
mus = mus[:int(T * SR)]; fade = int(2.0 * SR); mus[-fade:] *= np.linspace(1, 0, fade)
mus /= np.abs(mus).max() + 1e-9; mus *= 0.7
wav = OUT + '.wav'
with wave.open(wav, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(np.repeat((mus * 32767).astype(np.int16)[:, None], 2, axis=1).tobytes())
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', wav, '-af', 'loudnorm=I=-16:TP=-1.5', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', f'{T}', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for i in range(int(T * FPS)):
    enc.stdin.write(frame(i / FPS).tobytes())
enc.stdin.close(); enc.wait(); os.remove(wav)
print('story', OUT, round(T, 1), 's')
