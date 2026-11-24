#!/usr/bin/env python3
"""ZEIPAN COUNTRY CUP — long-form episode (16:9, ~9-10 min). Six countries play 10 events: long-track marble races
(zeipan/race2.py --wide: following camera, live standings, commentary, music) and ball escapes (zeipan/sim.py
--event). After every event a voiced standings card with flags; then the champion, the season table, the outro.
  python3 -I zeipan/countrycup.py EPISODE OUT.mp4 [--teams TR,US,BR,IN,MX,ID] [--workers 2]
Season points: zeipan/country_season1.json. Checks: every event has a complete finishing order and the table is
recomputed from the raw orders before anything is written."""
import os as _os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): _os.environ.setdefault(_v, '1')
import sys, os, json, subprocess, functools, concurrent.futures as cf, numpy as np, soundfile as sf, cv2
cv2.setNumThreads(1)
from PIL import Image, ImageDraw, ImageFont

EP = int(sys.argv[1]); OUT = sys.argv[2]
CODES = (sys.argv[sys.argv.index('--teams') + 1] if '--teams' in sys.argv else 'TR,US,BR,IN,MX,ID').split(',')
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 2
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
SCR = os.environ.get('ZP_SCRATCH', '/tmp/claude-0/-home-user/d825807f-e0e5-55ce-ac85-8ebee4d46dbb/scratchpad/cup')
WORK = os.path.join(SCR, f'country-ep{EP:02d}'); os.makedirs(WORK, exist_ok=True)
SEASON = os.path.join(HERE, 'country_season1.json')
W, H, FPS, SR = 1920, 1080, 30, 48000
COUNTRIES = {'US': ('USA', '🇺🇸'), 'BR': ('BRAZIL', '🇧🇷'), 'TR': ('TURKEY', '🇹🇷'), 'IN': ('INDIA', '🇮🇳'), 'MX': ('MEXICO', '🇲🇽'),
             'ID': ('INDONESIA', '🇮🇩'), 'PH': ('PHILIPPINES', '🇵🇭'), 'DE': ('GERMANY', '🇩🇪'), 'GB': ('UK', '🇬🇧'), 'FR': ('FRANCE', '🇫🇷'),
             'JP': ('JAPAN', '🇯🇵'), 'KR': ('KOREA', '🇰🇷'), 'AR': ('ARGENTINA', '🇦🇷'), 'CA': ('CANADA', '🇨🇦'), 'IT': ('ITALY', '🇮🇹'),
             'ES': ('SPAIN', '🇪🇸'), 'PK': ('PAKISTAN', '🇵🇰'), 'NG': ('NIGERIA', '🇳🇬'), 'EG': ('EGYPT', '🇪🇬'), 'SA': ('SAUDI ARABIA', '🇸🇦')}
TEAMS = [COUNTRIES[c][0] for c in CODES]; EMOJI = {COUNTRIES[c][0]: COUNTRIES[c][1] for c in CODES}
SPOKEN = {'USA': 'the U.S.A.', 'UK': 'the U.K.'}
def spoken(n, start=False):
    s = SPOKEN.get(n, n.title()); return s[0].upper() + s[1:] if start else s
YEL = (255, 229, 0); PTS = [10, 7, 5, 3, 2, 1]
KINDS = ['race', 'escape', 'race', 'escape', 'race', 'race', 'escape', 'race', 'escape', 'race']
NEV = len(KINDS)
EVNAME = {'race': 'MARBLE RACE', 'escape': 'BALL ESCAPE'}; SAY = {'race': 'the marble race', 'escape': 'the ball escape'}
WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']
def say(n): return WORDS[n] if n < len(WORDS) else str(n)


# ------------------------------------------------------------------ 1) events
def run_event(k):
    kind = KINDS[k]; out = os.path.join(WORK, f'ev{k + 1:02d}-{kind}.mp4'); label = f'EVENT {k + 1} OF {NEV}|{EVNAME[kind]}'
    if os.path.exists(out) and os.path.exists(out + '.json'): return k, json.load(open(out + '.json'))
    seed = 20000 * EP + 53 * k + 7
    if kind == 'race':
        cmd = ['python3', '-I', os.path.join(HERE, 'race2.py'), str(seed), out, '--teams', ','.join(CODES), '--wide', '--label', label]
    else:
        cmd = ['python3', '-I', os.path.join(HERE, 'sim.py'), 'escape', str(seed), out, '--event', '--label', label, '--teams', ','.join(CODES)]
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out + '.json'): sys.exit(f'event {k + 1} failed: {r.stderr[-500:]}')
    return k, json.load(open(out + '.json'))

