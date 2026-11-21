#!/usr/bin/env python3
"""Render vertical 1080x1920 clips with the ZEIPAN pro edit.

  python3 tools/render.py WORKDIR CONFIG.json [clip-name ...]

Three stages, streamed frame by frame:
  A  ffmpeg: layout (facecam top, gameplay bottom, blurred fill), dead-air cuts   -> raw frames
  B  python (tools/fx.py): camera push-in, punch-ins, shake, cut transitions
     (zoom / whip / glitch), zoom-blur into the end card, emoji pop-ups           -> raw frames
  C  ffmpeg: animated hook + captions (ASS), LIVE tag, progress bar, ZEIPAN brand
     layers (tools/brand.py), voice + SFX mix, H.264 encode

Per-clip config keys: name, src, tx, start, end, hook ("LINE 1|LINE 2"), and optional
seam, cam, game, layout ("full"), cap_y, tag, end_title, end_link, sources, drop,
replace, bleep, emoji (list), stickers ([[clip_time, "😂"], ...]), fx, trim_silence, brand."""
import json, re, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import brand   # ZEIPAN logo bug, branded end card, sound stings (tools/brand.py)
import fx      # camera moves, transitions, emoji pop-ups, SFX (tools/fx.py)

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

def bleep_spans(clip, D, remap=None):
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
    if remap:
        spans = [[remap(a), remap(b)] for a, b in spans]
        spans = [s for s in spans if s[1] - s[0] > 0.04]
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

# ---------- "our own edit" effects: dead-air cuts, punch-in zooms, whoosh, progress bar ----------
def load_pcm(clip, sr=8000):
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(clip['start']), '-t', str(clip['end'] - clip['start']),
                          '-i', clip['src'], '-vn', '-ac', '1', '-ar', str(sr), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(float), sr

def keep_segments(clip, D0):
    """Cut silent stretches (> min_gap s, below -32 dB) down to 0.35 s; never touch the first 1 s / last 1 s."""
    if not clip.get('fx', True) or not clip.get('trim_silence', True):
        return [[0, D0]]
    out = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-ss', str(clip['start']), '-t', str(D0),
                          '-i', clip['src'], '-vn', '-af', 'silencedetect=n=-32dB:d=1.0', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', out)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', out)]
    cuts = []
    for a, b in zip(st, en):
        a, b = max(a + 0.175, 1.0), min(b - 0.175, D0 - 1.0)
        if b - a > 0.3:
            cuts.append([a, b])
    keep, t = [], 0.0
    for a, b in cuts:
        keep.append([t, a]); t = b
    keep.append([t, D0])
    return [k for k in keep if k[1] - k[0] > 0.05]

def make_remap(keep):
    def remap(t):
        acc = 0.0
        for a, b in keep:
            if t < a:
                return acc
            if t <= b:
                return acc + t - a
            acc += b - a
        return acc
    return remap

def find_peaks(clip, keep, remap, D):
    """Loudest reaction moments (in output time) for punch-in zooms -> (sorted peaks, loudest)."""
    if not clip.get('fx', True):
        return [], None
    import numpy as np
    x, sr = load_pcm(clip)
    win = int(sr * 0.1)
    if len(x) < win * 20:
        return [], None
    rms = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, mode='valid')[::win] + 1)
    db = 20 * np.log10(rms)
    thr = max(np.percentile(db, 88), db.mean() + 1.0 * db.std())
    peaks = []
    for i in np.argsort(-db):
        t = i * 0.1
        if db[i] < thr or not any(a <= t <= b for a, b in keep):
            continue
        tn = remap(t)
        if tn < 1.5 or tn > D - 1.0 or any(abs(tn - p) < 4.0 for p in peaks):
            continue
        peaks.append(tn)
        if len(peaks) >= max(1, int(D / 7)):
            break
    return sorted(peaks), (peaks[0] if peaks else None)

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

YEL = '&H0000E5FF&'     # brand yellow #FFE500 in ASS (BGR)

