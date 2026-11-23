#!/usr/bin/env python3
"""Brain Warp Lab long-form episode (16:9) built from finished puzzle Shorts — the format that earns watch
hours and mid-roll ads.
  python3 -I channel2/compile_long.py SPEC.json OUT.mp4
SPEC: {"title": ["30 BRAIN PUZZLES", "HOW MANY CAN YOU SOLVE?"], "episode": 1,
       "rounds": [{"name": "SHARP EYES", "items": ["channel2/oddone2/odd-004.mp4", ...]}, ...]}
Each Short sits in the middle of a 1920x1080 stage (left: puzzle counter, progress, running max score;
right: puzzle type, logo, subscribe). Voiced intro, animated round cards with sound, a score-rank card at
the end, plus OUT.chapters.txt (YouTube chapters) and OUT.thumb.jpg (thumbnail)."""
import sys, os, json, subprocess, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from bwlkit import font, logo, emoji, Audio, whoosh, chime, pop, note, ACCENT, YEL, GREEN, AMBER, RED, MAGENTA

SPEC = json.load(open(sys.argv[1])); OUT = sys.argv[2]
W, H = 1920, 1080
TMP = tempfile.mkdtemp(prefix='bwl_long_')
KIND = {'odd': ('FIND THE', 'ODD EMOJI', GREEN, 3), 'txt': ('FIND THE', 'ODD LETTER', AMBER, 3),
        'col': ('FIND THE', 'DIFFERENT COLOR', ACCENT, 3), 'math': ('EMOJI', 'MATH', YEL, 1),
        'diff': ('SPOT THE', 'DIFFERENCE', RED, 3)}
ILL = ('OPTICAL', 'ILLUSION', MAGENTA, 0)
items = [(r['name'], p) for r in SPEC['rounds'] for p in r['items']]
N = len(items); kind_of = lambda p: os.path.basename(p).split('-')[0]
MAXPTS = sum(KIND.get(kind_of(p), ILL)[3] for _, p in items)


def stage_bg():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.array([16, 9, 40], np.float32) + np.array([30, 10, 40], np.float32) * (y / H)[..., None]
    for cx, cy, r, col in ((0.15, 0.2, 0.45, (110, 50, 210)), (0.85, 0.8, 0.5, (20, 140, 160)), (0.5, 0.0, 0.35, (200, 50, 160))):
        g += np.array(col, np.float32) * 0.35 * np.exp(-(((x / W - cx) * W / H) ** 2 + (y / H - cy) ** 2) / r ** 2)[..., None]
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert('RGBA')
BG = stage_bg()


def panel(i, round_name, p, pts_so_far):
    im = BG.copy(); d = ImageDraw.Draw(im)
    sw = 608; x0 = (W - sw) // 2
    sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).rectangle([x0 - 6, -10, x0 + sw + 6, H + 10], fill=170)
    im.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(22)))
    lx = x0 // 2
    d.text((lx, 150), round_name, font=font('Inter Display SemiBold', 40), fill=ACCENT, anchor='mm')
    d.text((lx, 250), 'PUZZLE', font=font('Inter Display SemiBold', 54), fill=(200, 190, 255), anchor='mm')
    d.text((lx, 375), f'{i + 1}', font=font('Inter Black', 200), fill=(255, 255, 255), anchor='mm')
    d.text((lx, 495), f'of {N}', font=font('Inter Display SemiBold', 48), fill=(200, 190, 255), anchor='mm')
    bx0, bx1, by = lx - 230, lx + 230, 580
    d.rounded_rectangle([bx0, by, bx1, by + 26], 13, fill=(60, 45, 110))
    d.rounded_rectangle([bx0, by, bx0 + int((bx1 - bx0) * (i + 1) / N), by + 26], 13, fill=YEL)
    a, b, col, pts = KIND.get(kind_of(p), ILL)
    d.text((lx, 700), 'Keep score' if pts else 'Bonus round', font=font('Inter Display SemiBold', 44), fill=(230, 222, 255), anchor='mm')
    d.text((lx, 755), f'up to {pts} point{"s" if pts > 1 else ""} here' if pts else 'no points, just enjoy', font=font('Inter Display', 38), fill=(200, 190, 255), anchor='mm')
    d.text((lx, 870), f'max so far: {pts_so_far + pts}', font=font('Inter Display', 36), fill=(170, 160, 220), anchor='mm')
    rx = x0 + sw + (W - x0 - sw) // 2
    d.text((rx, 250), a, font=font('Inter Display SemiBold', 50), fill=(200, 190, 255), anchor='mm')
    d.text((rx, 330), b, font=font('Inter Black', 78 if len(b) < 12 else 62), fill=col, anchor='mm')
    im.alpha_composite(logo(220), (rx - 110, 500))
    d.text((rx, 780), 'BRAIN WARP LAB', font=font('Inter Black', 46), fill=(255, 255, 255), anchor='mm')
    d.rounded_rectangle([rx - 210, 830, rx + 210, 900], 35, fill=(255, 60, 80))
    d.text((rx, 866), 'SUBSCRIBE', font=font('Inter Black', 40), fill=(255, 255, 255), anchor='mm')
    return im.convert('RGB')


