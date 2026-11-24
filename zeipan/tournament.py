#!/usr/bin/env python3
"""ZEIPAN COLOR CUP — long-form episode (16:9, ~8-12 min): six colour teams play 12 simulated events
(marble races and ball escapes). After every event a voiced standings card; at the end the episode champion,
the season table and the outro. Season points are kept in zeipan/season1.json so the series continues.
  python3 -I zeipan/tournament.py EPISODE OUT.mp4 [--events 12] [--workers 2]
All events are simulated by zeipan/sim.py --event (own physics, own drawings, own sounds, offline voice)."""
import os as _os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): _os.environ.setdefault(_v, '1')
import sys, os, json, math, subprocess, functools, concurrent.futures as cf, numpy as np, soundfile as sf, cv2
cv2.setNumThreads(1)
from PIL import Image, ImageDraw, ImageFont

EP = int(sys.argv[1]); OUT = sys.argv[2]
NEV = int(sys.argv[sys.argv.index('--events') + 1]) if '--events' in sys.argv else 12
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 2
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
SCR = os.environ.get('ZP_SCRATCH', '/tmp/claude-0/-home-user/d825807f-e0e5-55ce-ac85-8ebee4d46dbb/scratchpad/cup')
WORK = os.path.join(SCR, f'ep{EP:02d}'); os.makedirs(WORK, exist_ok=True)
SEASON = os.path.join(HERE, 'season1.json')
W, H, FPS, SR = 1920, 1080, 30, 48000
TEAMS = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'PURPLE', 'ORANGE']
RGB = {'RED': (255, 60, 70), 'BLUE': (40, 150, 255), 'GREEN': (60, 220, 90), 'YELLOW': (255, 229, 0),
       'PURPLE': (170, 80, 230), 'ORANGE': (255, 150, 30)}
YEL = (255, 229, 0); PTS = [10, 7, 5, 3, 2, 1]
EVNAME = {'race': 'MARBLE RACE', 'escape': 'BALL ESCAPE'}
SAY = {'race': 'the marble race', 'escape': 'the ball escape'}
KINDS = [('race', 'escape')[k % 2] for k in range(NEV)]


@functools.lru_cache(None)
def font(name, s):
    return ImageFont.truetype(subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout, s)


def say(n):
    return ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve'][n]


# ------------------------------------------------------------------ 1) simulate + render every event clip
def run_event(k):
    kind = KINDS[k]; out = os.path.join(WORK, f'ev{k + 1:02d}-{kind}.mp4')
    if os.path.exists(out) and os.path.exists(out + '.json'): return k, json.load(open(out + '.json'))
    seed = 10000 * EP + 37 * k + 1
    r = subprocess.run(['python3', '-I', os.path.join(HERE, 'sim.py'), kind, str(seed), out, '--event', '--label',
                        f'EVENT {k + 1} OF {NEV}|{EVNAME[kind]}'], cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out + '.json'): sys.exit(f'event {k + 1} failed: {r.stderr[-400:]}')
    return k, json.load(open(out + '.json'))

results = {}
with cf.ThreadPoolExecutor(WORKERS) as ex:
    for k, info in ex.map(run_event, range(NEV)):
        results[k] = info; print('event', k + 1, KINDS[k], info['order'], flush=True)
for k in range(NEV):
    assert sorted(results[k]['order']) == sorted(TEAMS), f'event {k + 1}: incomplete finishing order'   # every team placed once

# ------------------------------------------------------------------ 2) points
season = json.load(open(SEASON)) if os.path.exists(SEASON) else {'episodes': {}}
season['episodes'].pop(str(EP), None)
prev_total = {t: sum(e['points'][t] for e in season['episodes'].values()) for t in TEAMS}
ep_pts = {t: 0 for t in TEAMS}; after = []
for k in range(NEV):
    gained = {t: PTS[results[k]['order'].index(t)] for t in TEAMS}
    for t in TEAMS: ep_pts[t] += gained[t]
    after.append((dict(gained), dict(ep_pts)))

# ------------------------------------------------------------------ 3) cards
from kokoro_onnx import Kokoro  # noqa: F401  (bwlkit wraps it with a light, non-spinning session)
sys.path.insert(0, os.path.join(REPO, 'channel2')); import bwlkit
KK = bwlkit.kokoro()


def voice(txt):
    s, sr = KK.create(txt, voice='am_michael', speed=1.05, lang='en-us')
    return cv2.resize(s.astype(np.float32)[None, :], (int(len(s) * SR / sr), 1), interpolation=cv2.INTER_LINEAR)[0]


