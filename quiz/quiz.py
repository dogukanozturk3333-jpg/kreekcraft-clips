#!/usr/bin/env python3
"""Geography quiz videos — "Guess the Flag" (Shorts and long-form). Flags are drawn from the Noto Color Emoji font
(Apache 2.0), voice is Kokoro (offline, Apache 2.0), music and sounds are synthesised here: no third-party footage.
  python3 -I quiz/quiz.py short SEED OUT.mp4 [--brand NAME]      # 5 flags, easy -> impossible, ~35 s, 1080x1920
  python3 -I quiz/quiz.py long  SEED OUT.mp4 [--brand NAME]      # 5 levels x 12 flags, ~8.5 min, 1920x1080
Every question is checked before rendering: exactly one correct option, four different options, the flag shown is
the flag of the answer (the emoji is built from the ISO code of the answer itself)."""
import os as _os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): _os.environ.setdefault(_v, '1')
import sys, os, json, math, random, functools, subprocess, numpy as np, cv2, soundfile as sf
cv2.setNumThreads(1)
from PIL import Image, ImageDraw, ImageFont, ImageFilter

MODE, SEED, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
BRAND = sys.argv[sys.argv.index('--brand') + 1] if '--brand' in sys.argv else ''
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
LONG = MODE == 'long'
W, H = (1920, 1080) if LONG else (1080, 1920)
FPS, SR = 30, 44100
YEL, GREEN, RED, WHITE = (255, 214, 60), (60, 210, 110), (235, 70, 80), (255, 255, 255)
BG1, BG2 = np.array([24, 40, 92], np.float32), np.array([10, 16, 44], np.float32)      # deep blue (RGB)

# ------------------------------------------------------------------ countries: ISO code, name, difficulty 1..4
C = """US United States 1|BR Brazil 1|JP Japan 1|CA Canada 1|GB United Kingdom 1|DE Germany 1|FR France 1|IT Italy 1
|TR Turkey 1|CN China 1|IN India 1|MX Mexico 1|ES Spain 1|KR South Korea 1|AR Argentina 1|AU Australia 1|RU Russia 1
|SE Sweden 2|GR Greece 2|PT Portugal 2|NL Netherlands 2|CH Switzerland 2|NO Norway 2|EG Egypt 2|ZA South Africa 2
|PL Poland 2|IE Ireland 2|IL Israel 2|SA Saudi Arabia 2|NG Nigeria 2|FI Finland 2|DK Denmark 2|BE Belgium 2|AT Austria 2
|UA Ukraine 2|NZ New Zealand 2|JM Jamaica 2|CO Colombia 2|CL Chile 2|PK Pakistan 2
|VN Vietnam 3|ID Indonesia 3|MC Monaco 3|PE Peru 3|TH Thailand 3|MY Malaysia 3|PH Philippines 3|KE Kenya 3
|MA Morocco 3|RO Romania 3|TD Chad 3|HU Hungary 3|CZ Czechia 3|HR Croatia 3|RS Serbia 3|IR Iran 3|IQ Iraq 3|CU Cuba 3
|VE Venezuela 3|EC Ecuador 3|CI Ivory Coast 3|SG Singapore 3|QA Qatar 3|AE United Arab Emirates 3|LB Lebanon 3|NP Nepal 3
|BT Bhutan 4|KI Kiribati 4|SZ Eswatini 4|NR Nauru 4|TV Tuvalu 4|LS Lesotho 4|MU Mauritius 4|BN Brunei 4|SC Seychelles 4
|MD Moldova 4|KG Kyrgyzstan 4|TM Turkmenistan 4|MN Mongolia 4|LK Sri Lanka 4|KH Cambodia 4|LA Laos 4|BZ Belize 4
|GD Grenada 4|DM Dominica 4|VU Vanuatu 4|FJ Fiji 4|PG Papua New Guinea 4|ER Eritrea 4|DJ Djibouti 4|KM Comoros 4"""
COUNTRY = {}
for part in C.replace('\n', '').split('|'):
    p = part.strip().split(' '); COUNTRY[p[0]] = (' '.join(p[1:-1]), int(p[-1]))
