#!/usr/bin/env python3
"""Render vertical 1080x1920 KreekCraft clips: facecam+overlay top, gameplay bottom,
hook text, word-highlighted English captions, twitch.tv/kreekcraft tag + end card."""
import json, re, subprocess, sys, os

S = sys.argv[1]
CFG = json.load(open(sys.argv[2]))
ONLY = set(sys.argv[3:])
OUT = S + '/out'
os.makedirs(OUT, exist_ok=True); os.makedirs(S + '/ass', exist_ok=True)

END = 2.5          # end card seconds
SEAM = 800         # facecam panel height
W, H = 1080, 1920

CENSOR = [
    (r'\bshi+t+\b', 'SH*T'), (r'\bsheet\b', 'SH*T'), (r'\bfu\*\*', 'F**K'),
    (r'\bfuck\w*', 'F**K'), (r'\bbitch\w*', 'B*TCH'), (r'\bass\b', 'A**'),
    (r'\bdamn\b', 'D*MN'), (r'\bgoddamn\b', 'GODD*MN'), (r'\bdick\w*', 'D*CK'),
    (r'\bmotherf\w*', 'MOTHERF**KER'), (r'\bpussy\b', 'P*SSY'),
]

# Words bleeped in the AUDIO. Scanned in every transcript found for the clip
# (<S>/tx, <S>/txm and <S>/txp, the profanity-prompted one) so game dialogue
# that one model missed still gets caught.
BLEEP = re.compile(r"(shi+t|\bsheet\b|fu+c?k|fu\*|\bf\*|bitch|\bass\b|asshole|\bdick|pussy|\bcock\b|"
                   r"bastard|motherf|\*\*)", re.I)

def bleep_spans(clip, D):
    spans = []
    for model in ('tx', 'txm', 'txp', 'txp2'):
        p = f"{S}/{model}/{clip['tx']}.json"
        if not os.path.exists(p):
            continue
        for sg in json.load(open(p)):
            for w in sg.get('words', []):
                if BLEEP.search(w['word']):
                    a, b = w['start'] - clip['start'] - 0.06, w['end'] - clip['start'] + 0.06
                    if w['end'] - w['start'] < 0.15:   # zero-length timestamps
                        b = a + 0.45
                    if b > 0 and a < D:
                        spans.append([max(0, a), min(D, b)])
    spans += [list(x) for x in clip.get('bleep', [])]   # manual extra spans (clip time)
    spans.sort(); out = []
    for a, b in spans:
        if out and a <= out[-1][1] + 0.05:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out

def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'

def load_words(clip):
    words = []
    for model, a, b in clip.get('sources', [['txm', 0, 999]]):
        segs = json.load(open(f"{S}/{model}/{clip['tx']}.json"))
        for sg in segs:
            for w in sg.get('words', []):
                if a <= w['start'] < b:
                    words.append(dict(t0=w['start'], t1=w['end'], w=w['word'].strip()))
    words.sort(key=lambda x: x['t0'])
    # merge apostrophe / dash fragments into previous token
    merged = []
    for w in words:
        if merged and (w['w'].startswith("'") or w['w'] in ('-', '--')):
            merged[-1]['w'] += w['w']; merged[-1]['t1'] = w['t1']; continue
        merged.append(w)
    out = []
    for w in merged:
        if any(a <= w['t0'] < b for a, b in clip.get('drop', [])):
            continue
        if not re.search(r'[A-Za-z0-9]', w['w']):
            continue
        txt = w['w']
        txt = clip.get('replace', {}).get(txt.lower(), txt)
        for pat, rep in CENSOR:
            txt = re.sub(pat, rep, txt, flags=re.I)
        txt = re.sub(r'[,;:]+$', '', txt).replace('...', '')
        txt = re.sub(r'(?<!\w)\.$|(?<=\w)\.$', '', txt)  # drop trailing period
        w['w'] = txt.upper()
        t0, t1 = w['t0'] - clip['start'], w['t1'] - clip['start']
        if t0 < 0 or t0 >= clip['end'] - clip['start']:
            continue
        w['t0'], w['t1'] = t0, min(t1, clip['end'] - clip['start'])
        out.append(w)
    return out

def chunks(words, maxw=3, maxc=16):
    cur = []
    for w in words:
        if cur and (len(cur) >= maxw or w['t0'] - cur[-1]['t1'] > 0.6
                    or len(' '.join(x['w'] for x in cur + [w])) > maxc
                    or re.search(r'[.?!-]$', cur[-1]['w'])):
            yield cur; cur = []
        cur.append(w)
    if cur:
        yield cur

def esc(s):
    return s.replace('{', '(').replace('}', ')')

