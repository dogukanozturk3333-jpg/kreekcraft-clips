#!/usr/bin/env python3
"""ZEIPAN — satisfying physics simulations for Shorts ("which colour wins?"). Everything is simulated and drawn
here (no footage, no images, no third-party audio), so there is no copyright risk.
  python3 -I zeipan/sim.py TYPE SEED OUT.mp4
TYPE:
  grow    one ball bounces inside a ring and grows a little on every bounce until it fills the ring
  escape  four coloured balls bounce inside a spinning ring with a gap — the first one out wins
  race    six marbles race down a peg board — the first one across the finish line wins
The whole run is simulated first (so the outcome is known and the length can be checked), then rendered.
A seed is accepted only if the run ends inside the Shorts-friendly window; otherwise the next seed is tried."""
import os as _os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): _os.environ.setdefault(_v, '1')
import sys, os, math, json, functools, subprocess, numpy as np, cv2, soundfile as sf
cv2.setNumThreads(1)
from PIL import Image, ImageDraw, ImageFont, ImageFilter

KIND, SEED, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
W, H, FPS, SR, SUB = 1080, 1920, 30, 44100, 16          # 16 physics steps per frame
DT = 1.0 / (FPS * SUB)
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
YEL = (255, 229, 0); BGC = np.array([15, 11, 11], np.float32)          # brand: yellow #FFE500 on near-black (BGR here)
COLS = {'RED': (70, 60, 255), 'BLUE': (255, 150, 40), 'GREEN': (90, 220, 60), 'YELLOW': (0, 229, 255),
        'PURPLE': (230, 80, 170), 'ORANGE': (30, 150, 255)}            # BGR for OpenCV
CX, CY = W // 2, 1000


@functools.lru_cache(None)
def font(name, s):
    return ImageFont.truetype(subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout, s)