def build_ass(clip, D, remap=None):
    words = load_words(clip)
    if remap:
        for w in words:
            w['t0'], w['t1'] = remap(w['t0']), remap(w['t1'])
        words = [w for w in words if w['t1'] > w['t0']]
    ev = []
    cap_y = clip.get('cap_y', 1320)
    # ---- captions: each chunk pops in, active word turns yellow + grows, chunks tilt alternately
    cs = list(chunks(words))
    for ci, ch in enumerate(cs):
        nxt = cs[ci + 1][0]['t0'] if ci + 1 < len(cs) else D
        cend = min(nxt, ch[-1]['t1'] + 0.6, D)
        tilt = (-1.5, 1.5)[ci % 2]
        for wi, w in enumerate(ch):
            a = w['t0']
            b = ch[wi + 1]['t0'] if wi + 1 < len(ch) else cend
            if b - a < 0.05:
                continue
            parts = []
            for k, x in enumerate(ch):
                if k == wi:
                    grow = '' if wi == 0 else r'\fscx112\fscy112'
                    parts.append('{\\c' + YEL + grow + '}' + esc(x['w']) + r'{\c&H00FFFFFF&\fscx100\fscy100}')
                else:
                    parts.append(esc(x['w']))
            head = r'{\pos(540,%d)\frz%.1f' % (cap_y, tilt)
            if wi == 0:
                head += r'\fscx60\fscy60\alpha&H80&\t(0,80,\fscx110\fscy110\alpha&H00&)\t(80,150,\fscx100\fscy100)'
            ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{head}}}{' '.join(parts)}")
    # ---- hook: two boxes slam in one after the other, tilted, then pop out
    lines = clip['hook'].split('|')
    hd = clip.get('hook_dur', 3.2)
    hook_y = clip.get('seam', SEAM) + 185
    ys = [hook_y] if len(lines) == 1 else [hook_y - 48, hook_y + 48]
    for i, (ln, y) in enumerate(zip(lines, ys)):
        st = 0.0 + 0.14 * i
        frz = (2.0, -2.0)[i % 2]
        dur_ms = int((hd - st) * 1000)
        anim = (r'{\pos(540,%d)\frz%d\fscx240\fscy240\alpha&HFF&'
                r'\t(0,110,\fscx94\fscy94\alpha&H00&\frz%.1f)\t(110,190,\fscx100\fscy100)'
                r'\t(%d,%d,\fscx112\fscy112\alpha&HFF&)}') % (y, frz * 6, frz, dur_ms - 140, dur_ms)
        ev.append(f"Dialogue: {5 + i},{ts(st)},{ts(hd)},{'HookW' if i == 0 else 'HookY'},,0,0,0,,{anim}{esc(ln)}")
    # ---- LIVE tag with a blinking red dot
    tag = clip.get('tag', 'LIVE ON TWITCH.TV/KREEKCRAFT')
    t, k = 0.0, 0
    while t < D:
        e = min(D, t + 0.6)
        dot = r'{\c&H3C3CFF&}●' if k % 2 == 0 else r'{\alpha&HFF&}●{\alpha&H00&}'
        ev.append(f"Dialogue: 2,{ts(t)},{ts(e)},Tag,,0,0,0,,{{\\pos(540,1850)}}{dot}{{\\c&H00FFFFFF&}} {tag}")
        t, k = e, k + 1
    # ---- end card text (brand logo + follow button are added by tools/brand.py)
    ev.append(f"Dialogue: 6,{ts(D)},{ts(D + END)},EndS,,0,0,0,,"
              r"{\move(540,850,540,800,0,260)\fad(200,0)}" + clip.get('end_title', 'WATCH KREEKCRAFT LIVE'))
    ev.append(f"Dialogue: 6,{ts(D + 0.12)},{ts(D + END)},EndL,,0,0,0,,"
              r"{\pos(540,960)\fscx40\fscy40\alpha&HFF&\t(0,160,\fscx108\fscy108\alpha&H00&)\t(160,260,\fscx100\fscy100)}"
              + clip.get('end_link', 'twitch.tv/kreekcraft'))
    ev.append(f"Dialogue: 6,{ts(D + 0.3)},{ts(D + END)},EndS,,0,0,0,,"
              r"{\pos(540,1120)\fad(250,0)\fs46}" + clip.get('end_more', 'FOLLOW FOR MORE GTA 6 CLIPS'))
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter Black,90,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,8,4,5,40,40,0,1
Style: HookW,Inter Black,70,&H00000000,&H00000000,&H00FFFFFF,&H00FFFFFF,0,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: HookY,Inter Black,70,&H00000000,&H00000000,{YEL},{YEL},0,0,0,0,100,100,0,0,3,16,0,5,40,40,0,1
Style: Tag,Inter Black,38,&H00FFFFFF,&H00FFFFFF,&H00FF4691,&H00FF4691,0,0,0,0,100,100,1,0,3,10,0,5,40,40,0,1
Style: EndS,Inter Black,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,5,2,5,40,40,0,1
Style: EndL,Inter Black,92,&H00FFFFFF,&H00FFFFFF,&H00FF4691,&H00FF4691,0,0,0,0,100,100,0,0,3,26,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return head + '\n'.join(ev) + '\n'

