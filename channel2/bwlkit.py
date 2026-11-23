"""Brain Warp Lab shared kit: brand look, animated background, emoji/text glyphs, easing, original music bed,
sound effects, Kokoro voice and the encoder. Every new puzzle format builds on this so the channel keeps
one professional look (and the watermark) without copying code around."""
import os, math, functools, subprocess, unicodedata, numpy as np, soundfile as sf, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import brandmark

W, H, FPS, SR = 1080, 1920, 30, 44100
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
KOKORO = os.environ.get('KOKORO_DIR', '/tmp/claude-0/-home-user/d825807f-e0e5-55ce-ac85-8ebee4d46dbb/scratchpad/kokoro')
HERE = os.path.dirname(os.path.abspath(__file__))
ACCENT, MAGENTA, YEL = (46, 230, 214), (255, 60, 200), (255, 214, 60)
GREEN, AMBER, RED = (88, 220, 130), (255, 200, 60), (255, 80, 100)
INK = (44, 26, 84)
CARD_FILL = (242, 238, 252, 255)


@functools.lru_cache(None)
def font(name, s):
    return ImageFont.truetype(subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout, s)


@functools.lru_cache(None)
def emoji(e, size):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), e, font=f, embedded_color=True, anchor='mm')
    return im.crop(im.getbbox()).resize((max(2, size), max(2, size)), Image.LANCZOS)


def split_emoji(s):
    out, cur = [], ''
    for ch in s:
        if cur and unicodedata.category(ch) not in ('Mn', 'Cf') and ord(ch) not in (0xFE0F, 0x200D):
            out.append(cur); cur = ''
        cur += ch
    return out + [cur]


@functools.lru_cache(None)
def logo(size):
    lg = Image.open(os.path.join(HERE, '..', 'studio', 'art', 'brainwarplab-logo.png')).convert('RGBA').resize((size, size), Image.LANCZOS)
    m = Image.new('L', (size, size), 0); ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255); lg.putalpha(m); return lg