def card_png(lines, sub, path, top=None, small=None):
    im = BG.copy(); d = ImageDraw.Draw(im)
    im.alpha_composite(logo(170), (W // 2 - 85, 110))
    if top: d.text((W // 2, 360), top, font=font('Inter Display SemiBold', 58), fill=ACCENT, anchor='mm')
    for j, s in enumerate(lines):
        d.text((W // 2 + 5, 485 + j * 140 + 6), s, font=font('Inter Black', 124), fill=(0, 0, 0), anchor='mm')
        d.text((W // 2, 485 + j * 140), s, font=font('Inter Black', 124), fill=(255, 255, 255), anchor='mm')
    if sub: d.text((W // 2, 485 + len(lines) * 140 + 30), sub, font=font('Inter Display SemiBold', 54), fill=YEL, anchor='mm')
    if small:
        for j, s in enumerate(small): d.text((W // 2, 850 + j * 56), s, font=font('Inter Display SemiBold', 44), fill=(220, 210, 255), anchor='mm')
    im.convert('RGB').save(path)


def run(args): subprocess.run(['ffmpeg', '-v', 'error', '-y'] + args, check=True)
ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', '-r', '30',
       '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-ac', '2']


def card_video(png, dur, voice, out, music=True):
    au = Audio(dur)
    if music: au.music_bed(dur - 0.6, bpm=104)
    au.sfx_at(0, whoosh(0.5, 0.3)); au.sfx_at(0.25, chime(0.7))
    if voice: au.say(0.5, voice, speed=1.05)
    au.write(f'{out}.wav')
    run(['-loop', '1', '-t', str(dur), '-i', png, '-i', f'{out}.wav', '-filter_complex',
         f"[0:v]scale=2112:1188,zoompan=z='1+0.04*on/({int(dur * 30)})':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30,"
         f"fade=in:0:9,fade=out:st={dur - 0.3}:d=0.3[v]", '-map', '[v]', '-map', '1:a',
         '-af', 'loudnorm=I=-14:TP=-2,aresample=48000'] + ENC + ['-t', str(dur), out])
    os.remove(f'{out}.wav')


segs, chapters, t = [], [], 0.0
def add(path):
    global t
    segs.append(path); t += float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                                                 capture_output=True, text=True).stdout)

title = SPEC['title']; n_r = len(SPEC['rounds'])
card_png(title, f'{N} puzzles · {n_r} rounds · keep score', f'{TMP}/intro.png', top=f'BRAIN WARP LAB · EPISODE {SPEC.get("episode", 1)}')
card_video(f'{TMP}/intro.png', 6.5, f'Welcome to Brain Warp Lab! {N} puzzles in {n_r} rounds. Keep score, pause whenever you need, '
           f'and tell me your total at the end.', f'{TMP}/s000.mp4')
chapters.append((0, 'Intro')); add(f'{TMP}/s000.mp4')
i = 0; pts = 0
for ri, r in enumerate(SPEC['rounds']):
    card_png([f'ROUND {ri + 1}'], r['name'], f'{TMP}/r{ri}.png', small=[f'{len(r["items"])} puzzles'])
    card_video(f'{TMP}/r{ri}.png', 3.0, f'Round {ri + 1}. {r["name"].title()}.', f'{TMP}/r{ri}.mp4', music=False)
    chapters.append((t, f'Round {ri + 1}: {r["name"].title()}')); add(f'{TMP}/r{ri}.mp4')
    for p in r['items']:
        panel(i, f'ROUND {ri + 1} · {r["name"]}', p, pts).save(f'{TMP}/p{i}.png')
        o = f'{TMP}/s{i + 1:03d}.mp4'
        run(['-loop', '1', '-i', f'{TMP}/p{i}.png', '-i', p, '-filter_complex',
             '[1:v]scale=608:1080,setsar=1[s];[0:v][s]overlay=(W-w)/2:0:shortest=1[v]', '-map', '[v]', '-map', '1:a'] + ENC + [o])
        pts += KIND.get(kind_of(p), ILL)[3]; i += 1; add(o)
tiers = [(0.0, 'Beginner'), (0.4, 'Sharp Eyes'), (0.7, 'Genius'), (0.9, 'Brain Warp Master')]
lines = [f'{int(lo * MAXPTS)}{"+" if k == len(tiers) - 1 else "–" + str(int(tiers[k + 1][0] * MAXPTS) - 1)}  {name}' for k, (lo, name) in enumerate(tiers)]
card_png(['WHAT WAS', 'YOUR SCORE?'], f'max {MAXPTS} points', f'{TMP}/outro.png', small=lines)
card_video(f'{TMP}/outro.png', 9.0, f'Time to add it up! The maximum was {MAXPTS} points. Are you a beginner, sharp eyes, a genius, '
           f'or a Brain Warp master? Comment your score, and subscribe for a new episode.', f'{TMP}/s999.mp4')
chapters.append((t, 'Your score')); add(f'{TMP}/s999.mp4')
open(f'{TMP}/list.txt', 'w').write(''.join(f"file '{s}'\n" for s in segs))
run(['-f', 'concat', '-safe', '0', '-i', f'{TMP}/list.txt', '-c', 'copy', '-movflags', '+faststart', OUT])
open(OUT + '.chapters.txt', 'w').write(''.join(f'{int(c // 60)}:{int(c % 60):02d} {n}\n' for c, n in chapters))
# thumbnail (for when custom thumbnails are enabled on the channel)
th = BG.copy().convert('RGBA'); d = ImageDraw.Draw(th)
d.text((70, 120), title[0], font=font('Inter Black', 120), fill=(255, 255, 255))
d.text((70, 260), 'CAN YOU SOLVE THEM?', font=font('Inter Black', 92), fill=YEL)
for k, e in enumerate(('🍎', '🔍', '🎨', '🧠')):
    th.alpha_composite(emoji(e, 170), (90 + k * 210, 460))
th.alpha_composite(logo(300), (W - 400, 640))
th.convert('RGB').resize((1280, 720), Image.LANCZOS).save(OUT + '.thumb.jpg', quality=92)
shutil.rmtree(TMP)
print('long', OUT, N, 'puzzles', round(t / 60, 1), 'min', os.path.getsize(OUT) // 1_000_000, 'MB, max', MAXPTS, 'points')
