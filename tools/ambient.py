#!/usr/bin/env python3
"""Synthesized ambient soundscapes (rain, fireplace, wind, thunder, brown noise) – no samples, no copyright.
  python3 -I tools/ambient.py rain|fire|rainfire OUT.wav SECONDS"""
import sys, wave, numpy as np
SR = 44100
kind, out, secs = sys.argv[1], sys.argv[2], float(sys.argv[3])
rng = np.random.default_rng(7); N = int(secs * SR)

def fft_filter(x, lo, hi, tilt=0.0):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    g = ((f >= lo) & (f <= hi)).astype(float)
    if tilt: g *= np.where(f > 0, (np.maximum(f, 1) / 1000.0) ** tilt, 0)
    return np.fft.irfft(X * g, len(x))

def norm(x): return x / (np.abs(x).max() + 1e-9)

def block_noise(lo, hi, tilt=0.0, seed=0):
    """Filtered noise made in 20 s blocks with crossfades (keeps memory small for long files)."""
    r = np.random.default_rng(seed); B = 20 * SR; X = 2 * SR
    y = np.zeros(N + B)
    pos = 0; fade = np.linspace(0, 1, X)
    while pos < N:
        seg = norm(fft_filter(r.standard_normal(B + X), lo, hi, tilt))
        seg[:X] *= fade; seg[-X:] *= fade[::-1]
        y[pos:pos + B + X] += seg[:len(y) - pos]
        pos += B
    return y[:N]

def drops(rate, lo, hi, amp, seed):
    r = np.random.default_rng(seed); y = np.zeros(N)
    n = int(rate * secs); t = r.integers(0, N - 2000, n)
    L = 900; k = np.arange(L)
    for c in range(8):                                   # 8 pre-made drop timbres
        g = r.standard_normal(L) * np.exp(-k / r.uniform(60, 260))
        g = fft_filter(np.pad(g, (0, 4096 - L)), r.uniform(lo, (lo + hi) / 2), hi)[:L]
        g = norm(g)
        sel = t[c::8]; a = r.uniform(0.2, 1.0, len(sel)) * amp
        for ti, ai in zip(sel, a): y[ti:ti + L] += ai * g
    return y

def rain():
    bed = block_noise(300, 9000, -0.35, 1) * 0.35
    swell = 1 + 0.18 * np.sin(2 * np.pi * np.arange(N) / SR / 23) + 0.08 * np.sin(2 * np.pi * np.arange(N) / SR / 7.3)
    y = bed * swell + drops(160, 1500, 7000, 0.18, 2) + drops(12, 300, 1500, 0.35, 3)   # fine rain + window taps
    rum = block_noise(20, 160, 0, 4); env = np.zeros(N)                                  # distant thunder
    for c in np.random.default_rng(5).uniform(10, max(11, secs - 10), int(secs / 70) + 1):
        i = int(c * SR); L = int(9 * SR); e = np.sin(np.linspace(0, np.pi, L)) ** 3
        env[i:i + L] += e[:max(0, min(L, N - i))]
    return y + rum * env * 0.5

def fire():
    bed = block_noise(40, 900, -0.5, 11) * 0.45
    crack = drops(9, 2500, 9000, 0.55, 12) + drops(25, 1200, 5000, 0.15, 13)
    pops = drops(1.2, 400, 2500, 0.9, 14)
    return bed * (1 + 0.25 * block_noise(0.1, 1.5, 0, 15)) + crack + pops

y = {'rain': rain, 'fire': fire}.get(kind, None)
if y: y = y()
else: y = rain() * 0.8 + fire() * 0.6
L = y.copy(); R = np.roll(y, int(0.011 * SR)) * 0.92 + 0.08 * y          # gentle stereo width
st = np.stack([L, R], 1); st /= np.abs(st).max() + 1e-9; st *= 0.8
f = int(3 * SR); st[:f] *= np.linspace(0, 1, f)[:, None]; st[-f:] *= np.linspace(1, 0, f)[:, None]
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print('ambient', kind, out, secs, 's')