def ease_out_back(x, s=1.7):
    x = min(max(x, 0), 1) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def ease_in_out(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- animated background
_bw, _bh = 135, 240
_yy, _xx = np.mgrid[0:_bh, 0:_bw].astype(np.float32)
_T, _B = np.array([18, 10, 44], np.float32), np.array([44, 16, 78], np.float32)
_grad = _T + (_B - _T) * (_yy / _bh)[..., None]
def background(t):
    img = _grad.copy()
    for (cx, cy, r, col, sp, ph) in ((0.25, 0.25, 0.55, (110, 50, 210), 0.11, 0), (0.8, 0.7, 0.6, (20, 150, 170), 0.08, 2),
                                     (0.6, 0.15, 0.4, (200, 50, 160), 0.13, 4)):
        px = (cx + 0.12 * math.sin(t * sp * 6.28 + ph)) * _bw; py = (cy + 0.08 * math.cos(t * sp * 5.1 + ph)) * _bh
        g = np.exp(-(((_xx - px) / (r * _bw)) ** 2 + ((_yy - py) / (r * _bw)) ** 2))[..., None]
        img += np.array(col, np.float32) * 0.45 * g
    return Image.fromarray(cv2.resize(np.clip(img, 0, 255).astype(np.uint8), (W, H), interpolation=cv2.INTER_CUBIC)).convert('RGBA')


def title(d, text, size=76, y=264, scale=1.0):
    f = font('Inter Black', max(10, int(size * scale)))
    d.text((W // 2 + 4, y + 4), text, font=f, fill=(0, 0, 0, 110), anchor='mm')
    d.text((W // 2, y), text, font=f, fill=(255, 255, 255), anchor='mm')


def brand_top(d):
    d.text((W // 2, 150), 'BRAIN WARP LAB', font=font('Inter Display SemiBold', 30), fill=(200, 190, 255), anchor='mm')


def pill(d, text, y, fill, size=42, ink=(20, 12, 40)):
    f = font('Inter Black', size); w = d.textlength(text, font=f)
    d.rounded_rectangle([W // 2 - w / 2 - 32, y - 33, W // 2 + w / 2 + 32, y + 33], 33, fill=fill)
    d.text((W // 2, y + 1), text, font=f, fill=ink, anchor='mm')


@functools.lru_cache(None)
def card(box, radius=48):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).rounded_rectangle([box[0], box[1] + 18, box[2], box[3] + 18], radius, fill=150)
    im.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(26)))
    d.rounded_rectangle(box, radius, fill=CARD_FILL)
    return im


def timer(d, frac, left, color, t, cx=W // 2, cy=1520, R=70):
    pulse = 1 + (0.08 * max(0, math.sin((t % 1) * math.pi)) if left <= 3 else 0); r = R * pulse
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(24, 14, 50, 235))
    d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * frac, fill=color, width=12)
    d.text((cx, cy + 2), str(left), font=font('Inter Black', int(64 * pulse)), fill=color, anchor='mm')


def ring(d, cx, cy, R, u, col=MAGENTA):
    ang = 360 * ease_in_out(u * 2.5)
    for wdt, a in ((16, 90), (8, 255)):
        d.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + ang, fill=col + (a,), width=wdt)


# ---------------------------------------------------------------- audio
class Audio:
    def __init__(self, T):
        self.T = T; n = int((T + 1) * SR)
        self.music = np.zeros(n, np.float32); self.voice = np.zeros(n, np.float32); self.sfx = np.zeros(n, np.float32)
        self._k = None

    @staticmethod
    def _put(buf, at, s, g=1.0):
        i = int(at * SR); j = min(len(buf), i + len(s))
        if j > i: buf[i:j] += g * s[:j - i]

    def sfx_at(self, at, s, g=1.0): self._put(self.sfx, at, s, g)

    def say(self, at, txt, speed=1.1, voice='am_michael'):
        if self._k is None:
            from kokoro_onnx import Kokoro
            self._k = Kokoro(f'{KOKORO}/kokoro.onnx', f'{KOKORO}/voices.bin')
        s, sr = self._k.create(txt, voice=voice, speed=speed, lang='en-us')
        s = cv2.resize(s.astype(np.float32)[None, :], (int(len(s) * SR / sr), 1), interpolation=cv2.INTER_LINEAR)[0]
        self._put(self.voice, at, s); return len(s) / SR

    def music_bed(self, end_t, intense_from=None, bpm=112, prog=((60, 64, 67), (57, 60, 64), (53, 57, 60), (55, 59, 62))):
        beat = 60 / bpm; mf = lambda m: 440 * 2 ** ((m - 69) / 12)
        for k in range(int(end_t / beat)):
            bar, pos = divmod(k, 4); chord = prog[bar % 4]; at = k * beat
            hard = intense_from is not None and at >= intense_from
            if pos == 0:
                self._put(self.music, at, note(mf(chord[0] - 24), beat * 2, 'bass', 0.32))
                self._put(self.music, at, note(mf(chord[0] - 12), beat * 4, 'pad', 0.05))
            if pos == 2: self._put(self.music, at, note(mf(chord[0] - 17), beat * 2, 'bass', 0.22))
            for half in (0, 1):
                m = chord[(pos * 2 + half) % 3] + (12 if (pos * 2 + half) % 4 == 3 else 0)
                self._put(self.music, at + half * beat / 2, note(mf(m), 0.5, 'marimba', 0.11))
            sh = np.random.default_rng(k).uniform(-1, 1, int(0.04 * SR)) * np.exp(-np.arange(int(0.04 * SR)) / SR * 90)
            for q in ((0.5,) if not hard else (0.25, 0.5, 0.75)): self._put(self.music, at + q * beat, sh, 0.05)
        for i_, m in enumerate((72, 76, 79)): self._put(self.music, end_t + 0.05 * i_, note(mf(m), 1.5, 'marimba', 0.13))
        self._put(self.music, end_t, note(mf(48), 2.5, 'bass', 0.3))

    def write(self, path):
        env = np.convolve(np.abs(self.voice), np.ones(int(0.25 * SR)) / int(0.25 * SR), 'same')
        duck = 1 - 0.55 * np.clip(env / (env.max() + 1e-9) * 4, 0, 1)
        mix = self.music * duck * 0.9 + self.voice + self.sfx
        mix = mix / max(1.0, np.abs(mix).max() / 0.5)
        sf.write(path, np.stack([mix, mix], 1)[:int(self.T * SR)].astype(np.float32), SR, subtype='FLOAT')


def note(f, dur, kind='marimba', g=0.2):
    n = int(dur * SR); tt = np.arange(n) / SR
    if kind == 'marimba':
        s = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 9) + 0.35 * np.sin(2 * np.pi * f * 4 * tt) * np.exp(-tt * 30)
    elif kind == 'bass':
        N = int(SR / f); buf = np.random.default_rng(int(f)).uniform(-1, 1, N); s = np.zeros(n)
        for k in range(n):
            s[k] = buf[k % N]; buf[k % N] = 0.5 * (buf[k % N] + buf[(k + 1) % N]) * 0.996
        s *= np.exp(-tt * 3)
    else:
        s = sum(np.sin(2 * np.pi * f * m * tt + m) / m for m in (1, 2, 3)) * np.minimum(1, tt / 0.3) * np.exp(-tt * 0.8)
    return (g * s).astype(np.float32)

def tone(f, dur, decay, g):
    tt = np.arange(int(dur * SR)) / SR; return (g * np.sin(2 * np.pi * f * tt) * np.exp(-tt * decay)).astype(np.float32)
def whoosh(dur=0.45, g=0.35):
    n = int(dur * SR); x = np.random.default_rng(1).normal(0, 1, n); env = np.sin(np.linspace(0, np.pi, n)) ** 2
    y = np.convolve(x, np.ones(12) / 12, 'same') * env; return (g * y / np.abs(y).max()).astype(np.float32)
def pop(g=0.25):
    n = int(0.08 * SR); tt = np.arange(n) / SR; f = 500 + 900 * tt / 0.08
    return (g * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 40)).astype(np.float32)
def heartbeat(g=0.5):
    return tone(55, 0.18, 18, g) + np.concatenate([np.zeros(int(0.14 * SR), np.float32), tone(50, 0.16, 20, g * 0.7)])[:int(0.18 * SR)]
def chime(g=1.0):
    return tone(880, 0.7, 5, 0.22 * g) + tone(1320, 0.7, 6, 0.14 * g) + tone(1760, 0.7, 8, 0.07 * g)
def tick(): return tone(1200, 0.04, 90, 0.09)


# ---------------------------------------------------------------- encode
def encode(frame_fn, T, audio, out):
    wav = out + '.wav'; audio.write(wav)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                            '-i', '-', '-i', wav, '-af', 'loudnorm=I=-14:TP=-2:LRA=9,aresample=48000,alimiter=limit=0.7:attack=1:release=40:level=false',
                            '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
                            '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for n in range(int(T * FPS)):
        im = brandmark.apply_pil(frame_fn(n / FPS))
        enc.stdin.write(im.convert('RGB').tobytes())
    enc.stdin.close(); enc.wait(); os.remove(wav)


def end_screen(t, a, b, headline=('HOW MANY', 'DID YOU FIND?'), buttons=(('1', GREEN), ('2', AMBER), ('3', RED)),
               line='Comment your score  ·  new puzzle every day'):
    u = (t - a) / (b - a); bg = background(t); d = ImageDraw.Draw(bg); brand_top(d)
    k = ease_out_back(u * 4)
    for j, s in enumerate(headline):
        d.text((W // 2, 640 + j * 125), s, font=font('Inter Black', max(10, int(104 * k))), fill=(255, 255, 255), anchor='mm')
    n_b = len(buttons)
    for n, (lab, col) in enumerate(buttons):
        kk = ease_out_back((t - a - 0.45 - n * 0.22) * 4)
        if kk <= 0.02: continue
        cx, cy = W // 2 + (n - (n_b - 1) / 2) * 240, 1010; rw, rh = (78 if len(lab) < 3 else 120) * kk, 78 * kk
        d.rounded_rectangle([cx - rw, cy - rh, cx + rw, cy + rh], int(rh), fill=col)
        d.text((cx, cy + 3), lab, font=font('Inter Black', max(10, int((84 if len(lab) < 3 else 60) * kk))), fill=(20, 12, 40), anchor='mm')
    if u > 0.2:
        lg = logo(260).copy(); lg.putalpha(lg.getchannel('A').point(lambda v: int(v * min(1, (u - .2) * 4))))
        bg.alpha_composite(lg, (W // 2 - 130, 1300)); d = ImageDraw.Draw(bg)
    if u > 0.35:
        d.text((W // 2, 1200), line, font=font('Inter Display SemiBold', 44), fill=ACCENT + (int(255 * min(1, (u - .35) * 5)),), anchor='mm')
    return bg
