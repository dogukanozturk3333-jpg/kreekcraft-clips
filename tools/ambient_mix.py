#!/usr/bin/env python3
"""Build a long, non-repeating-sounding ambience from a few seamless loops (ElevenLabs SFX v3):
random loop order + random start offsets + 6 s equal-power crossfades, gentle de-hiss EQ, streamed to AAC.
  python3 -I tools/ambient_mix.py OUT.m4a SECONDS loop1.mp3 [loop2.mp3 ...]"""
import sys, subprocess, numpy as np
SR = 44100; out, secs = sys.argv[1], float(sys.argv[2]); files = sys.argv[3:]
def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
loops = [load(f) for f in files]
for i, l in enumerate(loops):                       # match loudness between loops
    loops[i] = l / (np.sqrt((l ** 2).mean()) + 1e-9) * 0.12
rng = np.random.default_rng(42); XF = int(6 * SR)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-i', '-',
                        '-af', 'highshelf=f=7000:g=-4,lowpass=f=14000,afade=t=in:d=4', '-c:a', 'aac', '-b:a', '192k', out], stdin=subprocess.PIPE)
def piece():
    l = loops[rng.integers(len(loops))]; reps = rng.integers(2, 5)
    s = rng.integers(0, len(l)); x = np.roll(l, -s, axis=0)
    return np.concatenate([x] * reps)               # seamless loop repeated 2–4 times from a random offset
fi = np.sqrt(np.linspace(0, 1, XF))[:, None]; fo = np.sqrt(np.linspace(1, 0, XF))[:, None]
total = int(secs * SR); written = 0; cur = piece()
while written < total:
    nxt = piece()
    body = cur[:-XF]
    n = min(len(body), total - written); enc.stdin.write(body[:n].astype(np.float32).tobytes()); written += n
    if written >= total: break
    blend = cur[-XF:] * fo + nxt[:XF] * fi
    nxt = np.concatenate([blend, nxt[XF:]]); cur = nxt
enc.stdin.close(); enc.wait(); print('mix', out, secs)
