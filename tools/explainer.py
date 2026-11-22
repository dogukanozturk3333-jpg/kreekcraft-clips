#!/usr/bin/env python3
"""Overlay layer for ZEIPAN voiceover shorts (lists, guides) made from AI stills + an ElevenLabs voice.

The background (stills, blur, zoom) and the voice are put together in the ElevenLabs sandbox,
because their files can't be downloaded here. This script renders everything that goes ON TOP:
hook, section headers, location chips, word-highlighted captions, progress bar and the ZEIPAN
brand layers. It renders that layer twice, over pure black and pure white, and stacks the two
vertically (1080x3840) so the sandbox can recover exact colour + alpha:
    on black  B = a*c          on white  W = a*c + (1-a)
    final     = B + (W - B) * background
The audio track holds the sound effects only (stings, whooshes).

  python3 -I tools/explainer.py SPEC.json OUT.mp4
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brand

W, H = 1080, 1920
spec = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
D = spec['D']; END = 2.5; T = D + END
SEAM = spec.get('seam', 560)
IMG_H = spec.get('img_h', 608)
CAP_Y = spec.get('cap_y', 1500)

def ts(t):
    t = max(0, t); return f'{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}'

def words_from_runs(runs):
    """runs: [[t0, t1, "text"]] -> words with times spread by letter count."""
    out = []
    for a, b, txt in runs:
        ws = txt.split()
        wt = [len(re.sub(r'[^A-Za-z0-9]', '', w)) + 1.5 for w in ws]
        tot = sum(wt); t = a
        for w, k in zip(ws, wt):
            d = (b - a) * k / tot
            out.append(dict(w=w, t0=t, t1=t + d)); t += d
    return out

def chunks(words, maxw=3, maxc=16):
    cur = []
    for w in words:
        if cur and (len(cur) >= maxw or w['t0'] - cur[-1]['t1'] > 0.35
                    or len(' '.join(x['w'] for x in cur + [w])) > maxc
                    or re.search(r'[.?!,:]$', cur[-1]['w'])):
            yield cur; cur = []
        cur.append(w)
    if cur: yield cur

def clean(w):
    return re.sub(r'[,;:.!?]+$', '', w).upper()

ev = []
words = words_from_runs(spec['runs'])
cs = list(chunks(words))
for ci, ch in enumerate(cs):
    nxt = cs[ci + 1][0]['t0'] if ci + 1 < len(cs) else D
    cend = min(nxt, ch[-1]['t1'] + 0.5, D)
    for wi, w in enumerate(ch):
        a = w['t0']; b = ch[wi + 1]['t0'] if wi + 1 < len(ch) else cend
        parts = [(r'{\c&H0000E5FF&}' + clean(x['w']) + r'{\c&H00FFFFFF&}') if k == wi else clean(x['w'])
                 for k, x in enumerate(ch)]
        pop = r'{\fscx108\fscy108\t(0,90,\fscx100\fscy100)}' if wi == 0 else ''
        ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{{\\pos(540,{CAP_Y})}}{pop}{' '.join(parts)}")

# hook in the top area, first seconds
hd = spec.get('hook_dur', 3.4)
ev.append(f"Dialogue: 5,{ts(0)},{ts(hd)},Hook,,0,0,0,,{{\\pos(540,{SEAM // 2 + 10})\\fad(0,150)}}"
          + spec['hook'].replace('|', r'\N'))
# sections: number + name on top, location chip under the picture
for s in spec['sections']:
    a, b = s['t0'], s['t1']
    if s.get('num'):
        ev.append(f"Dialogue: 4,{ts(a)},{ts(b)},Num,,0,0,0,,{{\\pos(540,{SEAM // 2 - 70})"
                  r"\fscx40\fscy40\t(0,180,\fscx100\fscy100)}" + f"#{s['num']}")
    if s.get('title'):
        ev.append(f"Dialogue: 4,{ts(a)},{ts(b)},Title,,0,0,0,,{{\\pos(540,{SEAM // 2 + 80})\\fad(120,0)}}"
                  + s['title'].replace('|', r'\N'))
    if s.get('loc'):
        y = SEAM + IMG_H + 95
        ev.append(f"Dialogue: 4,{ts(a + 0.25)},{ts(b)},Loc,,0,0,0,,{{\\pos(540,{y})\\fad(150,0)}}"
                  + r"{\c&H0000E5FF&}LOCATION  {\c&HFFFFFF&}" + s['loc'])
ev.append(f"Dialogue: 3,{ts(0)},{ts(D)},Small,,0,0,0,,{{\\an9\\pos(1060,{SEAM + 22})}}AI ILLUSTRATION")
ev.append(f"Dialogue: 6,{ts(D)},{ts(T)},EndS,,0,0,0,,{{\\pos(540,1000)\\fad(150,0)}}"
          + spec.get('end_line', 'MORE GTA 6 GUIDES EVERY DAY'))

ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Black,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,7,3,5,40,40,0,1
Style: Hook,Inter Black,74,&H00000000,&H00000000,&H0000E5FF,&H0000E5FF,0,0,0,0,100,100,0,0,3,18,0,5,40,40,0,1
Style: Num,Inter Black,150,&H0000E5FF,&H0000E5FF,&H000F0B0B,&H80000000,0,1,0,0,100,100,0,0,1,9,4,5,40,40,0,1
Style: Title,Inter Black,66,&H00FFFFFF,&H00FFFFFF,&H000F0B0B,&H80000000,0,0,0,0,100,100,0,0,1,7,3,5,40,40,0,1
Style: Loc,Inter Black,40,&H00FFFFFF,&H00FFFFFF,&H000F0B0B,&H000F0B0B,0,0,0,0,100,100,1,0,3,16,0,5,40,40,0,1
Style: Small,Inter Black,24,&H99FFFFFF,&H99FFFFFF,&H99000000,&H00000000,0,0,0,0,100,100,1,0,1,2,0,9,0,0,0,1
Style: EndS,Inter Black,52,&H0000E5FF,&H0000E5FF,&H000F0B0B,&H80000000,0,0,0,0,100,100,1,0,1,6,2,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + '\n'.join(ev) + '\n'
work = OUT + '.work'; os.makedirs(work, exist_ok=True)
open(f'{work}/ov.ass', 'w').write(ass)

# whooshes on every section change
cuts = [s['t0'] for s in spec['sections'] if s['t0'] > 0.1]
wav = f'{work}/sfx.wav'
import numpy as np
sfx = np.zeros(int(T * brand.SR))
for i, c in enumerate(cuts):
    brand._add(sfx, brand.whoosh(0.32, 0.22, seed=10 + i), max(0, c - 0.16))
brand.write_wav(wav, sfx)

def layer(bgcol, path):
    fc = (f"color=c={bgcol}:s={W}x{H}:r=30:d={T}[c0];"
          f"[c0]drawbox=x=0:y={SEAM - 3}:w=iw:h=6:color=0xFFE500:t=fill:enable='lt(t,{D})',"
          f"drawbox=x=0:y={SEAM + IMG_H - 3}:w=iw:h=6:color=0xFFE500:t=fill:enable='lt(t,{D})',"
          f"ass={work}/ov.ass[v0];"
          f"[1:a]anull[a0];" + brand.filters(2, 'v0', 'a0', 'v', 'a', D, SEAM))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-i', wav]
                   + brand.inputs() +
                   ['-filter_complex', fc.replace('color=c=', 'color=c=', 1), '-map', '[v]', '-map', '[a]',
                    '-t', f'{T}', '-c:v', 'libx264rgb', '-crf', '0', '-preset', 'ultrafast', '-pix_fmt', 'rgb24',
                    '-c:a', 'pcm_s16le', path], check=True)

# brand.filters converts to yuv420p at the end; keep that out for the matte layers
_orig = brand.filters
brand.filters = lambda *a: _orig(*a).replace(',format=yuv420p[', ',format=rgb24[')
layer('black', f'{work}/B.mkv'); layer('white', f'{work}/W.mkv')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{work}/B.mkv', '-i', f'{work}/W.mkv',
                '-filter_complex', '[0:v][1:v]vstack[v]', '-map', '[v]', '-map', '0:a',
                '-c:v', 'libx264rgb', '-crf', '4', '-preset', 'slow', '-pix_fmt', 'rgb24', '-r', '30',
                '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT], check=True)
print('overlay', OUT, os.path.getsize(OUT) // 1024, 'KB')
