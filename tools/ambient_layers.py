#!/usr/bin/env python3
"""Long ambience from several layers (e.g. rain + fireplace), each built from a few seamless 30 s loops
(ElevenLabs SFX v3). Every layer plays its loops in random order, from random offsets, with 6 s
equal-power crossfades, so nothing audibly repeats. Peaky layers (fire pops) are tamed per loop with a
compressor + limiter before mixing, so nothing startles a sleeping listener.

  python3 -I tools/ambient_layers.py OUT.m4a SECONDS 'rain:0:a.mp3,b.mp3' 'fire:-4:c.mp3,d.mp3:tame'
  layer spec = name:gain_dB:comma-separated loops[:tame]
"""
import sys, subprocess, numpy as np

SR = 44100; XF = int(6 * SR); RMS = 0.12; MASTER = 10 ** (-5.5 / 20)   # ~ -20 LUFS, calm for sleep
out, secs = sys.argv[1], float(sys.argv[2])
TAME = 'acompressor=threshold=-24dB:ratio=3:attack=3:release=120:knee=6,alimiter=limit=0.25:attack=2:release=60:level=false'


def load(p, tame):
    if tame:   # process 3 copies and keep the middle one so the compressor state wraps cleanly
        args = ['-stream_loop', '2', '-i', p, '-af', TAME]
    else:
        args = ['-i', p]
    raw = subprocess.run(['ffmpeg', '-v', 'error'] + args + ['-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    if tame:
        n = len(x) // 3; x = x[n:2 * n]
    return x / (np.sqrt((x ** 2).mean()) + 1e-9) * RMS


class Layer:
    def __init__(self, spec, seed):
        parts = spec.split(':')
        self.name, self.gain = parts[0], 10 ** (float(parts[1]) / 20)
        tame = len(parts) > 3 and parts[3] == 'tame'
        self.loops = [load(f, tame) for f in parts[2].split(',')]
        self.rng = np.random.default_rng(seed)
        self.fi = np.sqrt(np.linspace(0, 1, XF))[:, None]; self.fo = np.sqrt(np.linspace(1, 0, XF))[:, None]
        self.buf = self.piece()

    def piece(self):
        l = self.loops[self.rng.integers(len(self.loops))]
        x = np.roll(l, -self.rng.integers(0, len(l)), axis=0)
        return np.concatenate([x] * self.rng.integers(2, 5))

    def read(self, n):
        while len(self.buf) < n + XF:   # keep the crossfade tail in the buffer
            nxt = self.piece()
            blend = self.buf[-XF:] * self.fo + nxt[:XF] * self.fi
            self.buf = np.concatenate([self.buf[:-XF], blend, nxt[XF:]])
        out, self.buf = self.buf[:n], self.buf[n:]
        return out * self.gain


layers = [Layer(s, 42 + i) for i, s in enumerate(sys.argv[3:])]
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-i', '-',
                        '-af', 'highshelf=f=7000:g=-4,lowpass=f=14000,alimiter=limit=0.7:level=false,'
                               'afade=t=in:d=4,afade=t=out:st=%.2f:d=6' % (secs - 6),
                        ] + (['-c:a', 'pcm_s16le'] if out.endswith('.wav') else ['-c:a', 'aac', '-b:a', '128k']) + [out], stdin=subprocess.PIPE)
total = int(secs * SR); done = 0; CH = SR * 10
while done < total:
    n = min(CH, total - done)
    enc.stdin.write((MASTER * sum(l.read(n) for l in layers)).astype(np.float32).tobytes()); done += n
enc.stdin.close(); enc.wait()
print('mix', out, secs, [l.name for l in layers])