# look-alike flags: used as wrong options so the quiz is genuinely tricky
LOOKALIKE = [['ID', 'MC', 'PL'], ['TD', 'RO', 'MD'], ['IE', 'CI', 'IT'], ['NL', 'FR', 'RU', 'HR'], ['AU', 'NZ', 'GB'],
             ['CO', 'EC', 'VE'], ['NO', 'DK', 'SE', 'FI'], ['SN', 'ML', 'GN'] , ['US', 'MY', 'LR'], ['AT', 'LB', 'PE'],
             ['EG', 'IQ', 'YE'], ['SG', 'ID', 'MC'], ['HU', 'IT', 'IR'], ['QA', 'BH', 'AE']]
LEVEL_NAME = {1: 'EASY', 2: 'MEDIUM', 3: 'HARD', 4: 'IMPOSSIBLE'}
LEVEL_COL = {1: GREEN, 2: YEL, 3: (255, 140, 60), 4: RED}


def flag_emoji(code):
    return ''.join(chr(0x1F1E6 + ord(c) - 65) for c in code)


def make_question(rng, code):
    tier = COUNTRY[code][1]
    group = next((g for g in LOOKALIKE if code in g), [])
    pool = [c for c in group if c != code and c in COUNTRY]
    others = [c for c in COUNTRY if c != code and c not in pool and abs(COUNTRY[c][1] - tier) <= 1]
    rng.shuffle(others)
    wrong = (pool + others)[:3]
    opts = wrong + [code]; rng.shuffle(opts)
    q = dict(code=code, name=COUNTRY[code][0], tier=tier, options=[COUNTRY[c][0] for c in opts], answer=opts.index(code))
    # --- the checks this channel lives by
    assert len(set(q['options'])) == 4, q
    assert q['options'].count(q['name']) == 1 and q['options'][q['answer']] == q['name'], q
    assert flag_emoji(code) == ''.join(chr(0x1F1E6 + ord(c) - 65) for c in code)
    return q


rng = random.Random(SEED)
if LONG:
    LEVELS = [(1, 12), (2, 12), (3, 12), (3, 12), (4, 12)]          # level tier, number of flags
    used, QS = set(), []
    for li, (tier, n) in enumerate(LEVELS):
        cands = [c for c in COUNTRY if COUNTRY[c][1] == tier and c not in used]; rng.shuffle(cands)
        if len(cands) < n: cands += [c for c in COUNTRY if COUNTRY[c][1] == tier - 1 and c not in used and c not in cands]
        for c in cands[:n]: used.add(c); QS.append(dict(make_question(rng, c), level=li + 1))
    THINK, REVEAL = 5.0, 2.4
else:
    tiers = [1, 2, 3, 3, 4]; QS = []; used = set()
    for k, t in enumerate(tiers):
        c = rng.choice([c for c in COUNTRY if COUNTRY[c][1] == t and c not in used]); used.add(c)
        QS.append(dict(make_question(rng, c), level=k + 1))
    THINK, REVEAL = 3.2, 1.7

# ------------------------------------------------------------------ timeline
segs = []                      # (kind, start, end, data)
t = 0.0
INTRO = 2.6 if not LONG else 7.0
segs.append(('intro', t, t + INTRO, None)); t += INTRO
prev_level = None
for i, q in enumerate(QS):
    if LONG and q['level'] != prev_level:
        segs.append(('level', t, t + 3.6, q['level'])); t += 3.6; prev_level = q['level']
    segs.append(('q', t, t + THINK + REVEAL, (i, q))); t += THINK + REVEAL
OUTRO = 3.0 if not LONG else 8.0
segs.append(('outro', t, t + OUTRO, None)); t += OUTRO
T = t; N = int(T * FPS)


# ------------------------------------------------------------------ drawing
@functools.lru_cache(None)
def font(name, s):
    return ImageFont.truetype(subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout, s)


@functools.lru_cache(None)
def background():
    yy = np.linspace(0, 1, H)[:, None, None]; xx = np.linspace(0, 1, W)[None, :, None]
    g = BG1 * (1 - yy) + BG2 * yy
    g = g + 18 * np.exp(-(((xx - 0.5) ** 2) / 0.08 + ((yy - 0.35) ** 2) / 0.05))       # soft spotlight
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), 'RGB').convert('RGBA')