def build_ass(clip, D):
    words = load_words(clip)
    ev = []
    cs = list(chunks(words))
    for ci, ch in enumerate(cs):
        nxt = cs[ci + 1][0]['t0'] if ci + 1 < len(cs) else D
        cend = min(nxt, ch[-1]['t1'] + 0.6, D)
        for wi, w in enumerate(ch):
            a = w['t0']
            b = ch[wi + 1]['t0'] if wi + 1 < len(ch) else cend
            if b - a < 0.05:
                continue
            parts = []
            for k, x in enumerate(ch):
                if k == wi:
                    parts.append(r'{\c&H0000E5FF&}' + esc(x['w']) + r'{\c&H00FFFFFF&}')
                else:
                    parts.append(esc(x['w']))
            pop = r'{\fscx108\fscy108\t(0,90,\fscx100\fscy100)}' if wi == 0 else ''
            pop = r'{\pos(540,%d)}' % clip.get('cap_y', 1320) + pop
            ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{pop}{' '.join(parts)}")
    hook = clip['hook'].replace('|', r'\N')
    hd = clip.get('hook_dur', 3.2)
    hook_y = clip.get('seam', SEAM) + 185
    ev.append(f"Dialogue: 5,{ts(0)},{ts(hd)},Hook,,0,0,0,,"
              r"{\pos(540," + str(hook_y) + r")\fad(0,150)}" + hook)
    ev.append(f"Dialogue: 2,{ts(0)},{ts(D)},Tag,,0,0,0,,"
              r"{\pos(540,1850)}" + clip.get('tag', 'LIVE ON TWITCH.TV/KREEKCRAFT'))
    ev.append(f"Dialogue: 6,{ts(D)},{ts(D + END)},EndS,,0,0,0,,"
              r"{\pos(540,800)\fad(150,0)}" + clip.get('end_title', 'WATCH KREEKCRAFT LIVE'))
    ev.append(f"Dialogue: 6,{ts(D)},{ts(D + END)},EndL,,0,0,0,,"
              r"{\pos(540,960)\fad(150,0)\fscx70\fscy70\t(0,200,\fscx100\fscy100)}"
              + clip.get('end_link', 'twitch.tv/kreekcraft'))
    ev.append(f"Dialogue: 6,{ts(D)},{ts(D + END)},EndS,,0,0,0,,"
              r"{\pos(540,1120)\fad(150,0)\fs46}FOLLOW FOR MORE GTA 6 CLIPS")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Black,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,7,3,5,40,40,0,1
Style: Hook,Inter Black,68,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Tag,Inter Black,38,&H00FFFFFF,&H00FFFFFF,&H00FF4691,&H00FF4691,0,0,0,0,100,100,1,0,3,10,0,5,40,40,0,1
Style: EndS,Inter Black,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,5,2,5,40,40,0,1
Style: EndL,Inter Black,92,&H00FFFFFF,&H00FFFFFF,&H00FF4691,&H00FF4691,0,0,0,0,100,100,0,0,3,26,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return head + '\n'.join(ev) + '\n'

def render(clip):
    D = clip['end'] - clip['start']
    ass = f"{S}/ass/{clip['name']}.ass"
    open(ass, 'w').write(build_ass(clip, D))
    T = D + END
    full = clip.get('layout') == 'full'
    seam = clip.get('seam', SEAM)                                  # facecam panel height
    cx, cy, cw, ch = clip.get('cam', [0, 0.015, 0.225, 0.555])     # facecam crop (fractions)
    gx, gyy, gw, gh = clip.get('game', [0.272, 0.03, 0.456, 0.84])  # gameplay crop (fractions)
    gy = seam + (H - seam - 608) // 2 if full else seam
    fc = (
        f"[0:v]trim=start={clip['start']}:end={clip['end']},setpts=PTS-STARTPTS,fps=30,split=3[v1][v2][v3];"
        f"[v1]crop=ih*9/16:ih,scale={W}:{H},gblur=sigma=40,eq=brightness=-0.12[bg];"
        f"[v2]crop=iw*{cw}:ih*{ch}:iw*{cx}:ih*{cy},"
        f"scale=w={W}:h={seam}:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2[cam];"
        + (f"[v3]scale={W}:-2[game];" if full else
           f"[v3]crop=iw*{gw}:ih*{gh}:iw*{gx}:ih*{gyy},"
           f"scale={W}:{H - seam}:force_original_aspect_ratio=increase,crop={W}:{H - seam}[game];") +
        f"[bg][cam]overlay=x=(W-w)/2:y=({seam}-h)/2[t1];[t1][game]overlay=0:{gy},"
        f"drawbox=x=0:y={seam - 3}:w=iw:h=6:color=0x9146FF:t=fill,"
        f"tpad=stop_mode=clone:stop_duration={END},"
        f"gblur=sigma=28:enable='gte(t,{D})',eq=brightness=-0.28:enable='gte(t,{D})',"
        f"ass={ass},format=yuv420p[v];"
        f"[0:a]atrim=start={clip['start']}:end={clip['end']},asetpts=PTS-STARTPTS,"
        f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,"
        f"afade=t=out:st={D - 0.4}:d={0.4 + END * 0.6},apad=whole_dur={T}[a0]"
    )
    spans = bleep_spans(clip, D)
    if spans:
        on = '+'.join(f'between(t,{a:.2f},{b:.2f})' for a, b in spans)
        fc += (f";[a0]volume=0:enable='{on}'[am];"
               f"sine=f=1000:sample_rate=48000:duration={T},volume=1.6,"
               f"volume=0:enable='not({on})'[bp];"
               f"[am][bp]amix=inputs=2:normalize=0:duration=first[a]")
    else:
        fc += ";[a0]anull[a]"
    print(clip['name'], 'bleeps:', [(round(a, 2), round(b, 2)) for a, b in spans], flush=True)
    out = f"{OUT}/{clip['name']}.mp4"
    cmd = ['ffmpeg', '-v', 'error', '-y', '-i', clip['src'], '-filter_complex', fc,
           '-map', '[v]', '-map', '[a]', '-t', f'{T}',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-maxrate', '10M', '-bufsize', '20M',
           '-profile:v', 'high', '-level', '4.1', '-r', '30', '-g', '60',
           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    print('rendered', out, os.path.getsize(out) // 1024 // 1024, 'MB', flush=True)

for c in CFG:
    if ONLY and c['name'] not in ONLY:
        continue
    render(c)