def stickers_for(clip, peaks, remap, seam):
    """Emoji pop-ups: explicit [[clip_time, emoji], ...] or automatic on reaction peaks."""
    xs, y = (930, 150), max(170, int(seam * 0.36))
    if 'stickers' in clip:
        times = [(remap(t) if remap else t, e) for t, e in clip['stickers']]
    else:
        em = clip.get('emoji', ['😂', '💀', '😭'])
        times = [(p, em[i % len(em)]) for i, p in enumerate(peaks[:3])]
    return [(t, e, xs[i % 2], y) for i, (t, e) in enumerate(times)]

def render(clip):
    D0 = clip['end'] - clip['start']
    keep = keep_segments(clip, D0)
    remap = make_remap(keep)
    D = round(sum(b - a for a, b in keep), 3)
    peaks, loudest = find_peaks(clip, keep, remap, D)
    cuts, acc = [], 0.0
    for a, b in keep[:-1]:
        acc += b - a; cuts.append(round(acc, 3))
    ass = f"{S}/ass/{clip['name']}.ass"
    open(ass, 'w').write(build_ass(clip, D, remap))
    T = D + END
    sel = '+'.join(f'between(t,{a:.3f},{b:.3f})' for a, b in keep)
    cut = len(keep) > 1
    vsel = f"select='{sel}',setpts=N/30/TB," if cut else ''
    asel = f"aselect='{sel}',asetpts=N/SR/TB," if cut else ''
    full = clip.get('layout') == 'full'
    branded = clip.get('brand', True)
    seam = clip.get('seam', SEAM)                                  # facecam panel height
    cx, cy, cw, ch = clip.get('cam', [0, 0.015, 0.225, 0.555])     # facecam crop (fractions)
    gx, gyy, gw, gh = clip.get('game', [0.272, 0.03, 0.456, 0.84])  # gameplay crop (fractions)
    gy = seam + (H - seam - 608) // 2 if full else seam
    stick = stickers_for(clip, peaks, remap, seam) if clip.get('fx', True) else []
    print(clip['name'], f'length {D0:.1f}s -> {D:.1f}s, cuts {cuts}, peaks {[round(p, 2) for p in peaks]}, '
          f'shake {loudest and round(loudest, 2)}, stickers {[(round(t, 2), e) for t, e, *_ in stick]}', flush=True)

    # ---- stage A: layout -> raw frames
    fcv = (
        f"[0:v]trim=start={clip['start']}:end={clip['end']},setpts=PTS-STARTPTS,fps=30,{vsel}split=3[v1][v2][v3];"
        f"[v1]crop=ih*9/16:ih,scale={W}:{H},gblur=sigma=40,eq=brightness=-0.12[bg];"
        f"[v2]crop=iw*{cw}:ih*{ch}:iw*{cx}:ih*{cy},"
        f"scale=w={W}:h={seam}:force_original_aspect_ratio=decrease:flags=lanczos,scale=trunc(iw/2)*2:trunc(ih/2)*2[cam];"
        + (f"[v3]scale={W}:-2:flags=lanczos[game];" if full else
           f"[v3]crop=iw*{gw}:ih*{gh}:iw*{gx}:ih*{gyy},"
           f"scale={W}:{H - seam}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H - seam}[game];") +
        f"[bg][cam]overlay=x=(W-w)/2:y=({seam}-h)/2[t1];[t1][game]overlay=0:{gy},"
        f"unsharp=5:5:0.6:5:5:0.0,drawbox=x=0:y={seam - 3}:w=iw:h=6:color=0x9146FF:t=fill,"
        f"tpad=stop_mode=clone:stop_duration={END},format=rgb24[v]"
    )
    A = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', clip['src'], '-filter_complex', fcv, '-map', '[v]',
                          '-t', f'{T}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)

    # ---- voice track
    fca = (f"[0:a]atrim=start={clip['start']}:end={clip['end']},asetpts=PTS-STARTPTS,{asel}"
           f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,"
           f"afade=t=out:st={D - 0.4}:d={0.4 + END * 0.6},apad=whole_dur={T}[a0]")
    spans = bleep_spans(clip, D0, remap)
    if spans:
        on = '+'.join(f'between(t,{a:.2f},{b:.2f})' for a, b in spans)
        fca += (f";[a0]volume=0:enable='{on}'[am];"
                f"sine=f=1000:sample_rate=48000:duration={T},volume=1.6,"
                f"volume=0:enable='not({on})'[bp];"
                f"[am][bp]amix=inputs=2:normalize=0:duration=first[a]")
    else:
        fca += ";[a0]anull[a]"
    print(clip['name'], 'bleeps:', [(round(a, 2), round(b, 2)) for a, b in spans], flush=True)
    voice, sfx = f"{S}/ass/{clip['name']}.voice.wav", f"{S}/ass/{clip['name']}.sfx.wav"
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', clip['src'], '-filter_complex', fca, '-map', '[a]',
                    '-t', f'{T}', '-c:a', 'pcm_s16le', voice], check=True)

    # ---- stage B plan + SFX
    beats = []
    if clip.get('fx', True):     # sentence starts after a pause, >= 3.5 s apart, away from peaks/cuts
        ws = load_words(clip)
        for w0, w1 in zip(ws, ws[1:]):
            g0, g1 = remap(w0['t1']), remap(w1['t0'])
            if g1 - g0 >= 0.3 or re.search(r'[.?!]$', w0['w']) or w0['w'].endswith('?'):
                b = g1 - 0.03
                if 3.4 <= b <= D - 2.0 and all(abs(b - x) > 1.2 for x in peaks + cuts) \
                        and all(abs(b - x) >= 3.5 for x in beats):
                    beats.append(round(b, 2))
    print(clip['name'], 'beats:', beats, flush=True)
    ed = fx.Edit(D, END, cuts if clip.get('fx', True) else [], peaks, seam, stick,
                 shake=loudest, intro=clip.get('fx', True), beats=beats)
    ed.sfx(sfx)

    # ---- stage C: text, brand, mix, encode
    bar = f"drawbox=x=0:y=ih-12:w='iw*t/{D}':h=12:color=0xFFE500@0.95:t=fill:enable='lt(t,{D})',"
    fc = (f"[0:v]vignette=angle=PI/6,{bar}ass={ass},format=yuv420p[{'vpre' if branded else 'v'}];"
          f"[1:a][2:a]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95:level=disabled"
          f"[{'apre' if branded else 'a'}]")
    extra = []
    if branded:
        fc += ';' + brand.filters(3, 'vpre', 'apre', 'v', 'a', D, seam)
        extra = brand.inputs()
    out = f"{OUT}/{clip['name']}.mp4"
    C = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', '30', '-i', '-', '-i', voice, '-i', sfx] + extra +
                         ['-filter_complex', fc, '-map', '[v]', '-map', '[a]', '-t', f'{T}',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-maxrate', '11M', '-bufsize', '22M',
                          '-profile:v', 'high', '-level', '4.1', '-r', '30', '-g', '60',
                          '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', out],
                         stdin=subprocess.PIPE)
    n, size = 0, W * H * 3
    while True:
        buf = A.stdout.read(size)
        if len(buf) < size:
            break
        C.stdin.write(ed.frame(np.frombuffer(buf, np.uint8).reshape(H, W, 3), n).tobytes())
        n += 1
    C.stdin.close(); A.wait()
    if C.wait() != 0 or A.returncode != 0:
        raise SystemExit(f"ffmpeg failed for {clip['name']}")
    print('rendered', out, n, 'frames', os.path.getsize(out) // 1024 // 1024, 'MB', flush=True)

for c in CFG:
    if ONLY and c['name'] not in ONLY:
        continue
    render(c)