@functools.lru_cache(None)
def flag_img(code, w):
    fi = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
    ImageDraw.Draw(fi).text((100, 100), flag_emoji(code), font=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109),
                            embedded_color=True, anchor='mm')
    fi = fi.crop(fi.getbbox()); h = int(fi.height * w / fi.width); fi = fi.resize((w, h), Image.LANCZOS)
    fi = fi.filter(ImageFilter.UnsharpMask(radius=2, percent=55, threshold=2))       # the emoji font is a bitmap: keep edges crisp
    card = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0)); sh = Image.new('RGBA', card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([14, 22, w + 26, h + 34], 26, fill=(0, 0, 0, 140)); sh = sh.filter(ImageFilter.GaussianBlur(12))
    card.alpha_composite(sh); m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 22, fill=255)
    fi.putalpha(Image.composite(fi.getchannel('A'), Image.new('L', (w, h), 0), m)); card.alpha_composite(fi, (20, 20))
    return card


def brand_tag(im):
    if not BRAND: return
    d = ImageDraw.Draw(im); d.text((W // 2, H - 60), BRAND, font=font('Inter Black', 30), fill=(255, 255, 255, 120), anchor='mm')


def ring(d, cx, cy, R, frac, txt, col=YEL):
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(12, 18, 48, 230))
    d.arc([cx - R, cy - R, cx + R, cy + R], -90, -90 + 360 * frac, fill=col, width=12)
    d.text((cx, cy + 2), txt, font=font('Inter Black', int(R * 0.95)), fill=col, anchor='mm')


@functools.lru_cache(None)
def question_base(i, reveal):
    q = QS[i]; im = background().copy(); d = ImageDraw.Draw(im)
    if LONG:
        d.text((60, 70), 'GUESS THE FLAG', font=font('Inter Black', 54), fill=WHITE, anchor='lm')
        lv = q['level']; tier = q['tier']
        d.rounded_rectangle([60, 115, 520, 175], 30, fill=LEVEL_COL[tier])
        d.text((290, 146), f'LEVEL {lv} · {LEVEL_NAME[tier]}', font=font('Inter Black', 32), fill=(20, 20, 30), anchor='mm')
        d.text((W - 60, 70), f'{i + 1} / {len(QS)}', font=font('Inter Black', 54), fill=YEL, anchor='rm')
        fl = flag_img(q['code'], 700); im.alpha_composite(fl, (560 - fl.width // 2, 560 - fl.height // 2))
        x0, y0, bw, bh, gap = 1110, 250, 740, 130, 28
    else:
        d.text((W // 2, 120), 'GUESS THE FLAG', font=font('Inter Black', 92), fill=WHITE, anchor='mm', stroke_width=4, stroke_fill=(8, 12, 40))
        tier = q['tier']
        d.rounded_rectangle([W // 2 - 250, 190, W // 2 + 250, 260], 35, fill=LEVEL_COL[tier])
        d.text((W // 2, 226), f'{i + 1}/5 · {LEVEL_NAME[tier]}', font=font('Inter Black', 38), fill=(20, 20, 30), anchor='mm')
        fl = flag_img(q['code'], 720); im.alpha_composite(fl, (W // 2 - fl.width // 2, 640 - fl.height // 2))
        x0, y0, bw, bh, gap = 110, 1010, 860, 118, 22
    for k, opt in enumerate(q['options']):
        y = y0 + k * (bh + gap); ok = k == q['answer']
        if reveal: fill = GREEN if ok else (40, 46, 80)
        else: fill = (250, 250, 255)
        tc = (255, 255, 255) if (reveal and ok) else ((150, 155, 180) if reveal else (20, 24, 50))
        d.rounded_rectangle([x0, y, x0 + bw, y + bh], bh // 2, fill=fill)
        d.ellipse([x0 + 14, y + 14, x0 + bh - 14, y + bh - 14], fill=(20, 28, 70) if not (reveal and ok) else (255, 255, 255))
        d.text((x0 + bh // 2, y + bh // 2), 'ABCD'[k], font=font('Inter Black', 44), fill=YEL if not (reveal and ok) else GREEN, anchor='mm')
        size = 50 if len(opt) < 16 else 40
        d.text((x0 + bh + 20, y + bh // 2), opt, font=font('Inter Black', size), fill=tc, anchor='lm')
        if reveal and ok: d.text((x0 + bw - 50, y + bh // 2), '✓', font=font('DejaVu Sans Bold', 64), fill=WHITE, anchor='mm')
    brand_tag(im)
    return im


def frame(tt):
    seg = next((s for s in segs if s[1] <= tt < s[2]), segs[-1])                   # float-safe at segment edges
    kind, a, b, data = seg; u = tt - a
    if kind == 'q':
        i, q = data; rev = u >= THINK
        im = question_base(i, rev).copy(); d = ImageDraw.Draw(im)
        if not rev:
            left = THINK - u
            cx, cy, R = (160, 930, 80) if LONG else (W // 2, 1690, 86)
            ring(d, cx, cy, R, left / THINK, str(int(math.ceil(left))))
        else:
            k = min(1.0, (u - THINK) / 0.25)
            msg = q['name'].upper()
            if LONG: d.text((560, 950), msg, font=font('Inter Black', 64 if len(msg) < 16 else 48), fill=GREEN, anchor='mm', stroke_width=4, stroke_fill=(8, 12, 40))
            else: d.text((W // 2, 1690), msg, font=font('Inter Black', 76 if len(msg) < 14 else 56), fill=GREEN, anchor='mm', stroke_width=5, stroke_fill=(8, 12, 40))
        return im
    im = background().copy(); d = ImageDraw.Draw(im)
    if kind == 'intro':
        if LONG:
            d.text((W // 2, 300), 'GUESS THE FLAG', font=font('Inter Black', 150), fill=WHITE, anchor='mm', stroke_width=6, stroke_fill=(8, 12, 40))
            d.text((W // 2, 460), f'{len(QS)} FLAGS · 5 LEVELS · EASY TO IMPOSSIBLE', font=font('Inter Black', 56), fill=YEL, anchor='mm')
            for k, c in enumerate(['US', 'BR', 'JP', 'TR', 'IN', 'BT']):
                fl = flag_img(c, 190); im.alpha_composite(fl, (int(W / 2 + (k - 2.5) * 260 - fl.width / 2), 600))
            d.text((W // 2, 930), 'keep score and comment your result!', font=font('Inter Display SemiBold', 46), fill=(220, 225, 255), anchor='mm')
        else:
            d.text((W // 2, 640), 'GUESS THE', font=font('Inter Black', 130), fill=WHITE, anchor='mm', stroke_width=6, stroke_fill=(8, 12, 40))
            d.text((W // 2, 790), 'FLAG', font=font('Inter Black', 190), fill=YEL, anchor='mm', stroke_width=6, stroke_fill=(8, 12, 40))
            d.text((W // 2, 960), 'easy → impossible', font=font('Inter Black', 64), fill=(220, 225, 255), anchor='mm')
            d.text((W // 2, 1080), 'can you get all 5?', font=font('Inter Black', 64), fill=GREEN, anchor='mm')
    elif kind == 'level':
        lv = data; tier = LEVELS[lv - 1][0]
        d.text((W // 2, 420), f'LEVEL {lv}', font=font('Inter Black', 130), fill=WHITE, anchor='mm')
        d.text((W // 2, 580), LEVEL_NAME[tier], font=font('Inter Black', 160), fill=LEVEL_COL[tier], anchor='mm', stroke_width=6, stroke_fill=(8, 12, 40))
    elif kind == 'outro':
        if LONG:
            d.text((W // 2, 330), 'HOW MANY DID YOU GET?', font=font('Inter Black', 110), fill=WHITE, anchor='mm')
            d.text((W // 2, 480), f'comment your score out of {len(QS)}', font=font('Inter Display SemiBold', 56), fill=YEL, anchor='mm')
            d.text((W // 2, 640), 'subscribe for a new quiz every week', font=font('Inter Display SemiBold', 50), fill=(220, 225, 255), anchor='mm')
        else:
            d.text((W // 2, 720), 'HOW MANY', font=font('Inter Black', 130), fill=WHITE, anchor='mm')
            d.text((W // 2, 860), 'DID YOU GET?', font=font('Inter Black', 120), fill=YEL, anchor='mm')
            d.text((W // 2, 1010), 'comment your score 👇'.replace(' 👇', ''), font=font('Inter Black', 64), fill=(220, 225, 255), anchor='mm')
            for k in range(5):
                ok = True; cx = W // 2 + (k - 2) * 150
                d.text((cx, 1180), str(k + 1), font=font('Inter Black', 70), fill=YEL, anchor='mm')
    brand_tag(im)
    return im


# ------------------------------------------------------------------ audio
mix = np.zeros(int((T + 2) * SR), np.float32); mus = np.zeros_like(mix)
def put(at, s, g=1.0, buf=None):
    buf = mix if buf is None else buf; i = int(at * SR); j = min(len(buf), i + len(s)); buf[i:j] += g * s[:j - i]
def tone(f, d, g, decay=8):
    x = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x)) * np.exp(-x * decay) * g
BPM = 112; beat = 60 / BPM; b, k = 0.0, 0
chords = [(220.0, 277.2, 329.6), (196.0, 246.9, 293.7), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7)]
while b < T:
    ch = chords[(k // 8) % 4]
    put(b, tone(ch[k % 3] * 2, beat * 0.5, 0.03, 10), 1.0, mus)
    if k % 2 == 0: put(b, tone(ch[0] / 2, beat * 1.8, 0.05, 2.5), 1.0, mus)
    b += beat / 2; k += 1
for kind, a, b_, data in segs:
    if kind == 'q':
        for s in range(int(THINK)): put(a + s, tone(1200, 0.06, 0.12, 60))
        put(a + THINK, tone(784, 0.6, 0.18, 5)); put(a + THINK + 0.08, tone(1175, 0.7, 0.14, 5))
sys.path.insert(0, os.path.join(REPO, 'channel2')); import bwlkit
KK = bwlkit.kokoro()
def voice(txt, speed=1.06):
    s, sr = KK.create(txt, voice='am_michael', speed=speed, lang='en-us')
    return cv2.resize(s.astype(np.float32)[None, :], (int(len(s) * SR / sr), 1), interpolation=cv2.INTER_LINEAR)[0]
duck = np.ones(len(mix), np.float32)
def say(at, txt):
    v = voice(txt); put(at, v); i0, i1 = int(at * SR), min(len(mix), int(at * SR) + len(v)); duck[i0:i1] = 0.4
for kind, a, b_, data in segs:
    if kind == 'intro':
        say(a + 0.2, f'Guess the flag! {len(QS)} flags, from easy to impossible. Keep score!' if LONG else
            'Guess the flag! Five flags, from easy to impossible. Can you get all five?')
    elif kind == 'level':
        say(a + 0.3, f'Level {data}: {LEVEL_NAME[LEVELS[data - 1][0]].lower()}!')
    elif kind == 'q':
        say(a + THINK + 0.15, data[1]['name'] + '!')
    elif kind == 'outro':
        say(a + 0.2, 'How many did you get? Comment your score!' if not LONG else
            f'How many did you get out of {len(QS)}? Comment your score, and subscribe for a new quiz every week!')
duck = np.convolve(duck, np.ones(2205) / 2205, 'same')
mix = mix + mus * duck
mix = mix / max(1.0, np.abs(mix).max() / 0.6)
wav = OUT + '.wav'; sf.write(wav, np.stack([mix, mix], 1)[:int(T * SR)], SR, subtype='FLOAT')

enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', wav, '-af', 'loudnorm=I=-15:TP=-2:LRA=9,aresample=48000,lowpass=f=15500,alimiter=limit=0.6:level=false',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '20' if not LONG else '22', '-pix_fmt', 'yuv420p',
                        '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for n in range(N):
    enc.stdin.write(np.asarray(frame(n / FPS).convert('RGB'), np.uint8).tobytes())
enc.stdin.close(); enc.wait(); os.remove(wav)
chapters = []
if LONG:
    for kind, a, b_, data in segs:
        if kind == 'intro': chapters.append((a, 'Intro'))
        elif kind == 'level': chapters.append((a, f'Level {data}: {LEVEL_NAME[LEVELS[data - 1][0]].title()}'))
        elif kind == 'outro': chapters.append((a, 'Your score'))
json.dump(dict(mode=MODE, seed=SEED, questions=[dict(n=i + 1, flag=q['code'], answer=q['name'], options=q['options'], tier=q['tier']) for i, q in enumerate(QS)],
               chapters=[f'{int(a // 60)}:{int(a % 60):02d} {t_}' for a, t_ in chapters], length=round(T, 1)), open(OUT + '.json', 'w'), indent=1)
print('quiz', MODE, OUT, round(T, 1), 's', [q['name'] for q in QS][:8], flush=True)
