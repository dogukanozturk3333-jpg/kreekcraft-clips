"""Per-frame "pro edit" effects for render.py.

Camera:      slow push-in for the whole clip, punch-in zooms on reaction peaks,
             camera shake on the biggest reaction, glitch/zoom entrance on frame 1.
Transitions: every jump cut gets one (rotating): zoom-punch + flash, whip pan with
             motion blur, RGB-split glitch. Zoom-blur into the end card.
Stickers:    optional emoji pop-ups (bounce in, wobble, pop out), off by default.
Sound:       matching SFX track (whooshes, glitch, boom, pops, riser) as a wav.
Captions, hook and brand layers are added later by ffmpeg on top, so they stay steady.
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import brand

W, H, FPS = 1080, 1920, 30
EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

def clamp(x): return max(0.0, min(1.0, x))
def out_cubic(x): return 1 - (1 - x) ** 3
def in_cubic(x): return x ** 3
def out_back(x, k=2.2): x -= 1; return 1 + (k + 1) * x ** 3 + k * x ** 2

_emoji_cache = {}
def emoji(ch, size):
    key = (ch, size)
    if key not in _emoji_cache:
        f = ImageFont.truetype(EMOJI_FONT, 109)
        im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor='mm')
        im = im.crop(im.getbbox())
        sh = Image.new('RGBA', im.size, (0, 0, 0, 255))      # soft drop shadow
        sh.putalpha(im.getchannel('A').point(lambda v: int(v * 0.55)))
        pad = 16; base = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
        base.alpha_composite(sh, (pad, pad + 6))
        base = base.filter(ImageFilter.GaussianBlur(6))
        base.alpha_composite(im, (pad, pad))
        s = size / max(base.size)
        _emoji_cache[key] = base.resize((int(base.width * s), int(base.height * s)), Image.LANCZOS)
    return _emoji_cache[key]


class Edit:
    def __init__(self, D, end, cuts, peaks, seam, stickers=(), shake=None, intro=True, beats=()):
        """cuts = jump cuts (output time); beats = sentence starts that get a transition
        and a jump-zoom reframe even though nothing was cut there."""
        self.D, self.T, self.seam = D, D + end, seam
        kinds = ('zoom', 'whip', 'glitch')
        marks = sorted(set(round(c, 2) for c in list(cuts) + list(beats)))
        self.cuts = [(c, kinds[i % 3], 1 if i % 2 == 0 else -1) for i, c in enumerate(marks)]
        # jump zoom: framing alternates tight / wide at every transition
        self.levels = [(c, 0.085 if i % 2 == 0 else 0.0) for i, c in enumerate(marks)]
        self.peaks = peaks
        self.shake = shake
        self.stickers = list(stickers)
        self.intro = intro
        self.end_bg = None

    # ------------------------------------------------------------ camera
    def camera(self, t):
        D = self.D
        z = 1.035 + 0.045 * clamp(t / D)                      # slow push-in
        for c, lv in self.levels:                              # jump-zoom reframes
            if t >= c: jz = lv
        z += jz if self.levels and t >= self.levels[0][0] else 0.0
        cx, cy = W / 2, self.seam * 0.62                       # zoom towards the facecam/seam
        dx = dy = rot = 0.0
        for p in self.peaks:                                   # punch-in on reactions
            u = t - (p - 0.08)
            if 0 <= u < 0.08: z += 0.09 * out_cubic(u / 0.08)
            elif 0.08 <= u < 0.7: z += 0.09 * (1 - out_cubic((u - 0.08) / 0.62))
        if self.shake is not None:
            u = t - self.shake
            if 0 <= u < 0.55:
                a = 18 * (1 - u / 0.55) ** 1.5
                dx += a * math.sin(2 * math.pi * 17 * u)
                dy += a * math.cos(2 * math.pi * 23 * u + 0.7)
                rot += 0.9 * (1 - u / 0.55) * math.sin(2 * math.pi * 11 * u)
                z += 0.03 * (1 - u / 0.55)
        for c, kind, sgn in self.cuts:
            u = t - c
            if kind == 'zoom' and 0 <= u < 0.35:
                z += 0.16 * math.exp(-u / 0.09)
            if kind == 'whip' and -0.1 <= u < 0.12:
                dx += sgn * 190 * (1 - abs(u) / 0.12)
            if kind == 'glitch' and 0 <= u < 0.14:
                dx += 14 * math.sin(97 * u * 30)
        if self.intro and t < 0.25:
            z += 0.16 * (1 - t / 0.25) ** 2
        if D - 0.3 <= t < D:                                  # zoom into the end card
            z += 0.35 * in_cubic((t - (D - 0.3)) / 0.3)
        z = max(z, 1.0 + 2 * (abs(dx) + abs(dy)) / W + 0.01)
        return z, cx, cy, dx, dy, rot

    @staticmethod
    def warp(img, z, cx, cy, dx, dy, rot):
        r = math.radians(rot); co, si = math.cos(r) / z, math.sin(r) / z
        ox, oy = cx + dx, cy + dy
        a, b, d, e = co, si, -si, co
        c = cx - a * ox - b * oy; f = cy - d * ox - e * oy
        return img.transform((W, H), Image.AFFINE, (a, b, c, d, e, f), resample=Image.BICUBIC)

    # ------------------------------------------------------------ frame
    def frame(self, arr, n):
        t = n / FPS
        if t >= self.D and self.end_bg is not None:           # end card background
            u = clamp((t - self.D) / (self.T - self.D))
            s = 1.0 + 0.06 * u
            bg = self.warp(self.end_bg, s, W / 2, H / 2, 0, 0, 0)
            return np.asarray(bg)
        img = Image.fromarray(arr)
        img = self.warp(img, *self.camera(t))
        out = np.asarray(img).astype(np.int16)
        # flashes
        fl = 0.0
        if self.intro and t < 0.1: fl = max(fl, 0.55 * (1 - t / 0.1))
        for c, kind, _ in self.cuts:
            u = t - c
            if kind == 'zoom' and 0 <= u < 0.1: fl = max(fl, 0.35 * (1 - u / 0.1))
        if self.shake is not None and 0 <= t - self.shake < 0.07: fl = max(fl, 0.25)
        # rgb split / glitch
        split = 0
        if self.intro and t < 0.2: split = int(22 * (1 - t / 0.2))
        for c, kind, _ in self.cuts:
            u = t - c
            if kind == 'glitch' and 0 <= u < 0.14: split = max(split, int(26 * (1 - u / 0.14)) + 4)
        if self.shake is not None and 0 <= t - self.shake < 0.15: split = max(split, 10)
        if split:
            out[..., 0] = np.roll(out[..., 0], split, axis=1)
            out[..., 2] = np.roll(out[..., 2], -split, axis=1)
            if split > 12:                                   # displaced slices
                rng = np.random.default_rng(n)
                for _ in range(6):
                    y0 = int(rng.integers(0, H - 120)); hh = int(rng.integers(14, 110))
                    out[y0:y0 + hh] = np.roll(out[y0:y0 + hh], int(rng.integers(-110, 110)), axis=1)
        # whip motion blur
        for c, kind, sgn in self.cuts:
            u = t - c
            if kind == 'whip' and -0.1 <= u < 0.12:
                L = int(150 * (1 - abs(u) / 0.12)) * sgn
                if abs(L) > 6:
                    acc = np.zeros_like(out, dtype=np.int32)
                    for i in range(8):
                        acc += np.roll(out, int(L * i / 8), axis=1)
                    out = (acc // 8).astype(np.int16)
        if fl:
            out = out + ((255 - out) * fl).astype(np.int16)
        out = np.clip(out, 0, 255).astype(np.uint8)
        # zoom blur into the end card
        if self.D - 0.3 <= t < self.D:
            k = in_cubic((t - (self.D - 0.3)) / 0.3)
            out = np.asarray(Image.fromarray(out).filter(ImageFilter.GaussianBlur(1 + 16 * k)))
        if t + 1 / FPS >= self.D and self.end_bg is None:
            b = Image.fromarray(out).filter(ImageFilter.GaussianBlur(30))
            self.end_bg = Image.fromarray((np.asarray(b) * 0.55).astype(np.uint8))
        # stickers (on top of the camera move so they stay steady)
        if self.stickers:
            img = Image.fromarray(out).convert('RGBA')
            for (ts, ch, x, y) in self.stickers:
                u = t - ts
                if 0 <= u < 1.1:
                    if u < 0.22: s = out_back(u / 0.22)
                    elif u > 0.95: s = 1 - in_cubic((u - 0.95) / 0.15)
                    else: s = 1.0
                    if s > 0.03:
                        e = emoji(ch, 190)
                        e = e.resize((max(1, int(e.width * s)), max(1, int(e.height * s))), Image.BICUBIC)
                        e = e.rotate(12 * math.sin(u * 9) * (1 - clamp(u)), resample=Image.BICUBIC, expand=True)
                        img.alpha_composite(e, (int(x - e.width / 2), int(y - e.height / 2)))
            out = np.asarray(img.convert('RGB'))
        return out

    # ------------------------------------------------------------ sound
    def sfx(self, path):
        SR = brand.SR
        x = np.zeros(int(self.T * SR) + SR)
        add = brand._add

        def boom(amp):
            n = int(0.7 * SR); t = np.arange(n) / SR
            fr = 95 * np.exp(-t / 0.18) + 42
            s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.35)
            s = np.tanh(2.2 * s) * amp
            s[:240] += brand._noise_band(240, 1500, 8000, 5) * amp * 0.5
            return s

        def glitch(amp, seed):
            n = int(0.16 * SR); rng = np.random.default_rng(seed)
            s = brand._noise_band(n, 800, 9000, seed)
            gate = np.repeat(rng.integers(0, 2, n // 600 + 1), 600)[:n]
            s = np.repeat(s[::9], 9)[:n] * gate          # bit-crushed stutter
            return amp * s * np.linspace(1, 0.3, n)

        def riser(dur, amp):
            n = int(dur * SR); t = np.arange(n) / SR
            fr = 180 + 1400 * (t / dur) ** 2
            s = 0.5 * np.sin(2 * np.pi * np.cumsum(fr) / SR) + 0.5 * brand._noise_band(n, 1000, 8000, 9)
            return amp * s * (t / dur) ** 2

        pop = lambda amp: brand._tone(650, 1700, 0.18, 0.05, amp)
        add(x, boom(0.55), 0.0)                                          # hook slam
        add(x, brand._tone(300, 160, 0.25, 0.06, 0.25), 0.14)            # second hook line
        for c, kind, _ in self.cuts:
            if kind == 'glitch': add(x, glitch(0.32, int(c * 100)), c)
            else: add(x, brand.whoosh(0.32, 0.30, int(c * 10)), max(0, c - 0.16))
        for p in self.peaks:
            if p != self.shake: add(x, brand.whoosh(0.4, 0.22, int(p * 7)), max(0, p - 0.25))
        if self.shake is not None: add(x, boom(0.75), self.shake)
        for ts, *_ in self.stickers: add(x, pop(0.28), ts)
        add(x, riser(0.45, 0.22), max(0, self.D - 0.45))
        x = x[:int(self.T * SR)]
        brand.write_wav(path, np.tanh(x * 1.1) / 1.1)