results = {}
with cf.ThreadPoolExecutor(WORKERS) as ex:
    for k, info in ex.map(run_event, range(NEV)):
        results[k] = info; print('event', k + 1, KINDS[k], info['order'], flush=True)
for k in range(NEV):
    assert sorted(results[k]['order']) == sorted(TEAMS), f'event {k + 1}: incomplete finishing order {results[k]["order"]}'

# ------------------------------------------------------------------ 2) points (recomputed from the raw orders)
season = json.load(open(SEASON)) if os.path.exists(SEASON) else {'teams': TEAMS, 'episodes': {}}
season['episodes'].pop(str(EP), None)
ep_pts = {t: 0 for t in TEAMS}; after = []
for k in range(NEV):
    gained = {t: PTS[results[k]['order'].index(t)] for t in TEAMS}
    for t in TEAMS: ep_pts[t] += gained[t]
    after.append((dict(gained), dict(ep_pts)))
assert sum(ep_pts.values()) == NEV * sum(PTS), 'points do not add up'


# ------------------------------------------------------------------ 3) cards
@functools.lru_cache(None)
def font(name, s):
    return ImageFont.truetype(subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout, s)


@functools.lru_cache(None)
def flag(name, d):
    fi = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
    ImageDraw.Draw(fi).text((100, 100), EMOJI[name], font=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109),
                            embedded_color=True, anchor='mm')
    fi = fi.crop(fi.getbbox()); sc = d / min(fi.width, fi.height)
    fi = fi.resize((max(d, int(fi.width * sc) + 1), max(d, int(fi.height * sc) + 1)), Image.LANCZOS)
    fi = fi.crop(((fi.width - d) // 2, (fi.height - d) // 2, (fi.width - d) // 2 + d, (fi.height - d) // 2 + d))
    mk = Image.new('L', (d * 4, d * 4), 0); ImageDraw.Draw(mk).ellipse([0, 0, d * 4 - 1, d * 4 - 1], fill=255)
    out = Image.new('RGBA', (d, d), (255, 255, 255, 255)); inner = Image.new('L', (d * 4, d * 4), 0)
    ImageDraw.Draw(inner).ellipse([int(d * 0.25), int(d * 0.25), d * 4 - int(d * 0.25) - 1, d * 4 - int(d * 0.25) - 1], fill=255)
    out.paste(fi.convert('RGB'), (0, 0), inner.resize((d, d), Image.LANCZOS)); out.putalpha(mk.resize((d, d), Image.LANCZOS))
    return out


sys.path.insert(0, os.path.join(REPO, 'channel2')); import bwlkit
KK = bwlkit.kokoro()
def voice(txt):
    s, sr = KK.create(txt, voice='am_michael', speed=1.05, lang='en-us')
    return cv2.resize(s.astype(np.float32)[None, :], (int(len(s) * SR / sr), 1), interpolation=cv2.INTER_LINEAR)[0]
def tone(f, d, g):
    x = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 4) * g
def sting(): return sum(tone(f, 1.2, 0.18) for f in (523.3, 659.3, 784.0))


def base():
    px = np.zeros((H, W, 3), np.float32) + np.array([11, 11, 15], np.float32) + np.linspace(0, 1, H)[:, None, None] * np.array([28, 8, 18], np.float32)
    im = Image.fromarray(px.astype(np.uint8)).convert('RGBA')
    lg = Image.open(os.path.join(REPO, 'brand', 'art', 'logo.png')).convert('RGBA').resize((56, 56), Image.LANCZOS)
    lg.putalpha(lg.getchannel('A').point(lambda v: v * 170 // 255)); im.alpha_composite(lg, (40, H - 90))
    ImageDraw.Draw(im).text((110, H - 62), 'ZEIPAN COUNTRY CUP', font=font('Inter Black', 28), fill=YEL + (170,), anchor='lm')
    return im


def table(im, totals, gained=None, title='STANDINGS', top=200):
    d = ImageDraw.Draw(im); d.text((W // 2, top - 90), title, font=font('Inter Black', 64), fill=(255, 255, 255), anchor='mm')
    rows = sorted(TEAMS, key=lambda t: (-totals[t], TEAMS.index(t)))
    for i, t in enumerate(rows):
        y = top + 30 + i * 112
        d.rounded_rectangle([440, y - 46, 1500, y + 46], 26, fill=(28, 24, 40) if i else (52, 44, 12))
        d.text((500, y), str(i + 1), font=font('Inter Black', 54), fill=YEL, anchor='mm')
        im.alpha_composite(flag(t, 64), (560, y - 32))
        d.text((660, y), t, font=font('Inter Black', 50 if len(t) < 9 else 40), fill=(255, 255, 255), anchor='lm')
        if gained: d.text((1150, y), f'+{gained[t]}', font=font('Inter Black', 46), fill=(130, 230, 150), anchor='mm')
        d.text((1470, y), f'{totals[t]} PTS', font=font('Inter Black', 50), fill=(255, 255, 255), anchor='rm')
    return im


def card(name, im, dur, audio):
    png = os.path.join(WORK, name + '.png'); im.convert('RGB').save(png)
    mix = np.zeros(int(dur * SR), np.float32)
    for at, s, g in audio:
        i = int(at * SR); j = min(len(mix), i + len(s)); mix[i:j] += g * s[:j - i]
    mix = mix / max(1.0, np.abs(mix).max() / 0.6); wav = os.path.join(WORK, name + '.wav')
    sf.write(wav, np.stack([mix, mix], 1), SR, subtype='FLOAT'); out = os.path.join(WORK, name + '.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', str(FPS), '-t', str(dur), '-i', png, '-i', wav,
                    '-vf', f'fade=in:0:8,fade=out:st={dur - 0.25}:d=0.25', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                    '-pix_fmt', 'yuv420p', '-r', str(FPS), '-c:a', 'aac', '-b:a', '160k', '-ar', str(SR), '-ac', '2', '-shortest', out], check=True)
    return out


segs = []
im = base(); d = ImageDraw.Draw(im)
d.text((W // 2, 210), 'ZEIPAN COUNTRY CUP', font=font('Inter Black', 112), fill=YEL, anchor='mm')
d.text((W // 2, 330), f'SEASON 1  ·  EPISODE {EP}  ·  {NEV} EVENTS', font=font('Inter Black', 52), fill=(255, 255, 255), anchor='mm')
for i, t in enumerate(TEAMS):
    x = int(W // 2 + (i - (len(TEAMS) - 1) / 2) * 260); im.alpha_composite(flag(t, 150), (x - 75, 430))
    d.text((x, 620), t, font=font('Inter Black', 38 if len(t) < 9 else 30), fill=(255, 255, 255), anchor='mm')
d.text((W // 2, 790), 'PICK YOUR COUNTRY NOW!', font=font('Inter Black', 80), fill=YEL, anchor='mm')
d.text((W // 2, 885), 'comment it before the first race', font=font('Inter Display SemiBold', 40), fill=(210, 210, 220), anchor='mm')
names_spoken = ', '.join(spoken(t) for t in TEAMS[:-1]) + ' and ' + spoken(TEAMS[-1])
v = voice(f'Welcome to the Zeipan Country Cup! {names_spoken}: {say(NEV)} events, one champion. '
          f'Pick your country now, write it in the comments, and cheer until the very end!')
segs.append((card('00-intro', im, max(9.0, len(v) / SR + 1.5), [(0.0, sting(), 1.0), (0.6, v, 1.0)]), 'Intro: pick your country'))
for k in range(NEV):
    kind = KINDS[k]
    im = base(); d = ImageDraw.Draw(im)
    d.text((W // 2, 420), f'EVENT {k + 1} OF {NEV}', font=font('Inter Black', 70), fill=(200, 200, 210), anchor='mm')
    d.text((W // 2, 560), EVNAME[kind], font=font('Inter Black', 150), fill=YEL, anchor='mm')
    v = voice(f'Event {say(k + 1)}: {SAY[kind]}!')
    segs.append((card(f'{k + 1:02d}a-title', im, max(2.6, len(v) / SR + 0.8), [(0.1, v, 1.0)]), f'Event {k + 1}: {EVNAME[kind].title()}'))
    segs.append((os.path.join(WORK, f'ev{k + 1:02d}-{kind}.mp4'), None))
    gained, tot = after[k]; winner = results[k]['order'][0]
    leader = sorted(TEAMS, key=lambda t: (-tot[t], TEAMS.index(t)))[0]
    lead_txt = (f'And {spoken(winner)} leads the cup with {tot[leader]} points.' if leader == winner
                else f'{spoken(leader, True)} still leads with {tot[leader]} points.')
    v = voice(f'{spoken(winner, True)} wins {SAY[kind]}! ' + lead_txt)
    segs.append((card(f'{k + 1:02d}c-table', table(base(), tot, gained, f'STANDINGS AFTER EVENT {k + 1}'), max(5.5, len(v) / SR + 1.2),
                      [(0.2, v, 1.0)]), None))
tot = after[-1][1]; champ = sorted(TEAMS, key=lambda t: (-tot[t], TEAMS.index(t)))[0]
im = base(); d = ImageDraw.Draw(im)
d.text((W // 2, 190), f'EPISODE {EP} CHAMPION', font=font('Inter Black', 80), fill=(255, 255, 255), anchor='mm')
im.alpha_composite(flag(champ, 340), (W // 2 - 170, 290))
d.text((W // 2, 760), champ, font=font('Inter Black', 150 if len(champ) < 9 else 110), fill=YEL, anchor='mm', stroke_width=6, stroke_fill=(0, 0, 0))
d.text((W // 2, 900), f'{tot[champ]} POINTS', font=font('Inter Black', 70), fill=(255, 255, 255), anchor='mm')
v = voice(f'And the champion of episode {say(EP)} is... {spoken(champ)}, with {tot[champ]} points! Was it your country?')
segs.append((card('90-champion', im, max(7.0, len(v) / SR + 1.5), [(0.0, sting(), 1.0), (0.8, v, 1.0)]), 'Champion'))
season['teams'] = TEAMS
season['episodes'][str(EP)] = {'points': tot, 'champion': champ, 'events': [results[k]['order'] for k in range(NEV)]}
season_tot = {t: sum(e['points'].get(t, 0) for e in season['episodes'].values()) for t in TEAMS}
v = voice('Here is the season table. Every point counts for the season title.')
segs.append((card('91-season', table(base(), season_tot, tot, 'SEASON 1 TABLE', top=220), max(6.0, len(v) / SR + 1.2), [(0.2, v, 1.0)]), 'Season table'))
im = base(); d = ImageDraw.Draw(im)
d.text((W // 2, 340), 'WHERE ARE YOU FROM?', font=font('Inter Black', 110), fill=(255, 255, 255), anchor='mm')
d.text((W // 2, 480), 'comment your country — it could race next week', font=font('Inter Display SemiBold', 50), fill=(210, 210, 220), anchor='mm')
d.text((W // 2, 660), 'NEW COUNTRY CUP EVERY SATURDAY', font=font('Inter Black', 66), fill=YEL, anchor='mm')
lg = Image.open(os.path.join(REPO, 'brand', 'art', 'logo.png')).convert('RGBA').resize((160, 160), Image.LANCZOS); im.alpha_composite(lg, (W // 2 - 80, 770))
v = voice('Where are you from? Comment your country, it could race in the next cup. Subscribe, and see you on Saturday!')
segs.append((card('99-outro', im, max(7.0, len(v) / SR + 1.5), [(0.2, v, 1.0)]), 'Outro'))

# ------------------------------------------------------------------ 4) join, loudness, chapters
lst = os.path.join(WORK, 'list.txt'); open(lst, 'w').write(''.join(f"file '{p}'\n" for p, _ in segs))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-pix_fmt', 'yuv420p', '-r', str(FPS),
                '-af', 'loudnorm=I=-15:TP=-2:LRA=9,aresample=48000,lowpass=f=15500,alimiter=limit=0.6:level=false',
                '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', OUT], check=True)
t, ch = 0.0, []
for p, title in segs:
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout)
    if title: ch.append(f'{int(t // 60)}:{int(t % 60):02d} {title}')
    t += dur
open(OUT + '.chapters.txt', 'w').write('\n'.join(ch) + '\n')
json.dump(season, open(SEASON, 'w'), indent=1)
print('country cup episode', EP, OUT, '%.1f min' % (t / 60), 'champion', champ, tot, flush=True)
