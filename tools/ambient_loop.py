#!/usr/bin/env python3
"""Seamless living-picture loop for long ambience videos: flames in the fireplace rise and sway
(tileable noise warp), the fire and lantern flicker and cast a soft warm glow on the room.
Everything is periodic in LOOP seconds, so the clip can be stream-copied end to end for hours.
  python3 -I tools/ambient_loop.py IMG.jpg CFG.json OUT.mp4
CFG: {"fps":15,"loop":20,"fire":[cx,cy,rx,ry],"lights":[[cx,cy,r,amp],...],
      "snow":{"mask":"mask.png","wind":0.4,"layers":[{"n":300,"r":1.6,"blur":0.6,"alpha":0.85,"fall":2,"sway":6},...]}}
fire, lights and snow are all optional. Snow flakes fall in depth layers (far = small, slow, sharp; near = big,
soft bokeh), sway, and drift with the wind; every flake path is periodic in LOOP, so the loop is seamless.
"fall" = how many times a flake crosses the frame per loop (integer)."""
import os as _os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): _os.environ.setdefault(_v, '1')   # parallel renders must not spin-wait on each other
import sys, json, subprocess, numpy as np, cv2
cv2.setNumThreads(1)
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

HAS_FIRE = 'fire' in cfg
cx, cy, rx, ry = cfg.get('fire', [-9999, -9999, 1, 1])
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

SNOW = cfg.get('snow'); flakes = []
if SNOW:
    smask = (cv2.imread(SNOW['mask'], cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0)[..., None] if SNOW.get('mask') else 1.0
    srng = np.random.default_rng(11); M = 40
    for L in SNOW['layers']:
        n = L['n']
        flakes.append(dict(L=L, x0=srng.uniform(0, W + 2 * M, n), y0=srng.uniform(0, H + 2 * M, n),
                           ph=srng.uniform(0, 6.283, n), sk=srng.integers(1, 4, n), rr=srng.uniform(0.7, 1.3, n)))

def snow_layer(i):
    t = i / N; acc = np.zeros((H, W), np.float32)
    for F in flakes:
        L = F['L']; lay = np.zeros((H + 2 * 40, W + 2 * 40), np.float32)
        y = (F['y0'] + t * L['fall'] * (H + 80)) % (H + 80)
        drift = round(SNOW.get('wind', 0) * L['fall'])                    # whole crossings per loop keep it periodic
        x = (F['x0'] + t * drift * (W + 80) + L.get('sway', 0) * np.sin(2 * np.pi * F['sk'] * t + F['ph'])) % (W + 80)
        for xi, yi, r in zip(x, y, F['rr'] * L['r']):
            cv2.circle(lay, (int(xi * 4), int(yi * 4)), max(1, int(r * 4)), L['alpha'], -1, cv2.LINE_AA, 2)
        lay = lay[40:40 + H, 40:40 + W]
        if L.get('blur', 0) > 0: lay = cv2.GaussianBlur(lay, (0, 0), L['blur'])
        acc = np.maximum(acc, lay)
    return acc[..., None] * smask

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
    fr = img if not HAS_FIRE else cv2.remap(img, xx + tx * 5 * SC * m, yy + (ty * 4 + 3) * SC * m, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    fr = img + (fr - img) * flame * fmask[..., None]
    gain = 1 + (fire_f[i] - 1) * fmask[..., None] + (glow_f[i] - 1) * glow * warm
    for g, f in lights: gain = gain + (f[i] - 1) * g * warm
    out = fr * gain
    if SNOW:
        a = snow_layer(i); out = out * (1 - a) + np.array(SNOW.get('color', [255, 250, 245]), np.float32) * a
    enc.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print('loop', OUT, N, 'frames')