@functools.lru_cache(None)
def text_layer(lines):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for y, txt, s, col in lines:
        d.text((W // 2, y), txt, font=font('Inter Black', s), fill=col + (255,), anchor='mm', stroke_width=6, stroke_fill=(0, 0, 0, 255))
    return np.asarray(im, np.float32)


@functools.lru_cache(None)
def brand_layer():
    """Small, faint Z logo + ZEIPAN at the bottom — present on every frame, never over the action."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    lg = Image.open(os.path.join(REPO, 'brand', 'art', 'logo.png')).convert('RGBA').resize((44, 44), Image.LANCZOS)
    lg.putalpha(lg.getchannel('A').point(lambda v: v * 150 // 255)); d = ImageDraw.Draw(im)
    f = font('Inter Black', 30); tw = d.textlength('ZEIPAN', font=f); x0 = int(W / 2 - (44 + 12 + tw) / 2)
    im.alpha_composite(lg, (x0, 1780 - 22)); d.text((x0 + 56, 1780), 'ZEIPAN', font=f, fill=YEL + (130,), anchor='lm')
    return np.asarray(im, np.float32)


def over(f, L):   # f is BGR float, L is an RGBA float layer
    a = L[..., 3:4] / 255.0
    return f * (1 - a) + L[..., [2, 1, 0]] * a


# ------------------------------------------------------------------ simulations (return frames of states + events)
def sim_grow(seed):
    rng = np.random.default_rng(seed); R = 430.0; g = 1500.0
    p = np.array([CX + rng.uniform(-60, 60), CY - 200.0]); v = np.array([rng.uniform(-500, 500), 0.0]); r = 26.0
    frames, events, bounces, t = [], [], 0, 0.0
    while t < 60:
        for _ in range(SUB):
            v[1] += g * DT; p += v * DT; t += DT
            d = p - [CX, CY]; dist = np.linalg.norm(d)
            if dist + r > R:
                n = d / dist; vn = v @ n
                if vn > 0:                                                       # a real bounce (moving outward)
                    v = v - 2 * vn * n
                    sp = np.linalg.norm(v); v = v / sp * max(sp, 1100.0)          # keep it lively
                    r = min(R - 2, r + 5.0); bounces += 1; events.append((t, bounces))
                p = np.array([CX, CY]) + n * (R - r)                             # always back inside, also after growing
        frames.append(dict(t=t, balls=[(p[0], p[1], r, 'YELLOW')], bounces=bounces, R=R))
        if r >= R - 4: break
    return frames, events, dict(bounces=bounces)


def sim_escape(seed):
    rng = np.random.default_rng(seed); R = 420.0; g = 900.0; r = 30.0; GAP = math.radians(34); OMEGA = 1.1
    names = ['RED', 'BLUE', 'GREEN', 'YELLOW']
    P = np.array([[CX + rng.uniform(-150, 150), CY + rng.uniform(-150, 150)] for _ in names])
    V = np.array([[rng.uniform(-500, 500), rng.uniform(-500, 200)] for _ in names])
    out = [False] * 4; frames, events, winner, t, t_win = [], [], None, 0.0, None
    while t < 70:
        for _ in range(SUB):
            t += DT; gap_c = (OMEGA * t) % (2 * math.pi)
            for i in range(4):
                V[i, 1] += g * DT; P[i] += V[i] * DT
                if out[i]: continue
                d = P[i] - [CX, CY]; dist = np.linalg.norm(d)
                if dist + r > R:
                    ang = math.atan2(d[1], d[0]) % (2 * math.pi); off = (ang - gap_c + math.pi) % (2 * math.pi) - math.pi
                    if abs(off) < GAP / 2 - math.asin(min(1, r / R)):          # fully inside the gap -> through it
                        if dist > R + r:
                            out[i] = True
                            if winner is None: winner, t_win = names[i], t; events.append((t, 'win', i))
                        continue
                    n = d / dist; P[i] = np.array([CX, CY]) + n * (R - r)
                    vn = V[i] @ n
                    if vn > 0:
                        V[i] = V[i] - 2 * vn * n; sp = np.linalg.norm(V[i]); V[i] = V[i] / sp * max(sp, 900.0)
                        events.append((t, 'wall', i))
            for i in range(4):                                                  # ball-ball elastic collisions
                for j in range(i + 1, 4):
                    if out[i] or out[j]: continue
                    d = P[j] - P[i]; dist = np.linalg.norm(d)
                    if 0 < dist < 2 * r:
                        n = d / dist; rel = (V[i] - V[j]) @ n
                        if rel > 0: V[i] -= rel * n; V[j] += rel * n; events.append((t, 'hit', i))
                        ov = 2 * r - dist; P[i] -= n * ov / 2; P[j] += n * ov / 2
        frames.append(dict(t=t, balls=[(P[i, 0], P[i, 1], r, names[i]) for i in range(4)], gap=(OMEGA * t) % (2 * math.pi),
                           GAP=GAP, R=R, winner=winner))
        if t_win is not None and t > t_win + 3.0: break
    return frames, events, dict(winner=winner, t_win=t_win)


def sim_race(seed):
    rng = np.random.default_rng(seed); g = 700.0; r = 24.0; names = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'PURPLE', 'ORANGE']
    X0, X1, TOP, FIN = 90.0, W - 90.0, 470.0, 1640.0
    pegs = [(X0 + 40 + (k + (0.5 if row % 2 else 0)) * 100, 580 + row * 76) for row in range(14) for k in range(9)
            if X0 + 20 < X0 + 40 + (k + (0.5 if row % 2 else 0)) * 100 < X1 - 20]
    PEG = np.array(pegs); pr = 11.0
    P = np.array([[CX + (i - 2.5) * 70 + rng.uniform(-8, 8), TOP + 20] for i in range(6)]); V = np.zeros((6, 2))
    order, frames, events, t, t_first = [], [], [], 0.0, None
    while t < 60:
        for _ in range(SUB):
            t += DT
            for i in range(6):
                if i in order: continue
                V[i, 1] += g * DT; V[i] *= (1 - 1.2 * DT); P[i] += V[i] * DT          # a little air drag
                if P[i, 0] < X0 + r: P[i, 0] = X0 + r; V[i, 0] = abs(V[i, 0]) * 0.7
                if P[i, 0] > X1 - r: P[i, 0] = X1 - r; V[i, 0] = -abs(V[i, 0]) * 0.7
                d = P[i] - PEG; dist = np.sqrt((d ** 2).sum(1)); k = int(dist.argmin())
                if dist[k] < r + pr:
                    n = d[k] / dist[k]; P[i] = PEG[k] + n * (r + pr); vn = V[i] @ n
                    if vn < 0:
                        V[i] = V[i] - 1.55 * vn * n; V[i, 0] += rng.uniform(-60, 60); events.append((t, 'peg', i))
                if P[i, 1] > FIN:
                    order.append(i); events.append((t, 'finish', i))
                    if t_first is None: t_first = t
            for i in range(6):
                for j in range(i + 1, 6):
                    if i in order or j in order: continue
                    d = P[j] - P[i]; dist = np.linalg.norm(d)
                    if 0 < dist < 2 * r:
                        n = d / dist; rel = (V[i] - V[j]) @ n
                        if rel > 0: V[i] -= rel * n; V[j] += rel * n
                        ov = 2 * r - dist; P[i] -= n * ov / 2; P[j] += n * ov / 2
        frames.append(dict(t=t, balls=[(P[i, 0], P[i, 1], r, names[i]) for i in range(6)], order=list(order), pegs=PEG, pr=pr,
                           box=(X0, TOP, X1, FIN)))
        if t_first is not None and (len(order) == 6 or t > t_first + 4.0): break
    return frames, events, dict(winner=names[order[0]] if order else None, order=[names[i] for i in order], t_win=t_first)


def sim_rings(seed):
    rng = np.random.default_rng(seed); g = 1100.0; r = 17.0; NR = 8; GAP = math.radians(38)
    RAD = [150.0 + k * 46 for k in range(NR)]
    SPD = [(0.7 + 0.12 * k) * (1 if k % 2 == 0 else -1) * rng.uniform(0.85, 1.15) for k in range(NR)]
    PH = [rng.uniform(0, 2 * math.pi) for _ in range(NR)]
    p = np.array([CX + rng.uniform(-30, 30), CY - 40.0]); v = np.array([rng.uniform(-400, 400), -200.0])
    k, frames, events, t, t_done = 0, [], [], 0.0, None
    while t < 70:
        for _ in range(SUB):
            t += DT; v[1] += g * DT; p += v * DT
            if k >= NR: continue
            R = RAD[k]; d = p - [CX, CY]; dist = np.linalg.norm(d)
            if dist + r > R:
                gc = (PH[k] + SPD[k] * t) % (2 * math.pi); ang = math.atan2(d[1], d[0]) % (2 * math.pi)
                off = (ang - gc + math.pi) % (2 * math.pi) - math.pi
                if abs(off) < GAP / 2 - math.asin(min(1, r / R)):
                    if dist > R + r:
                        events.append((t, 'ring', k)); k += 1
                        if k == NR: t_done = t
                    continue
                n = d / dist; vn = v @ n
                if vn > 0:
                    v = v - 2 * vn * n; sp = np.linalg.norm(v); v = v / sp * min(max(sp, 950.0), 1500.0)
                    events.append((t, 'wall', 0))
                p = np.array([CX, CY]) + n * (R - r)
            if dist > 900: v *= 0
        frames.append(dict(t=t, balls=[(p[0], p[1], r, 'YELLOW')], k=k, rings=[(RAD[j], (PH[j] + SPD[j] * t) % (2 * math.pi)) for j in range(k, NR)],
                           GAP=GAP, NR=NR))
        if t_done is not None and t > t_done + 2.0: break
    return frames, events, dict(winner='YELLOW' if t_done else None, t_win=t_done, rings=NR)


SIMS = {'grow': (sim_grow, 15, 45), 'escape': (sim_escape, 10, 45), 'race': (sim_race, 7, 40), 'rings': (sim_rings, 14, 48)}
fn, lo, hi = SIMS[KIND]
for seed in range(SEED, SEED + 60):                      # accept the first seed whose run fits a Short
    frames, events, info = fn(seed)
    end_t = frames[-1]['t']
    if os.environ.get('SIMDEBUG'): print('try', seed, round(end_t, 1), {k: v for k, v in info.items() if k != 'order'}, flush=True)
    if KIND == 'grow' and lo <= end_t <= hi: break
    if KIND != 'grow' and info.get('winner') and lo <= info['t_win'] <= hi - 4: break
else:
    sys.exit('no seed fits the time window')
print('seed', seed, 'info', info, 'sim length %.1f s' % end_t)

# ------------------------------------------------------------------ titles
TITLE = {'grow': ((250, 'EVERY BOUNCE', 84, (255, 255, 255)), (350, 'IT GETS BIGGER', 84, YEL)),
         'escape': ((250, 'WHICH COLOR', 84, (255, 255, 255)), (350, 'ESCAPES FIRST?', 84, YEL)),
         'race': ((250, 'WHICH MARBLE', 84, (255, 255, 255)), (350, 'WINS THE RACE?', 84, YEL)),
         'rings': ((250, 'CAN IT ESCAPE', 84, (255, 255, 255)), (350, 'ALL 8 RINGS?', 84, YEL))}[KIND]
ENDS = 2.8                                                # end card: "who did you pick?"
T = end_t + ENDS; N = int(T * FPS)

# ------------------------------------------------------------------ render
glow_acc = np.zeros((H // 2, W // 2, 3), np.float32)
bgimg = np.zeros((H, W, 3), np.float32) + BGC + np.linspace(0, 1, H)[:, None, None] * np.array([28, 8, 18], np.float32)


def draw_state(st, final=False):
    global glow_acc
    f = bgimg.copy(); lay = np.zeros((H, W, 3), np.uint8)
    if KIND in ('grow', 'escape'):
        R = st['R']
        if KIND == 'grow':
            cv2.circle(lay, (CX, CY), int(R) + 8, (255, 255, 255), 6, cv2.LINE_AA)
        else:
            g0 = st['gap'] - st['GAP'] / 2; g1 = st['gap'] + st['GAP'] / 2
            cv2.ellipse(lay, (CX, CY), (int(R) + 8, int(R) + 8), 0, math.degrees(g1), math.degrees(g0) + 360, (255, 255, 255), 8, cv2.LINE_AA)
    if KIND == 'rings':
        for R, gc in st['rings']:
            hue = int(180 * (R - 150) / (46 * 8)); col = cv2.cvtColor(np.uint8([[[hue, 200, 255]]]), cv2.COLOR_HSV2BGR)[0, 0].tolist()
            g0 = gc - st['GAP'] / 2; g1 = gc + st['GAP'] / 2
            cv2.ellipse(lay, (CX, CY), (int(R) + 3, int(R) + 3), 0, math.degrees(g1), math.degrees(g0) + 360, col, 6, cv2.LINE_AA)
    if KIND == 'race':
        X0, TOP, X1, FIN = st['box']
        for x, y in st['pegs']: cv2.circle(lay, (int(x), int(y)), int(st['pr']), (200, 200, 200), -1, cv2.LINE_AA)
        cv2.line(lay, (int(X0), int(TOP)), (int(X0), int(FIN)), (120, 120, 120), 4); cv2.line(lay, (int(X1), int(TOP)), (int(X1), int(FIN)), (120, 120, 120), 4)
        for k in range(0, int(X1 - X0), 40):                  # chequered finish line
            c = (255, 255, 255) if (k // 40) % 2 == 0 else (40, 40, 40)
            cv2.rectangle(lay, (int(X0 + k), int(FIN)), (int(min(X1, X0 + k + 40)), int(FIN + 16)), c, -1)
    for x, y, r, nm in st['balls']:
        if -100 < x < W + 100 and -100 < y < H + 100:
            cv2.circle(lay, (int(round(x * 4)), int(round(y * 4))), int(r * 4), COLS[nm], -1, cv2.LINE_AA, 2)
    small = cv2.resize(lay, (W // 2, H // 2), interpolation=cv2.INTER_AREA).astype(np.float32)
    glow_acc = glow_acc * 0.78 + small * 0.22                 # trails
    glow = cv2.resize(cv2.GaussianBlur(glow_acc, (0, 0), 9), (W, H))
    f = f + glow * 0.9 + cv2.resize(glow_acc, (W, H)) * 0.35
    m = (lay.max(2, keepdims=True) > 0).astype(np.float32); f = f * (1 - m) + lay.astype(np.float32) * m
    return f


def render(i):
    t = i / FPS
    if t < end_t:
        st = frames[min(len(frames) - 1, int(t * FPS))]; f = draw_state(st)
        f = over(f, text_layer(TITLE))
        YMSG, SMSG = (432, 56) if KIND == 'race' else (1560, 64)              # race: between title and board, never on the pegs
        if KIND == 'rings':
            left = st['NR'] - st['k']
            msg = f'{left} RINGS LEFT' if left > 1 else ('LAST RING!' if left == 1 else 'ESCAPED!')
            f = over(f, text_layer(((1560, msg, 72 if left else 96, YEL if left <= 1 else (255, 255, 255)),)))
            if t < 3.0: f = over(f, text_layer(((1660, 'YES OR NO? COMMENT NOW!', 44, YEL),)))
        elif KIND == 'grow':
            b = st['bounces']
            f = over(f, text_layer(((1560, f"{b} BOUNCE" + ('' if b == 1 else 'S'), 64, (255, 255, 255)),)))
            if t < 3.0: f = over(f, text_layer(((1660, 'GUESS HOW MANY!', 48, YEL),)))
        elif st.get('winner') or (KIND == 'race' and st['order']):
            wn = st.get('winner') or ['RED', 'BLUE', 'GREEN', 'YELLOW', 'PURPLE', 'ORANGE'][st['order'][0]]
            c = COLS[wn]; f = over(f, text_layer(((YMSG, f'{wn} WINS!', SMSG + 30 if KIND != 'race' else SMSG, (c[2], c[1], c[0])),)))
        elif t < 3.0:
            f = over(f, text_layer(((YMSG, 'PICK A COLOR NOW!', SMSG, (255, 255, 255)),)))
    else:
        u = t - end_t; f = bgimg.copy()
        if KIND == 'rings':
            L = ((740, 'IT ESCAPED!', 110, YEL), (870, f"ALL 8 RINGS IN {info['t_win']:.1f}s", 64, (255, 255, 255)), (1000, 'did you say yes or no?', 48, (200, 200, 200)))
        elif KIND == 'grow':
            L = ((760, f"{info['bounces']} BOUNCES!", 100, YEL), (880, 'DID YOU GUESS IT?', 76, (255, 255, 255)), (1000, 'tell us your guess in the comments', 48, (200, 200, 200)))
        else:
            c = COLS[info['winner']]
            L = ((740, f"{info['winner']} WON!", 110, (c[2], c[1], c[0])), (870, 'WHO DID YOU PICK?', 76, (255, 255, 255)), (1000, 'tell us in the comments', 48, (200, 200, 200)))
        f = over(f, text_layer(L))
        if u > 0.5:
            lg = Image.open(os.path.join(REPO, 'brand', 'art', 'logo.png')).convert('RGBA').resize((200, 200), Image.LANCZOS)
            im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); im.alpha_composite(lg, (W // 2 - 100, 1180)); f = over(f, np.asarray(im, np.float32))
    return over(f, brand_layer())


# ------------------------------------------------------------------ audio: notes on bounces, fanfare on the win
mix = np.zeros(int((T + 1) * SR), np.float32)
def put(at, s, g=1.0):
    i = int(at * SR); j = min(len(mix), i + len(s)); mix[i:j] += g * s[:j - i]
def pluck(freq, dur=0.5, g=0.25):
    x = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * np.pi * freq * x) + 0.4 * np.sin(4 * np.pi * freq * x) + 0.15 * np.sin(6 * np.pi * freq * x)) * np.exp(-x * 7) * g
PENTA = [261.6, 293.7, 329.6, 392.0, 440.0]
def scale(k): return PENTA[k % 5] * (2 ** (k // 5))
last = {}
for ev in events:
    t = ev[0]
    if t > end_t: continue
    if KIND == 'grow':
        put(t, pluck(scale(min(ev[1], 24)) / 2, 0.6, 0.12))
    elif ev[1] == 'ring':
        for kk, fr in enumerate((scale(ev[2] + 5), scale(ev[2] + 7))): put(t + kk * 0.06, pluck(fr, 0.8, 0.2))
    elif ev[1] == 'win':
        for k, fr in enumerate((523.3, 659.3, 784.0, 1046.5)): put(t + k * 0.09, pluck(fr, 1.2, 0.22))
    elif ev[1] == 'finish':
        if ev[2] == frames[-1].get('order', [None])[0] if KIND == 'race' else False:
            for k, fr in enumerate((523.3, 659.3, 784.0, 1046.5)): put(t + k * 0.09, pluck(fr, 1.2, 0.22))
        else: put(t, pluck(880, 0.4, 0.15))
    else:
        i = ev[2]
        if t - last.get(i, -1) < 0.06: continue                   # no machine-gun clicks
        last[i] = t; put(t, pluck(scale(i * 2 + 3), 0.35, 0.12 if ev[1] == 'peg' else 0.16))
tt = np.arange(len(mix)) / SR
pad = (np.sin(2 * np.pi * 110 * tt) + 0.5 * np.sin(2 * np.pi * 165 * tt)) * 0.02 * np.clip(tt / 1.5, 0, 1) * np.clip((T - tt) / 1.0, 0, 1)
mix += pad.astype(np.float32)
mix = mix / max(1.0, np.abs(mix).max() / 0.6)
wav = OUT + '.wav'; sf.write(wav, np.stack([mix, mix], 1)[:int(T * SR)], SR, subtype='FLOAT')

enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-i', wav, '-af', 'loudnorm=I=-15:TP=-2:LRA=9,aresample=48000,alimiter=limit=0.7:level=false',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                        '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for i in range(N): enc.stdin.write(np.clip(render(i), 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); os.remove(wav)
json.dump(dict(kind=KIND, seed=seed, **{k: v for k, v in info.items()}), open(OUT + '.json', 'w'))
print('zeipan', KIND, OUT, round(T, 1), 's', info)
