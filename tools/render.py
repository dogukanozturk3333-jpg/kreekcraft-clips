#!/usr/bin/env python3
"""Render vertical 1080x1920 streamer clips with the Zeipan edit package (brand.yaml):
brand frame + channel badge, "<Streamer> • GTA 6 • Day N" context strip, facecam/overlay panel on top
(never zoomed or blurred, so the streamer's overlay stays visible), gameplay below with 1.2x punch-ins on
reaction peaks, own hook line, word-highlighted captions, punchline sound effects, and an ending that
replays the main moment zoomed at 0.5x with the twitch.tv CTA so the Short loops.

usage: render.py <workdir> <clips.json> [clip names...]
  <workdir>/tx|txm/<clip.tx>.json   whisper transcripts with word timestamps
  <workdir>/out/<name>.mp4          output
  BRAND=<path> overrides ../brand.yaml
"""
import datetime, json, os, re, subprocess, sys
from zoneinfo import ZoneInfo

import yaml

S = sys.argv[1]
CFG = json.load(open(sys.argv[2]))
ONLY = set(sys.argv[3:])
OUT = S + '/out'
os.makedirs(OUT, exist_ok=True); os.makedirs(S + '/ass', exist_ok=True)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND = yaml.safe_load(open(os.environ.get('BRAND', REPO + '/brand.yaml')))

END = 2.5          # end card seconds when a clip turns the replay off
SEAM = 860         # bottom edge of the facecam panel
W, H = 1080, 1920
FW = BRAND['frame']['width'] if BRAND['frame'].get('enabled', True) else 0
TOP = BRAND['top_bar']['height']

def ass_col(hexrgb, alpha='00'):
    h = hexrgb.lstrip('#')
    return f'&H{alpha}{h[4:6]}{h[2:4]}{h[0:2]}'.upper()

FRAME_C = BRAND['frame']['color'].lstrip('#')
ACCENT_C = BRAND['frame']['accent'].lstrip('#')

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

def src_path(clip):
    p = clip['src']
    return p if os.path.isabs(p) else os.path.join(S, p)

