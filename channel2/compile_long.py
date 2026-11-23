#!/usr/bin/env python3
"""Brain Warp Lab long-form compilation (16:9) from finished puzzle Shorts — the format that earns watch
hours and mid-roll ads. Each Short sits in the middle of a 1920x1080 stage: left panel = puzzle counter +
progress bar + "keep score", right panel = puzzle type + subscribe prompt. Title card at the start,
score/outro card at the end.
  python3 -I channel2/compile_long.py OUT.mp4 "TITLE LINE 1|TITLE LINE 2" short1.mp4 short2.mp4 ..."""
import sys, os, subprocess, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from bwlkit import font, logo, ACCENT, YEL, GREEN, AMBER, RED

OUT, TITLE, SHORTS = sys.argv[1], sys.argv[2].split('|'), sys.argv[3:]
W, H = 1920, 1080; N = len(SHORTS)
TMP = tempfile.mkdtemp(prefix='bwl_long_')
KIND = {'odd': ('FIND THE', 'ODD EMOJI', GREEN), 'txt': ('FIND THE', 'ODD LETTER', AMBER), 'col': ('FIND THE', 'DIFFERENT COLOR', ACCENT),
        'math': ('EMOJI', 'MATH', YEL), 'diff': ('SPOT THE', 'DIFFERENCE', RED), 'lilac': ('OPTICAL', 'ILLUSION', ACCENT),
        'spiral': ('OPTICAL', 'ILLUSION', ACCENT), 'troxler': ('OPTICAL', 'ILLUSION', ACCENT), 'afterimage': ('OPTICAL', 'ILLUSION', ACCENT)}


def stage_bg():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.array([16, 9, 40], np.float32) + np.array([30, 10, 40], np.float32) * (y / H)[..., None]
    for cx, cy, r, col in ((0.15, 0.2, 0.45, (110, 50, 210)), (0.85, 0.8, 0.5, (20, 140, 160)), (0.5, 0.0, 0.35, (200, 50, 160))):
        g += np.array(col, np.float32) * 0.35 * np.exp(-(((x / W - cx) * W / H) ** 2 + (y / H - cy) ** 2) / r ** 2)[..., None]
    return Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert('RGBA')

BG = stage_bg()


def panel(i, kind):
    im = BG.copy(); d = ImageDraw.Draw(im)
    # frame around the Short
    sw = 608; x0 = (W - sw) // 2
    sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).rectangle([x0 - 6, -10, x0 + sw + 6, H + 10], fill=170)
    im.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(22)))
    # left: counter
    lx = x0 // 2
    d.text((lx, 230), 'PUZZLE', font=font('Inter Display SemiBold', 54), fill=(200, 190, 255), anchor='mm')
    d.text((lx, 360), f'{i + 1}', font=font('Inter Black', 200), fill=(255, 255, 255), anchor='mm')
    d.text((lx, 480), f'of {N}', font=font('Inter Display SemiBold', 48), fill=(200, 190, 255), anchor='mm')
    bx0, bx1, by = lx - 230, lx + 230, 570
    d.rounded_rectangle([bx0, by, bx1, by + 26], 13, fill=(60, 45, 110))
    d.rounded_rectangle([bx0, by, bx0 + int((bx1 - bx0) * (i + 1) / N), by + 26], 13, fill=YEL)
    d.text((lx, 690), 'Keep score:', font=font('Inter Display SemiBold', 42), fill=(230, 222, 255), anchor='mm')
    d.text((lx, 745), '1 point per level you beat', font=font('Inter Display', 38), fill=(200, 190, 255), anchor='mm')
    d.text((lx, 860), 'Pause anytime to think', font=font('Inter Display', 38), fill=(170, 160, 220), anchor='mm')
    # right: puzzle type + subscribe
    rx = x0 + sw + (W - x0 - sw) // 2; a, b, col = KIND.get(kind, ('BRAIN', 'PUZZLE', ACCENT))
    d.text((rx, 250), a, font=font('Inter Display SemiBold', 50), fill=(200, 190, 255), anchor='mm')
    d.text((rx, 330), b, font=font('Inter Black', 78 if len(b) < 12 else 62), fill=col, anchor='mm')
    im.alpha_composite(logo(220), (rx - 110, 500))
    d.text((rx, 780), 'BRAIN WARP LAB', font=font('Inter Black', 46), fill=(255, 255, 255), anchor='mm')
    d.rounded_rectangle([rx - 210, 830, rx + 210, 900], 35, fill=(255, 60, 80))
    d.text((rx, 866), 'SUBSCRIBE', font=font('Inter Black', 40), fill=(255, 255, 255), anchor='mm')
    return im.convert('RGB')


def card(lines, sub, path):
    im = BG.copy(); d = ImageDraw.Draw(im)
    im.alpha_composite(logo(200), (W // 2 - 100, 120))
    for j, s in enumerate(lines):
        d.text((W // 2, 470 + j * 140), s, font=font('Inter Black', 120), fill=(255, 255, 255), anchor='mm')
    d.text((W // 2, 470 + len(lines) * 140 + 30), sub, font=font('Inter Display SemiBold', 54), fill=ACCENT, anchor='mm')
    im.convert('RGB').save(path)


def run(args): subprocess.run(['ffmpeg', '-v', 'error', '-y'] + args, check=True)

ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', '-r', '30',
       '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-ac', '2']
segs = []
card(TITLE, f'{N} puzzles · keep score · how many can you solve?', f'{TMP}/intro.png')
run(['-loop', '1', '-t', '4', '-i', f'{TMP}/intro.png', '-f', 'lavfi', '-t', '4', '-i', 'anullsrc=r=48000:cl=stereo',
     '-vf', 'fade=in:0:15'] + ENC + ['-shortest', f'{TMP}/s000.mp4']); segs.append(f'{TMP}/s000.mp4')
for i, sp in enumerate(SHORTS):
    kind = os.path.basename(sp).split('-')[0]
    panel(i, kind).save(f'{TMP}/p{i}.png')
    o = f'{TMP}/s{i + 1:03d}.mp4'
    run(['-loop', '1', '-i', f'{TMP}/p{i}.png', '-i', sp, '-filter_complex',
         '[1:v]scale=608:1080,setsar=1[s];[0:v][s]overlay=(W-w)/2:0:shortest=1[v]', '-map', '[v]', '-map', '1:a'] + ENC + [o])
    segs.append(o)
card(['WHAT WAS', 'YOUR SCORE?'], 'Comment it below  ·  new puzzles every day', f'{TMP}/outro.png')
run(['-loop', '1', '-t', '8', '-i', f'{TMP}/outro.png', '-f', 'lavfi', '-t', '8', '-i', 'anullsrc=r=48000:cl=stereo',
     '-vf', 'fade=out:st=7:d=1'] + ENC + ['-shortest', f'{TMP}/s999.mp4']); segs.append(f'{TMP}/s999.mp4')
open(f'{TMP}/list.txt', 'w').write(''.join(f"file '{s}'\n" for s in segs))
run(['-f', 'concat', '-safe', '0', '-i', f'{TMP}/list.txt', '-c', 'copy', '-movflags', '+faststart', OUT])
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', OUT], capture_output=True, text=True).stdout)
shutil.rmtree(TMP); print('long', OUT, N, 'puzzles', round(dur / 60, 1), 'min', os.path.getsize(OUT) // 1_000_000, 'MB')
