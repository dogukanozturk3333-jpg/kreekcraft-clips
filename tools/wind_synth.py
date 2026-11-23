#!/usr/bin/env python3
"""Original wind ambience, synthesised from noise (no samples, no licences), written as a seamless loop.
Layers: a gusting broadband body (time-varying band-pass), a soft howl that only rises in strong gusts
(two narrow resonances drifting in pitch), and a low rumble. Each stereo side gets its own noise; the gusts
are shared with a small delay so the wind moves across the room.
  python3 -I tools/wind_synth.py OUT.wav SECONDS SEED [--howl 0.5] [--strength 1.0] [--depth 0.65] [--indoor]
For a snowfall 'hush' (no wind character): --howl 0 --depth 0.2 --indoor
--indoor muffles the highs (wind heard through cabin walls and glass)."""
import sys, argparse, numpy as np, soundfile as sf
from numba import njit
from scipy.signal import butter, sosfilt

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('secs', type=float); ap.add_argument('seed', type=int)
ap.add_argument('--howl', type=float, default=0.5); ap.add_argument('--strength', type=float, default=1.0)
ap.add_argument('--indoor', action='store_true')
ap.add_argument('--depth', type=float, default=0.65, help='how much the gusts swell (0 = steady hush)')
a = ap.parse_args()
SR = 44100; XF = 8 * SR; N = int(a.secs * SR) + XF
rng = np.random.default_rng(a.seed)


def smooth_noise(n, period_s, seed):
    """Random curve with features about period_s long (cubic interpolation of random points)."""
    r = np.random.default_rng(seed); k = int(n / (period_s * SR)) + 4
    pts = r.standard_normal(k); x = np.linspace(0, k - 3.001, n)
    i = np.floor(x).astype(int); f = x - i
    p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
    return p1 + 0.5 * f * (p2 - p0 + f * (2 * p0 - 5 * p1 + 4 * p2 - p3 + f * (3 * (p1 - p2) + p3 - p0)))


@njit(cache=True)
def svf_bp(x, fc, q):
    """Chamberlin state-variable band-pass with per-sample cutoff."""
    y = np.zeros_like(x); low = 0.0; band = 0.0
    for n in range(x.shape[0]):
        f = 2.0 * np.sin(np.pi * min(fc[n], 8000.0) / 44100.0)
        high = x[n] - low - band / q[n]
        band += f * high; low += f * band
        y[n] = band
    return y


# gusts: slow swell + medium gusts, mapped to 0..1
g = 0.55 * smooth_noise(N, 14, a.seed) + 0.45 * smooth_noise(N, 3.5, a.seed + 1)
lo, hi = np.percentile(g, [3, 97]); g = np.clip((g - lo) / (hi - lo), 0, 1)
g = (1 - a.depth + a.depth * g) * a.strength          # gusts swell and fade, but never jump out of a sleeping ear's range
wob = smooth_noise(N, 1.2, a.seed + 2)

chans = []
for c, delay in ((0, 0), (1, int(0.35 * SR))):
    gc = np.roll(g, delay); w = rng.standard_normal(N)
    brown = sosfilt(butter(1, 200, 'low', fs=SR, output='sos'), w) * 6
    body = svf_bp(w * 0.6 + brown, 220 + 600 * gc ** 1.4, np.full(N, 0.9)) * (0.45 + 0.55 * gc)
    f1 = 330 + 380 * gc + 25 * wob
    howl_amt = np.clip((gc - 0.7) / 0.3, 0, 1) ** 2 * a.howl
    howl = (svf_bp(w, f1, np.full(N, 22.0)) + 0.6 * svf_bp(w, f1 * 1.47, np.full(N, 18.0))) * howl_amt * 2.2
    rumble = sosfilt(butter(2, 90, 'low', fs=SR, output='sos'), w) * 9 * (0.5 + 0.5 * gc)
    chans.append(body + howl + rumble)
x = np.stack(chans, 1)
cut = 2500 if a.indoor else 7000
x = sosfilt(butter(4, cut, 'low', fs=SR, output='sos'), x, axis=0)
x = sosfilt(butter(2, 35, 'high', fs=SR, output='sos'), x, axis=0)
# seamless loop: fold the extra tail over the head with an equal-power crossfade
fi = np.sqrt(np.linspace(0, 1, XF))[:, None]; fo = np.sqrt(np.linspace(1, 0, XF))[:, None]
y = x[:N - XF].copy(); y[:XF] = x[N - XF:] * fo + x[:XF] * fi
y = y / (np.sqrt((y ** 2).mean()) + 1e-9) * 0.1
sf.write(a.out, y.astype(np.float32), SR, subtype='FLOAT')
print('wind', a.out, a.secs, 's  peak', round(float(np.abs(y).max()), 3))
