#!/usr/bin/env python3
"""Seamless living-picture loop for long ambience videos: flames in the fireplace rise and sway
(tileable noise warp), the fire and lantern flicker and cast a soft warm glow on the room.
Everything is periodic in LOOP seconds, so the clip can be stream-copied end to end for hours.
  python3 -I tools/ambient_loop.py IMG.jpg CFG.json OUT.mp4
CFG: {"fps":15,"loop":20,"fire":[cx,cy,rx,ry],"lights":[[cx,cy,r,amp],...]}"""
import sys, json, subprocess, numpy as np, cv2
img = cv2.imread(sys.argv[1]).astype(np.float32); cfg = json.load(open(sys.argv[2])); OUT = sys.argv[3]
H, W = img.shape[:2]; FPS = cfg.get('fps', 15); T = cfg.get('loop', 20); N = FPS * T
rng = np.random.default_rng(7)
SC = cfg.get('scale', 1.0)                               # >1 when the picture was upscaled (vertical Shorts crop)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

def tile_noise(h, w, scale):           # periodic smooth noise via filtered FFT
    f = np.fft.fft2(rng.standard_normal((h, w)))
    ky = np.fft.fftfreq(h)[:, None]; kx = np.fft.fftfreq(w)[None, :]
    f *= np.exp(-(kx ** 2 + ky ** 2) * (scale ** 2))
    n = np.real(np.fft.ifft2(f)); return (n / n.std()).astype(np.float32)

def flicker(seed, amp, fmax=3.0):       # sum of sinusoids periodic in T
    r = np.random.default_rng(seed); t = np.arange(N) / FPS; s = np.zeros(N)
    for k in range(1, int(fmax * T)):
        s += r.standard_normal() / (1 + k / 8) * np.sin(2 * np.pi * k * t / T + r.uniform(0, 6.3))
    return 1 + amp * s / np.abs(s).max()

cx, cy, rx, ry = cfg['fire']
fmask = np.clip(1 - ((xx - cx) / rx) ** 2 - ((yy - cy) / ry) ** 2, 0, 1) ** 0.7
up = np.clip((cy + ry - yy) / (2 * ry), 0, 1)            # flames move more near the tips
lum = cv2.cvtColor(img.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
flame = cv2.GaussianBlur(np.clip((lum - 120) / 80, 0, 1), (0, 0), 6 * SC)[..., None]   # only bright flame pixels move, logs stay put
TH = 256; nx = tile_noise(TH, TH, 18 * SC); ny = tile_noise(TH, TH, 18 * SC)
glow = np.exp(-(((xx - cx) / (700 * SC)) ** 2 + ((yy - cy) / (520 * SC)) ** 2))[..., None]
fire_f = flicker(1, 0.09); glow_f = flicker(2, cfg.get('glow', 0.02), 0.6)   # room glow breathes slowly (cheap to encode)
lights = [(np.exp(-(((xx - lx) ** 2 + (yy - ly) ** 2) / (r ** 2)))[..., None], flicker(10 + i, a, 4))
          for i, (lx, ly, r, a) in enumerate(cfg.get('lights', []))]
warm = np.array([0.80, 0.93, 1.0], np.float32)   # BGR: glow leans orange

CRF = str(cfg.get('crf', 27))
VCODEC = {'x264': ['-c:v', 'libx264', '-preset', 'veryslow', '-crf', CRF, '-g', str(N), '-keyint_min', str(N), '-sc_threshold', '0',
                   '-x264-params', 'ipratio=2.5:aq-mode=3'],   # one crisp keyframe per loop, the rest is just the fire
          'x265': ['-c:v', 'libx265', '-preset', 'slow', '-crf', CRF, '-tag:v', 'hvc1',
                   '-x265-params', f'keyint={N}:min-keyint={N}:scenecut=0:log-level=error'],   # one closed GOP per loop
          'lossless': ['-c:v', 'libx264', '-preset', 'ultrafast', '-qp', '0']}[cfg.get('codec', 'x264')]
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}',
                        '-r', str(FPS), '-i', '-', ] + VCODEC + ['-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for i in range(N):
    sh = int(round(i / FPS * TH / 10)) % TH          # noise scrolls up one tile per 10 s (LOOP must be a multiple of 10)
    tx = np.tile(np.roll(nx, -sh, axis=0), (H // TH + 1, W // TH + 1))[:H, :W]
    ty = np.tile(np.roll(ny, -sh, axis=0), (H // TH + 1, W // TH + 1))[:H, :W]
    m = fmask * (0.35 + 0.65 * up)
    fr = cv2.remap(img, xx + tx * 5 * SC * m, yy + (ty * 4 + 3) * SC * m, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    fr = img + (fr - img) * flame * fmask[..., None]
    gain = 1 + (fire_f[i] - 1) * fmask[..., None] + (glow_f[i] - 1) * glow * warm
    for g, f in lights: gain = gain + (f[i] - 1) * g * warm
    enc.stdin.write(np.clip(fr * gain, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print('loop', OUT, N, 'frames')