def tone(f, d, g):
    x = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 4) * g


def base():
    im = Image.new('RGB', (W, H), (11, 11, 15)); px = np.asarray(im, np.float32)
    px = px + np.linspace(0, 1, H)[:, None, None] * np.array([18, 8, 28], np.float32)
    im = Image.fromarray(px.astype(np.uint8)).convert('RGBA')
    lg = Image.open(os.path.join(REPO, 'brand', 'art', 'logo.png')).convert('RGBA').resize((56, 56), Image.LANCZOS)
    lg.putalpha(lg.getchannel('A').point(lambda v: v * 170 // 255)); im.alpha_composite(lg, (40, H - 90))
    ImageDraw.Draw(im).text((110, H - 62), 'ZEIPAN COLOR CUP', font=font('Inter Black', 28), fill=YEL + (170,), anchor='lm')
    return im


def table(im, totals, gained=None, title='STANDINGS', top=200):
    d = ImageDraw.Draw(im); d.text((W // 2, top - 90), title, font=font('Inter Black', 64), fill=(255, 255, 255), anchor='mm')
    rows = sorted(TEAMS, key=lambda t: (-totals[t], TEAMS.index(t)))
    for i, t in enumerate(rows):
        y = top + 30 + i * 112; c = RGB[t]
        d.rounded_rectangle([460, y - 46, 1460, y + 46], 26, fill=(28, 24, 40) if i else (52, 44, 12))
        d.text((520, y), str(i + 1), font=font('Inter Black', 54), fill=YEL, anchor='mm')
        d.ellipse([580, y - 28, 636, y + 28], fill=c); d.text((670, y), t, font=font('Inter Black', 52), fill=(255, 255, 255), anchor='lm')
        if gained: d.text((1180, y), f'+{gained[t]}', font=font('Inter Black', 46), fill=(130, 230, 150), anchor='mm')
        d.text((1380, y), f'{totals[t]} PTS', font=font('Inter Black', 50), fill=(255, 255, 255), anchor='mm')
    return im


def card(name, im, dur, lines_audio):
    png = os.path.join(WORK, name + '.png'); im.convert('RGB').save(png)
    mix = np.zeros(int(dur * SR), np.float32)
    for at, s, g in lines_audio:
        i = int(at * SR); j = min(len(mix), i + len(s)); mix[i:j] += g * s[:j - i]
    mix = mix / max(1.0, np.abs(mix).max() / 0.6); wav = os.path.join(WORK, name + '.wav')
    sf.write(wav, np.stack([mix, mix], 1), SR, subtype='FLOAT')
    out = os.path.join(WORK, name + '.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-loop', '1', '-framerate', str(FPS), '-t', str(dur), '-i', png, '-i', wav,
                    '-vf', f'fade=in:0:8,fade=out:st={dur - 0.25}:d=0.25', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
                    '-pix_fmt', 'yuv420p', '-r', str(FPS), '-c:a', 'aac', '-b:a', '160k', '-ar', str(SR), '-ac', '2', '-shortest', out], check=True)
    return out


def sting():
    return sum(tone(f, 1.2, 0.18) * (1 if k == 0 else 0.8) for k, f in enumerate((523.3, 659.3, 784.0)))


segs = []                                                     # (path, chapter title or None)
# intro
im = base(); d = ImageDraw.Draw(im)
d.text((W // 2, 230), 'ZEIPAN COLOR CUP', font=font('Inter Black', 120), fill=YEL, anchor='mm')
d.text((W // 2, 350), f'SEASON 1  ·  EPISODE {EP}  ·  {NEV} EVENTS', font=font('Inter Black', 52), fill=(255, 255, 255), anchor='mm')
for i, t in enumerate(TEAMS):
    x = W // 2 + (i - 2.5) * 250; d.ellipse([x - 70, 520 - 70, x + 70, 520 + 70], fill=RGB[t])
    d.text((x, 640), t, font=font('Inter Black', 40), fill=(255, 255, 255), anchor='mm')
d.text((W // 2, 800), 'PICK YOUR TEAM NOW!', font=font('Inter Black', 80), fill=YEL, anchor='mm')
d.text((W // 2, 890), 'comment your color before the first race', font=font('Inter Display SemiBold', 40), fill=(210, 210, 220), anchor='mm')
v = voice(f'Welcome to the Zeipan Color Cup! Six teams, {say(NEV)} events. Pick your team now, write it in the comments, '
          f'and cheer for it until the very end!')
segs.append((card('00-intro', im, max(8.0, len(v) / SR + 1.5), [(0.0, sting(), 1.0), (0.6, v, 1.0)]), 'Intro: pick your team'))
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
    im = table(base(), tot, gained, f'STANDINGS AFTER EVENT {k + 1}')
    lead_txt = f'{leader.capitalize()} leads with {tot[leader]} points.' if leader != winner else f'And {winner.lower()} leads with {tot[leader]} points.'
    v = voice(f'{winner.capitalize()} wins {SAY[kind]}! ' + lead_txt)
    segs.append((card(f'{k + 1:02d}c-table', im, max(5.5, len(v) / SR + 1.2), [(0.2, v, 1.0)]), None))
# champion
tot = after[-1][1]; champ = sorted(TEAMS, key=lambda t: (-tot[t], TEAMS.index(t)))[0]
im = base(); d = ImageDraw.Draw(im)
d.text((W // 2, 200), f'EPISODE {EP} CHAMPION', font=font('Inter Black', 80), fill=(255, 255, 255), anchor='mm')
d.ellipse([W // 2 - 170, 300, W // 2 + 170, 640], fill=RGB[champ])
d.text((W // 2, 760), champ, font=font('Inter Black', 160), fill=RGB[champ], anchor='mm', stroke_width=6, stroke_fill=(0, 0, 0))
d.text((W // 2, 900), f'{tot[champ]} POINTS', font=font('Inter Black', 70), fill=YEL, anchor='mm')
v = voice(f'And the champion of episode {say(EP)} is... {champ.lower()}, with {tot[champ]} points! Did you pick {champ.lower()}?')
segs.append((card('90-champion', im, max(7.0, len(v) / SR + 1.5), [(0.0, sting(), 1.0), (0.8, v, 1.0)]), 'Champion'))
# season table
season['episodes'][str(EP)] = {'points': tot, 'champion': champ, 'events': [results[k]['order'] for k in range(NEV)]}
season_tot = {t: sum(e['points'][t] for e in season['episodes'].values()) for t in TEAMS}
im = table(base(), season_tot, tot, 'SEASON 1 TABLE', top=220)
v = voice('Here is the season table. Every point counts for the season title.')
segs.append((card('91-season', im, max(6.0, len(v) / SR + 1.2), [(0.2, v, 1.0)]), 'Season table'))
# outro
im = base(); d = ImageDraw.Draw(im)
d.text((W // 2, 360), 'WHO WAS YOUR TEAM?', font=font('Inter Black', 110), fill=(255, 255, 255), anchor='mm')
d.text((W // 2, 500), 'tell us in the comments', font=font('Inter Display SemiBold', 54), fill=(210, 210, 220), anchor='mm')
d.text((W // 2, 680), 'NEW COLOR CUP EVERY SATURDAY', font=font('Inter Black', 70), fill=YEL, anchor='mm')
lg = Image.open(os.path.join(REPO, 'brand', 'art', 'logo.png')).convert('RGBA').resize((160, 160), Image.LANCZOS); im.alpha_composite(lg, (W // 2 - 80, 780))
v = voice('Who was your team? Tell us in the comments, subscribe, and come back on Saturday for the next Color Cup!')
segs.append((card('99-outro', im, max(7.0, len(v) / SR + 1.5), [(0.2, v, 1.0)]), 'Outro'))

# ------------------------------------------------------------------ 4) join + final loudness, chapters
lst = os.path.join(WORK, 'list.txt'); open(lst, 'w').write(''.join(f"file '{p}'\n" for p, _ in segs))
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst,
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '24', '-pix_fmt', 'yuv420p', '-r', str(FPS),
                '-af', 'loudnorm=I=-15:TP=-2:LRA=9,aresample=48000,alimiter=limit=0.7:level=false', '-c:a', 'aac', '-b:a', '160k',
                '-movflags', '+faststart', OUT], check=True)
t, ch = 0.0, []
for p, title in segs:
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p], capture_output=True, text=True).stdout)
    if title: ch.append(f'{int(t // 60)}:{int(t % 60):02d} {title}')
    t += dur
open(OUT + '.chapters.txt', 'w').write('\n'.join(ch) + '\n')
json.dump(season, open(SEASON, 'w'), indent=1)
print('color cup episode', EP, OUT, '%.1f min' % (t / 60), 'champion', champ, tot)
