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
def cam(i, p):
    m = scenes[i].get('move', 'in'); z0, z1 = (1.0, 1.12) if m != 'out' else (1.12, 1.0)
    z = z0 + (z1 - z0) * ease(p)
    dx = {'left': -1, 'right': 1}.get(m, 0) * 0.04 * (p - 0.5)
    dy = {'up': -1, 'down': 1}.get(m, 0) * 0.04 * (p - 0.5)
    sw, sh = W / z, H / z; cx, cy = W / 2 + dx * W, H / 2 + dy * H
    return imgs[i].transform((W, H), Image.EXTENT, (cx - sw / 2, cy - sh / 2, cx + sw / 2, cy + sh / 2), Image.BICUBIC)

def text_layer(lines, size, y, alpha, font=SERIF, spacing=1.25):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); f = ImageFont.truetype(font, size)
    for k, ln in enumerate(lines):
        yy = y + k * size * spacing
        d.text((W / 2 + 3, yy + 3), ln, font=f, fill=(0, 0, 0, int(160 * alpha)), anchor='mm')
        d.text((W / 2, yy), ln, font=f, fill=(255, 248, 235, int(255 * alpha)), anchor='mm')
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