def probe_size(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                          'stream=width,height', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout
    w, h = out.strip().split(',')[:2]
    return int(w), int(h)

def streamer(clip):
    return BRAND['streamers'].get(clip.get('streamer', ''), {})

def day_number(clip):
    if 'day' in clip:
        return clip['day']
    st = streamer(clip)
    if not st or 'created' not in clip:
        return None
    tz = ZoneInfo(BRAND['context'].get('timezone', 'UTC'))
    created = datetime.datetime.fromisoformat(clip['created'].replace('Z', '+00:00')).astimezone(tz).date()
    day1 = st['day1'] if isinstance(st['day1'], datetime.date) else datetime.date.fromisoformat(str(st['day1']))
    return (created - day1).days + 1

def raw_bleeps(clip, D0):
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
                    if b > 0 and a < D0:
                        spans.append([max(0, a), min(D0, b)])
    spans += [list(x) for x in clip.get('bleep', [])]   # manual extra spans (clip time)
    return spans

def merge(spans):
    spans = sorted(s for s in spans if s[1] - s[0] > 0.04); out = []
    for a, b in spans:
        if out and a <= out[-1][1] + 0.05:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out

def ts(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f'{h}:{m:02d}:{s:05.2f}'

# ---------- our own edit: dead-air cuts, punch-in zooms, sfx, replay ----------
def load_pcm(clip, sr=8000):
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(clip['start']), '-t', str(clip['end'] - clip['start']),
                          '-i', src_path(clip), '-vn', '-ac', '1', '-ar', str(sr), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(float), sr

def loudness(clip):
    """dB per 0.1 s window over the clip range (clip time)."""
    import numpy as np
    x, sr = load_pcm(clip)
    win = int(sr * 0.1)
    if len(x) < win * 20:
        return None
    rms = np.sqrt(np.convolve(x ** 2, np.ones(win) / win, mode='valid')[::win] + 1)
    return 20 * np.log10(rms)

def keep_segments(clip, D0):
    """Cut silent stretches (> 1 s, below -32 dB) down to 0.35 s; never touch the first 1 s / last 1 s."""
    if not clip.get('fx', True) or not clip.get('trim_silence', True):
        return [[0, D0]]
    out = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-ss', str(clip['start']), '-t', str(D0),
                          '-i', src_path(clip), '-vn', '-af', 'silencedetect=n=-32dB:d=1.0', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', out)]
    en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', out)]
    cuts = []
    for a, b in zip(st, en):
        a, b = max(a + 0.175, 1.0), min(b - 0.175, D0 - 1.0)
        if b - a > 0.3:
            cuts.append([a, b])
    for a, b in clip.get('drop_video', []):     # manual cuts (source-file seconds)
        cuts.append([a - clip['start'], b - clip['start']])
    cuts = merge(cuts)
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

def find_peaks(clip, db, keep, remap, D):
    """Loudest reaction moments (output time) for the punch-in zooms."""
    import numpy as np
    rz = BRAND['reaction_zoom']
    if not clip.get('fx', True) or db is None:
        return []
    if 'zooms' in clip:                                  # manual reaction times (clip time)
        return sorted(remap(t - clip['start']) for t in clip['zooms'])   # source-file seconds
    thr = max(np.percentile(db, 88), db.mean() + 1.0 * db.std())
    peaks = []
    for i in np.argsort(-db):
        t = i * 0.1
        if db[i] < thr or not any(a <= t <= b for a, b in keep):
            continue
        tn = remap(t)
        if tn < 1.5 or tn > D - 1.0 or any(abs(tn - p) < rz['min_gap'] for p in peaks):
            continue
        peaks.append(tn)
        if len(peaks) >= max(1, int(D / rz['per_seconds'])):
            break
    return sorted(peaks)

def replay_range(clip, db, D0):
    """Clip-time range replayed at the end: clip['replay'] or a window around the loudest moment."""
    rp = clip.get('replay', True)
    if rp is False or not BRAND['replay'].get('enabled', True):
        return None
    if isinstance(rp, list):                           # source-file seconds
        return [max(0.0, rp[0] - clip['start']), min(D0, rp[1] - clip['start'])]
    L = BRAND['replay']['length']
    p = (int(db.argmax()) * 0.1) if db is not None else D0 / 2
    a = max(0.0, min(p - 0.65 * L, D0 - L))
    return [a, min(D0, a + L)]

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

def build_ass(clip, D, T, remap, seam, has_logo, replay):
    st = streamer(clip)
    sname = st.get('name', '')
    twitch = st.get('twitch', 'twitch.tv/kreekcraft')
    hi = ass_col(ACCENT_C)
    words = load_words(clip)
    for w in words:
        w['t0'], w['t1'] = remap(w['t0']), remap(w['t1'])
    words = [w for w in words if w['t1'] > w['t0']]
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
                    parts.append(r'{\c' + hi + r'&}' + esc(x['w']) + r'{\c&H00FFFFFF&}')
                else:
                    parts.append(esc(x['w']))
            pop = r'{\fscx108\fscy108\t(0,90,\fscx100\fscy100)}' if wi == 0 else ''
            pop = r'{\pos(540,%d)}' % clip.get('cap_y', 1320) + pop
            ev.append(f"Dialogue: 1,{ts(a)},{ts(b)},Cap,,0,0,0,,{pop}{' '.join(parts)}")
    # hook: our own line, never the Twitch clip title
    hook = clip['hook'].replace('|', r'\N')
    hd = clip.get('hook_dur', 3.2)
    ev.append(f"Dialogue: 5,{ts(0)},{ts(hd)},Hook,,0,0,0,,"
              r"{\pos(540," + str(seam + 185) + r")\fad(0,150)}" + hook)
    # brand top bar: channel badge (unless a logo image is overlaid) + context strip
    yb = FW + TOP // 2
    if not has_logo:
        ev.append(f"Dialogue: 7,{ts(0)},{ts(T)},Badge,,0,0,0,,"
                  r"{\an4\pos(" + str(FW + 26) + ',' + str(yb) + r")}" + BRAND['channel']['name'])
    day = day_number(clip)
    if sname and day:
        ctx = BRAND['context']['template'].format(streamer=sname, day=day)
        if BRAND['context'].get('uppercase', True):
            ctx = ctx.upper()
        ev.append(f"Dialogue: 7,{ts(0)},{ts(T)},Ctx,,0,0,0,,"
                  r"{\an6\pos(" + str(W - FW - 26) + ',' + str(yb) + r")}" + ctx)
    ev.append(f"Dialogue: 2,{ts(0)},{ts(T)},Tag,,0,0,0,,"
              r"{\pos(540,1850)}" + clip.get('tag', f'LIVE ON {twitch.upper()}'))
    # ending (replay or plain end card): overlay is never covered, CTA sits on the gameplay
    cta = BRAND['end_cta']
    title = clip.get('end_title', cta['title'].format(NAME=sname.upper() or 'KREEKCRAFT'))
    if replay:
        ev.append(f"Dialogue: 6,{ts(D)},{ts(T)},Rpl,,0,0,0,,"
                  r"{\an8\pos(540," + str(seam + 34) + r")\fad(120,0)}" + BRAND['replay']['label'])
    ev.append(f"Dialogue: 6,{ts(D)},{ts(T)},EndS,,0,0,0,,"
              r"{\pos(540,1440)\fad(150,0)}" + title)
    ev.append(f"Dialogue: 6,{ts(D)},{ts(T)},EndL,,0,0,0,,"
              r"{\pos(540,1565)\fad(150,0)\fscx70\fscy70\t(0,200,\fscx100\fscy100)}"
              + clip.get('end_link', twitch))
    ev.append(f"Dialogue: 6,{ts(D)},{ts(T)},EndS,,0,0,0,,"
              r"{\pos(540,1685)\fad(150,0)\fs46}" + cta['sub'])
    fc, ac = ass_col(FRAME_C), ass_col(ACCENT_C)
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
Style: Tag,Inter Black,38,&H00FFFFFF,&H00FFFFFF,{fc},{fc},0,0,0,0,100,100,1,0,3,10,0,5,40,40,0,1
Style: Badge,Inter Black,44,&H00FFFFFF,&H00FFFFFF,{fc},{fc},0,0,0,0,100,100,3,0,3,12,0,4,40,40,0,1
Style: Ctx,Inter Black,32,&H00FFFFFF,&H00FFFFFF,&H50000000,&H50000000,0,0,0,0,100,100,1,0,3,12,0,6,40,40,0,1
Style: Rpl,Inter Black,40,&H00000000,&H00000000,{ac},{ac},0,0,0,0,100,100,2,0,3,10,0,8,40,40,0,1
Style: EndS,Inter Black,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,6,3,5,40,40,0,1
Style: EndL,Inter Black,92,&H00FFFFFF,&H00FFFFFF,{fc},{fc},0,0,0,0,100,100,0,0,3,26,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    return head + '\n'.join(ev) + '\n'

def zoom_expr(peaks, D, replay):
    rz, rp = BRAND['reaction_zoom'], BRAND['replay']
    hold, rel = rz['hold'], rz['release']
    terms = [f"if(between(it-{p - 0.08:.2f},0,{hold}),1,if(between(it-{p - 0.08:.2f},{hold},{hold + rel}),"
             f"({hold + rel}-(it-{p - 0.08:.2f}))/{rel},0))" for p in peaks]
    main = f"1+{rz['scale'] - 1:.3f}*({'+'.join(terms)})" if terms else '1'
    if not replay:
        return main
    return f"if(gte(it,{D:.3f}),1+{rp['zoom'] - 1:.3f}*min(1,(it-{D:.3f})/0.35),{main})"

def render(clip):
    src = src_path(clip)
    sw, sh = probe_size(src)
    D0 = clip['end'] - clip['start']
    keep = keep_segments(clip, D0)
    remap = make_remap(keep)
    D = round(sum(b - a for a, b in keep), 3)
    db = loudness(clip) if clip.get('fx', True) else None
    peaks = find_peaks(clip, db, keep, remap, D)
    rr = replay_range(clip, db, D0)
    speed = BRAND['replay']['speed']
    RD = (rr[1] - rr[0]) / speed if rr else END
    T = round(D + RD, 3)
    seam = clip.get('seam', SEAM)
    logo = os.path.join(REPO, BRAND['channel'].get('logo') or '')
    has_logo = bool(BRAND['channel'].get('logo')) and os.path.isfile(logo)
    ass = f"{S}/ass/{clip['name']}.ass"
    open(ass, 'w').write(build_ass(clip, D, T, remap, seam, has_logo, bool(rr)))

    inputs = ['-i', src]
    if rr:
        inputs += ['-ss', f"{clip['start'] + rr[0]:.3f}", '-t', f'{rr[1] - rr[0]:.3f}', '-i', src]
    nin = 2 if rr else 1

    cut = len(keep) > 1
    sel = '+'.join(f'between(t,{a:.3f},{b:.3f})' for a, b in keep)
    vsel = f"select='{sel}',setpts=N/30/TB," if cut else ''
    asel = f"aselect='{sel}',asetpts=N/SR/TB," if cut else ''
    print(clip['name'], f'length {D0:.1f}s -> {D:.1f}s, cuts {len(keep) - 1}, zooms at {[round(float(p), 2) for p in peaks]}, '
          f'replay {rr} -> {RD:.1f}s, total {T:.1f}s', flush=True)

    full = clip.get('layout') == 'full'
    cx, cy, cw, ch = clip.get('cam', [0, 0.0, 0.23, 0.6])          # facecam + overlay crop (fractions)
    gx, gyy, gw, gh = clip.get('game', [0.272, 0.03, 0.456, 0.84])  # gameplay crop (fractions)
    GH = H - seam
    if full:
        GW_, GH_ = W, (round(W * sh / sw) // 2) * 2
        gy = seam + (GH - GH_) // 2
        game = f"[v3]scale={W}:{GH_}:flags=lanczos"
    else:
        GW_, GH_, gy = W, GH, seam
        game = (f"[v3]crop=iw*{gw}:ih*{gh}:iw*{gx}:ih*{gyy},"
                f"scale={W}:{GH}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{GH}")
    z = zoom_expr(peaks if clip.get('fx', True) else [], D, bool(rr))
    if z != '1':
        game += (f",zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih*0.45-(ih/zoom*0.45)'"
                 f":d=1:s={GW_}x{GH_}:fps=30")
    if rr:
        vin = (f"[0:v]trim=start={clip['start']}:end={clip['end']},setpts=PTS-STARTPTS,fps=30,{vsel}setsar=1[mv];"
               f"[1:v]setpts=(PTS-STARTPTS)/{speed},fps=30,setsar=1[rv];"
               f"[mv][rv]concat=n=2:v=1:a=0,split=3[v1][v2][v3];")
    else:
        vin = (f"[0:v]trim=start={clip['start']}:end={clip['end']},setpts=PTS-STARTPTS,fps=30,{vsel}"
               f"tpad=stop_mode=clone:stop_duration={END},setsar=1,split=3[v1][v2][v3];")
    camh = seam - FW - TOP
    bar = (f"drawbox=x={FW}:y=ih-{FW + 12}:w='(iw-{2 * FW})*t/{D}':h=12:color=0x{ACCENT_C}@0.95:t=fill"
           f":enable='lt(t,{D})'," if clip.get('fx', True) else '')
    border = f"drawbox=x=0:y=0:w=iw:h=ih:color=0x{FRAME_C}:t={FW}," if FW else ''
    fc = (
        vin +
        f"[v1]crop=ih*9/16:ih,scale={W}:{H},gblur=sigma=40,eq=brightness=-0.15[bg];"
        f"[v2]crop=iw*{cw}:ih*{ch}:iw*{cx}:ih*{cy},"
        f"scale=w={W - 2 * FW}:h={camh}:force_original_aspect_ratio=decrease:flags=lanczos,"
        f"scale=trunc(iw/2)*2:trunc(ih/2)*2[cam];"
        f"{game}[game];"
        f"[bg][cam]overlay=x=(W-w)/2:y={FW + TOP}+({camh}-h)/2[t1];[t1][game]overlay=0:{gy},"
        f"unsharp=5:5:0.6:5:5:0.0,drawbox=x=0:y={seam - 3}:w=iw:h=6:color=0x{FRAME_C}:t=fill,"
        f"{border}{bar}ass={ass},format=yuv420p[vb]"
    )
    if has_logo:
        inputs += ['-loop', '1', '-i', logo]
        fc += (f";[{nin}:v]scale=-1:{TOP - 30},format=rgba[lg];"
               f"[vb][lg]overlay=x={FW + 22}:y={FW}+({TOP}-h)/2:shortest=1[v]")
        nin += 1
    else:
        fc += ';[vb]null[v]'

    # ---- audio: main (+ slowed replay), loudness, effects, bleeps ----
    if rr:
        fc += (f";[0:a]atrim=start={clip['start']}:end={clip['end']},asetpts=PTS-STARTPTS,{asel}"
               f"aresample=48000,aformat=channel_layouts=stereo[ma];"
               f"[1:a]asetpts=PTS-STARTPTS,atempo={speed},aresample=48000,aformat=channel_layouts=stereo[ra];"
               f"[ma][ra]concat=n=2:v=0:a=1,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,"
               f"aformat=channel_layouts=stereo,afade=t=out:st={T - 0.6:.3f}:d=0.6,apad=whole_dur={T}[a00]")
    else:
        fc += (f";[0:a]atrim=start={clip['start']}:end={clip['end']},asetpts=PTS-STARTPTS,{asel}"
               f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo,"
               f"afade=t=out:st={D - 0.4}:d={0.4 + END * 0.6},apad=whole_dur={T}[a00]")
    fx = []          # (label, start time in output)
    rz = BRAND['reaction_zoom']
    if peaks and rz.get('whoosh', True):
        n = len(peaks)
        fc += (f";anoisesrc=d=0.45:c=pink:r=48000:a=0.5,highpass=f=300,lowpass=f=6500,"
               f"afade=t=in:d=0.2,afade=t=out:st=0.2:d=0.25,aformat=channel_layouts=stereo,volume=0.55,"
               f"asplit={n}" + ''.join(f'[w{i}]' for i in range(n)))
        fx += [(f'w{i}', p - 0.28) for i, p in enumerate(peaks)]
    sfx_dir = os.path.join(REPO, BRAND['sfx']['dir'])
    vol = BRAND['sfx'].get('volume', 0.8)
    hits = [(remap(t - clip['start']), name) for t, name in clip.get('sfx', [])]   # source-file seconds
    if rr and BRAND['replay'].get('sfx'):
        hits.append((D - 0.05, BRAND['replay']['sfx']))
    for k, (t, name) in enumerate(hits):
        inputs += ['-i', os.path.join(sfx_dir, name + '.wav')]
        fc += (f";[{nin}:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol}[s{k}]")
        fx.append((f's{k}', t))
        nin += 1
    if fx:
        fc += ';' + ';'.join(f"[{lab}]adelay={max(0, int(t * 1000))}:all=1[d{lab}]" for lab, t in fx)
        fc += (';[a00]' + ''.join(f'[d{lab}]' for lab, _ in fx) +
               f"amix=inputs={len(fx) + 1}:normalize=0:duration=first[a0]")
    else:
        fc += ';[a00]anull[a0]'
    raw = raw_bleeps(clip, D0)
    spans = [[remap(a), remap(b)] for a, b in raw]
    if rr:
        ra, rb = rr
        spans += [[D + (max(a, ra) - ra) / speed, D + (min(b, rb) - ra) / speed] for a, b in raw if b > ra and a < rb]
    spans = merge(spans)
    if spans:
        on = '+'.join(f'between(t,{a:.2f},{b:.2f})' for a, b in spans)
        fc += (f";[a0]volume=0:enable='{on}'[am];"
               f"sine=f=1000:sample_rate=48000:duration={T},volume=1.6,"
               f"volume=0:enable='not({on})'[bp];"
               f"[am][bp]amix=inputs=2:normalize=0:duration=first[a]")
    else:
        fc += ";[a0]anull[a]"
    print(clip['name'], 'bleeps:', [(round(a, 2), round(b, 2)) for a, b in spans],
          'sfx:', [(round(t, 2), n) for t, n in hits], flush=True)
    out = f"{OUT}/{clip['name']}.mp4"
    cmd = ['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', fc,
           '-map', '[v]', '-map', '[a]', '-t', f'{T}',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-maxrate', '11M', '-bufsize', '22M',
           '-profile:v', 'high', '-level', '4.1', '-r', '30', '-g', '60',
           '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    print('rendered', out, os.path.getsize(out) // 1024 // 1024, 'MB', flush=True)

for c in CFG:
    if ONLY and c['name'] not in ONLY:
        continue
    render(c)
