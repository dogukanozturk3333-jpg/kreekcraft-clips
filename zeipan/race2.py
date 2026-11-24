#!/usr/bin/env python3
"""ZEIPAN Marble Race 2.0 — a long multi-section track with a following camera, live standings, commentary and
music. Everything (physics, drawing, music, voice) is made here; no footage, no third-party audio.
  python3 -I zeipan/race2.py SEED OUT.mp4 [--teams US,BR,TR,IN,MX,ID] [--wide]
Track (top to bottom): start gate -> zig-zag ramps -> peg forest -> spinners -> final funnel -> finish line.
The race is simulated completely first (so the winner and the length are known and checked), then rendered.
--wide renders 1920x1080 (for the long-form cups) instead of the 1080x1920 Short."""
import os as _os
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): _os.environ.setdefault(_v, '1')
import sys, os, math, json, functools, subprocess, numpy as np, cv2, soundfile as sf
cv2.setNumThreads(1)
from PIL import Image, ImageDraw, ImageFont

SEED, OUT = int(sys.argv[1]), sys.argv[2]
WIDE = '--wide' in sys.argv
CODES = (sys.argv[sys.argv.index('--teams') + 1] if '--teams' in sys.argv else 'US,BR,TR,IN,MX,ID').split(',')
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
COUNTRIES = {'US': ('USA', '🇺🇸'), 'BR': ('BRAZIL', '🇧🇷'), 'TR': ('TURKEY', '🇹🇷'), 'IN': ('INDIA', '🇮🇳'), 'MX': ('MEXICO', '🇲🇽'),
             'ID': ('INDONESIA', '🇮🇩'), 'PH': ('PHILIPPINES', '🇵🇭'), 'DE': ('GERMANY', '🇩🇪'), 'GB': ('UK', '🇬🇧'), 'FR': ('FRANCE', '🇫🇷'),
             'JP': ('JAPAN', '🇯🇵'), 'KR': ('KOREA', '🇰🇷'), 'AR': ('ARGENTINA', '🇦🇷'), 'CA': ('CANADA', '🇨🇦'), 'IT': ('ITALY', '🇮🇹'),
             'ES': ('SPAIN', '🇪🇸'), 'PK': ('PAKISTAN', '🇵🇰'), 'NG': ('NIGERIA', '🇳🇬'), 'EG': ('EGYPT', '🇪🇬'), 'SA': ('SAUDI ARABIA', '🇸🇦'),
             'VN': ('VIETNAM', '🇻🇳'), 'PL': ('POLAND', '🇵🇱'), 'NL': ('NETHERLANDS', '🇳🇱'), 'PT': ('PORTUGAL', '🇵🇹'), 'RU': ('RUSSIA', '🇷🇺')}
NAMES = [COUNTRIES[c][0] for c in CODES]; FLAGS = [COUNTRIES[c][1] for c in CODES]; NB = len(NAMES)
W, VH, FPS, SUB, SR = 1080, 1920, 30, 16, 44100       # world width, viewport height (Short)
DT = 1.0 / (FPS * SUB); YEL = (255, 229, 0)
R = 27.0; G = 1500.0

# ------------------------------------------------------------------ track (world coordinates, y grows downward)
SEG = []                                               # static segments (x1, y1, x2, y2)
WL, WRt = 40.0, 1040.0
GATE_Y = 300.0
for k in range(6):                                     # zig-zag ramps: each slopes towards a gap at one wall
    y0 = 520 + k * 340
    if k % 2 == 0: SEG.append((WL, y0, 850, y0 + 150))
    else: SEG.append((WRt, y0, 230, y0 + 150))
PEG_TOP, PEG_BOT = 2700, 3500
PEGS = np.array([(80 + (i + (0.5 if j % 2 else 0)) * 115, PEG_TOP + j * 100) for j in range(9) for i in range(9)
                 if 70 < 80 + (i + (0.5 if j % 2 else 0)) * 115 < 1010], np.float32); PR = 13.0
SPIN = [(320.0, 3800.0, 190.0, 2.3), (760.0, 4080.0, 190.0, -2.6)]   # spinner centre x, y, half length, rad/s
FUN_Y0, FUN_Y1 = 4320.0, 4620.0
SEG += [(WL, FUN_Y0, 440, FUN_Y1), (WRt, FUN_Y0, 640, FUN_Y1), (440, FUN_Y1, 440, 4900), (640, FUN_Y1, 640, 4900)]
FINISH = 4860.0; WORLD_H = 5000
SECTIONS = [(400, 'ZIG ZAG'), (2650, 'PEG FOREST'), (3650, 'SPINNERS'), (4250, 'FINAL FUNNEL')]


def seg_collide(P, V, x1, y1, x2, y2, rest, vs=None):
    """Push every ball out of segment (x1,y1)-(x2,y2) (thickness 6) and bounce it. vs: surface velocity per ball."""
    ax, ay = x2 - x1, y2 - y1; L2 = ax * ax + ay * ay
    t = np.clip(((P[:, 0] - x1) * ax + (P[:, 1] - y1) * ay) / L2, 0, 1)
    cx, cy = x1 + t * ax, y1 + t * ay; dx, dy = P[:, 0] - cx, P[:, 1] - cy; d = np.sqrt(dx * dx + dy * dy) + 1e-9
    hit = d < R + 5
    if not hit.any(): return []
    nx, ny = dx / d, dy / d
    P[hit, 0] = cx[hit] + nx[hit] * (R + 5); P[hit, 1] = cy[hit] + ny[hit] * (R + 5)
    sx = vs[0] if vs is not None else 0.0; sy = vs[1] if vs is not None else 0.0
    rx, ry = V[:, 0] - sx, V[:, 1] - sy; vn = rx * nx + ry * ny
    m = hit & (vn < 0); out = []
    if m.any():
        imp = vn[m]
        rx[m] -= (1 + rest) * imp * nx[m]; ry[m] -= (1 + rest) * imp * ny[m]
        tx, ty = -ny[m], nx[m]; vt = rx[m] * tx + ry[m] * ty     # rolling friction along the surface
        rx[m] -= 0.004 * vt * tx; ry[m] -= 0.004 * vt * ty
        V[m, 0] = rx[m] + (sx[m] if np.ndim(sx) else sx); V[m, 1] = ry[m] + (sy[m] if np.ndim(sy) else sy)
        out = list(np.where(m & (imp < -260))[0])                # hard hits make a sound
    return out


def simulate(seed):
    rng = np.random.default_rng(seed)
    P = np.array([[200 + i * (680 / max(1, NB - 1)) + rng.uniform(-12, 12), GATE_Y - 40] for i in range(NB)], np.float64)
    V = np.zeros((NB, 2)); done = np.zeros(NB, bool); order = []; frames, events = [], []
    t, still = 0.0, np.zeros(NB)
    while t < 90:
        for _ in range(SUB):
            t += DT; act = ~done
            V[act, 1] += G * DT; V[act] *= (1 - 0.25 * DT); P[act] += V[act] * DT
            if t < 1.6: seg_collide(P, V, WL, GATE_Y, WRt, GATE_Y, 0.2)                    # start gate
            for x1, y1, x2, y2 in SEG:
                for i in seg_collide(P, V, x1, y1, x2, y2, 0.35): events.append((t, 'hit', int(i)))
            # walls
            lo = P[:, 0] < WL + R; P[lo, 0] = WL + R; V[lo, 0] = np.abs(V[lo, 0]) * 0.5
            hi = P[:, 0] > WRt - R; P[hi, 0] = WRt - R; V[hi, 0] = -np.abs(V[hi, 0]) * 0.5
            # pegs (only near the peg forest)
            near = act & (P[:, 1] > PEG_TOP - 60) & (P[:, 1] < PEG_BOT + 60)
            for i in np.where(near)[0]:
                d = P[i] - PEGS; dist = np.sqrt((d ** 2).sum(1)); k = int(dist.argmin())
                if dist[k] < R + PR:
                    n = d[k] / dist[k]; P[i] = PEGS[k] + n * (R + PR); vn = V[i] @ n
                    if vn < 0:
                        V[i] -= 1.6 * vn * n; V[i, 0] += rng.uniform(-50, 50)
                        if vn < -200: events.append((t, 'peg', int(i)))
            # spinners (moving segments: bounce off the bar's surface velocity)
            for sx, sy, hl, w in SPIN:
                a = w * t; ca, sa = math.cos(a), math.sin(a)
                x1, y1, x2, y2 = sx - hl * ca, sy - hl * sa, sx + hl * ca, sy + hl * sa
                rx, ry = P[:, 0] - sx, P[:, 1] - sy
                vs = (-w * ry, w * rx)
                for i in seg_collide(P, V, x1, y1, x2, y2, 0.6, vs): events.append((t, 'spin', int(i)))
            # balls against each other
            for i in range(NB):
                for j in range(i + 1, NB):
                    if done[i] or done[j]: continue
                    d = P[j] - P[i]; dist = math.hypot(d[0], d[1])
                    if 0 < dist < 2 * R:
                        n = d / dist; rel = (V[i] - V[j]) @ n
                        if rel > 0: V[i] -= rel * n; V[j] += rel * n
                        ov = 2 * R - dist; P[i] -= n * ov / 2; P[j] += n * ov / 2
            for i in np.where(act & (P[:, 1] > FINISH))[0]:
                done[i] = True; order.append(int(i)); events.append((t, 'finish', int(i)))
            V[done] = 0
        sp = np.hypot(V[:, 0], V[:, 1]); still = np.where((sp < 15) & ~done & (t > 2), still + 1 / FPS, 0)
        for i in np.where(still > 1.5)[0]: V[i] += [rng.uniform(-200, 200), -250]; still[i] = 0      # never get stuck
        frames.append(dict(t=t, P=P.copy(), done=done.copy(), order=list(order)))
        if len(order) == NB and t > events[-1][0] + 2.5: break
    return frames, events, order


for seed in range(SEED, SEED + 40):
    frames, events, order = simulate(seed)
    t_first = next((e[0] for e in events if e[1] == 'finish'), None); t_last = frames[-1]['t']
    if os.environ.get('SIMDEBUG'): print('try', seed, round(t_first or -1, 1), round(t_last, 1), [NAMES[i] for i in order], flush=True)
    if len(order) == NB and t_first and 18 <= t_first <= 48 and t_last <= 62: break
else:
    sys.exit('no seed gives a race of the right length')
print('seed', seed, 'first %.1f s, all %.1f s' % (t_first, t_last), [NAMES[i] for i in order], flush=True)
winner = NAMES[order[0]]

# lead changes for commentary + live ranking: progress = y (finished balls rank by finishing order)
def ranking(fr):
    fin = fr['order']; rest = [i for i in np.argsort(-fr['P'][:, 1]) if i not in fin]
    return fin + rest
lead, last_call, calls = None, -10.0, []
for fr in frames:
    l = ranking(fr)[0]; t = fr['t']
    if l != lead and t > 2.5 and t - last_call > 3.2 and not fr['order']:
        calls.append((t, f'{NAMES[l].capitalize()} takes the lead!')); last_call = t
    lead = l
sec_calls = {}
for fr in frames:
    y = fr['P'][ranking(fr)[0], 1]
    for yy, nm in SECTIONS[1:]:
        if y > yy and nm not in sec_calls and not fr['order']: sec_calls[nm] = fr['t']
SAY = {'PEG FOREST': 'Into the peg forest!', 'SPINNERS': 'Watch out for the spinners!', 'FINAL FUNNEL': 'Final stretch!'}
for nm, t in sec_calls.items():
    if all(abs(t - c[0]) > 2.0 for c in calls): calls.append((t, SAY[nm]))
calls.append((t_first, f'{winner.capitalize()} wins the race!'))
calls.sort()

# ------------------------------------------------------------------ drawing
@functools.lru_cache(None)
def font(name, s):
    return ImageFont.truetype(subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout, s)


@functools.lru_cache(None)
def flag_ball(k, r):
    fi = Image.new('RGBA', (200, 200), (0, 0, 0, 0))
    ImageDraw.Draw(fi).text((100, 100), FLAGS[k], font=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109),
                            embedded_color=True, anchor='mm')
    fi = fi.crop(fi.getbbox()); d = 2 * r; sc = d / min(fi.width, fi.height)
    fi = fi.resize((max(d, int(fi.width * sc) + 1), max(d, int(fi.height * sc) + 1)), Image.LANCZOS)
    fi = fi.crop(((fi.width - d) // 2, (fi.height - d) // 2, (fi.width - d) // 2 + d, (fi.height - d) // 2 + d)).convert('RGB')
    mk = Image.new('L', (d * 4, d * 4), 0); ImageDraw.Draw(mk).ellipse([0, 0, d * 4 - 1, d * 4 - 1], fill=255); mk = mk.resize((d, d), Image.LANCZOS)
    inner = Image.new('L', (d * 4, d * 4), 0); ImageDraw.Draw(inner).ellipse([12, 12, d * 4 - 13, d * 4 - 13], fill=255)
    rgb = Image.composite(fi, Image.new('RGB', (d, d), (255, 255, 255)), inner.resize((d, d), Image.LANCZOS))
    shade = np.asarray(rgb, np.float32)
    yy, xx = np.mgrid[0:d, 0:d]; hl = np.exp(-(((xx - d * 0.35) ** 2 + (yy - d * 0.3) ** 2) / (2 * (d * 0.18) ** 2)))[..., None]
    shade = np.clip(shade * (0.82 + 0.18 * (1 - yy / d))[..., None] + 90 * hl, 0, 255)   # simple 3D look: shading + highlight
    return shade[..., ::-1].copy(), (np.asarray(mk, np.float32) / 255.0)[..., None]


def build_world():
    bg = np.zeros((WORLD_H, W, 3), np.float32) + np.array([18, 12, 12], np.float32)
    bg += (np.linspace(0, 1, WORLD_H)[:, None, None] * np.array([40, 10, 30], np.float32))
    lay = np.zeros((WORLD_H, W, 3), np.uint8)
    neon = [(255, 200, 60), (120, 255, 120), (60, 200, 255), (255, 120, 220)]
    for k, (x1, y1, x2, y2) in enumerate(SEG):
        cv2.line(lay, (int(x1), int(y1)), (int(x2), int(y2)), neon[k % 4], 10, cv2.LINE_AA)
    cv2.line(lay, (int(WL), 0), (int(WL), WORLD_H), (90, 80, 110), 6); cv2.line(lay, (int(WRt), 0), (int(WRt), WORLD_H), (90, 80, 110), 6)
    for x, y in PEGS: cv2.circle(lay, (int(x), int(y)), int(PR), (230, 230, 240), -1, cv2.LINE_AA)
    for k in range(0, 200, 25):                                                            # chequered finish
        c = (255, 255, 255) if (k // 25) % 2 == 0 else (30, 30, 30)
        cv2.rectangle(lay, (440 + k, int(FINISH)), (min(640, 465 + k), int(FINISH) + 22), c, -1)
    glow = cv2.GaussianBlur(lay.astype(np.float32), (0, 0), 14)
    w = bg + glow * 0.9; m = (lay.max(2, keepdims=True) > 0).astype(np.float32); w = w * (1 - m) + lay * m
    im = Image.fromarray(np.clip(w[..., ::-1], 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for y, nm in SECTIONS:
        d.text((W // 2, y), nm, font=font('Inter Black', 44), fill=(255, 255, 255), anchor='mm')
    d.text((W // 2, FINISH + 70), 'FINISH', font=font('Inter Black', 60), fill=YEL, anchor='mm')
    return np.asarray(im, np.float32)[..., ::-1].copy()


WORLD = build_world()
OW, OH = (1920, 1080) if WIDE else (1080, 1920)
VIEW_H = 1080 if WIDE else VH                     # world pixels visible vertically
TOPBAND = 0 if WIDE else 330
cam = 0.0; trails = [[] for _ in range(NB)]


@functools.lru_cache(None)
def text_rgba(lines, w, h):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for x, y, txt, s, col, anchor in lines:
        d.text((x, y), txt, font=font('Inter Black', s), fill=col + (255,), anchor=anchor, stroke_width=6, stroke_fill=(0, 0, 0, 255))
    return np.asarray(im, np.float32)


def over(f, L, x0=0, y0=0):
    h, w = L.shape[:2]; a = L[..., 3:4] / 255.0
    f[y0:y0 + h, x0:x0 + w] = f[y0:y0 + h, x0:x0 + w] * (1 - a) + L[..., [2, 1, 0]] * a


def paste_ball(f, k, x, y, r):
    spr, a = flag_ball(k, r); h = spr.shape[0]; x0, y0 = int(round(x)) - h // 2, int(round(y)) - h // 2
    if x0 < 0 or y0 < 0 or x0 + h > f.shape[1] or y0 + h > f.shape[0]: return
    f[y0:y0 + h, x0:x0 + h] = f[y0:y0 + h, x0:x0 + h] * (1 - a) + spr * a


def standings_panel(rank, done_order):
    lines = []; x0 = 1655 if WIDE else 760; y0 = 120 if WIDE else 440
    rows = []
    for p, i in enumerate(rank[:6 if WIDE else 3]):
        rows.append((p, i))
    im = Image.new('RGBA', (300, 90 * len(rows) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for p, i in rows:
        y = 10 + p * 90
        d.rounded_rectangle([0, y, 299, y + 78], 22, fill=(20, 16, 34, 215) if p else (70, 58, 10, 230))
        d.text((32, y + 39), str(p + 1), font=font('Inter Black', 40), fill=YEL + (255,), anchor='mm')
        spr, a = flag_ball(i, 24); fl = Image.fromarray(np.concatenate([spr[..., ::-1], a * 255], 2).astype(np.uint8), 'RGBA')
        im.alpha_composite(fl, (62, y + 15))
        d.text((120, y + 39), NAMES[i], font=font('Inter Black', 30 if len(NAMES[i]) < 9 else 22), fill=(255, 255, 255, 255), anchor='lm')
    return np.asarray(im, np.float32), x0 - 150 if WIDE else x0, y0


def render(i):
    global cam
    t = i / FPS; fr = frames[min(len(frames) - 1, i)]; rank = ranking(fr)
    alive = [k for k in rank if not fr['done'][k]]
    focus = fr['P'][alive[0], 1] if alive else FINISH
    target = min(max(focus - VIEW_H * (0.42 if not WIDE else 0.45), 0), WORLD_H - VIEW_H)
    cam = target if i == 0 else cam + (target - cam) * 0.09
    y0 = int(cam); view = WORLD[y0:y0 + VIEW_H].copy()
    for sx, sy, hl, w in SPIN:                                        # spinners
        a = w * t; ca, sa = math.cos(a), math.sin(a)
        p1 = (int(sx - hl * ca), int(sy - hl * sa - y0)); p2 = (int(sx + hl * ca), int(sy + hl * sa - y0))
        cv2.line(view, p1, p2, (80, 220, 255), 14, cv2.LINE_AA); cv2.circle(view, (int(sx), int(sy - y0)), 14, (255, 255, 255), -1, cv2.LINE_AA)
    if t < 1.6: cv2.line(view, (int(WL), int(GATE_Y - y0)), (int(WRt), int(GATE_Y - y0)), (60, 60, 255), 10, cv2.LINE_AA)
    for k in range(NB):                                                # soft motion trails
        trails[k] = (trails[k] + [tuple(fr['P'][k])])[-7:]
        for j, (x, y) in enumerate(trails[k][:-1]):
            if 0 < y - y0 < VIEW_H:
                c = view[int(y - y0), int(min(max(x, 0), W - 1))]
                cv2.circle(view, (int(x), int(y - y0)), int(R * (0.35 + 0.08 * j)), (200, 190, 230), -1, cv2.LINE_AA)
    for k in reversed(rank):
        x, y = fr['P'][k]; paste_ball(view, k, x, y - y0, int(R))
    if alive:                                                          # crown over the leader
        x, y = fr['P'][rank[0]]
        tri = np.array([[x - 22, y - y0 - 40], [x - 10, y - y0 - 58], [x, y - y0 - 44], [x + 10, y - y0 - 58], [x + 22, y - y0 - 40]], np.int32)
        cv2.fillPoly(view, [tri], (0, 215, 255), cv2.LINE_AA)
    if WIDE:
        f = np.zeros((OH, OW, 3), np.float32) + np.array([18, 12, 12], np.float32)
        vs = cv2.resize(view, (int(W * OH / VIEW_H), OH)); x0 = (OW - vs.shape[1]) // 2; f[:, x0:x0 + vs.shape[1]] = vs
    else:
        f = view
        band = np.zeros((TOPBAND, OW, 3), np.float32) + np.array([30, 14, 20], np.float32)
        f[:TOPBAND] = f[:TOPBAND] * 0.25 + band * 0.75
    L, px, py = standings_panel(tuple(rank), tuple(fr['order'])); over(f, L, px, py)
    if not WIDE:
        msg = 'PICK YOUR COUNTRY!' if t < 3.0 else ('3' if t < 0 else '')
        over(f, text_rgba(((OW // 2, 120, 'WHICH COUNTRY', 80, (255, 255, 255), 'mm'), (OW // 2, 220, 'WINS THE RACE?', 80, YEL, 'mm')), OW, 300))
        if fr['order']:
            over(f, text_rgba(((OW // 2, 60, f'{NAMES[fr["order"][0]]} WINS!', 92, YEL, 'mm'),), OW, 140), 0, 1500)
        elif t < 3.0:
            over(f, text_rgba(((OW // 2, 60, msg, 64, (255, 255, 255), 'mm'),), OW, 140), 0, 1500)
        tag = text_rgba(((OW // 2, 30, 'ZEIPAN', 30, YEL, 'mm'),), OW, 60); tag[..., 3] *= 0.55; over(f, tag, 0, 1750)
    return f


END = 2.6 if not WIDE else 0.0
T = frames[-1]['t'] + END; N = int(T * FPS)


def end_card(u):
    f = np.zeros((OH, OW, 3), np.float32) + np.array([18, 12, 12], np.float32)
    spr, a = flag_ball(order[0], 140); h = spr.shape[0]; x0 = OW // 2 - h // 2; y0 = 420
    f[y0:y0 + h, x0:x0 + h] = f[y0:y0 + h, x0:x0 + h] * (1 - a) + spr * a
    over(f, text_rgba(((OW // 2, 840, f'{winner} WON!', 104 if len(winner) < 9 else 80, YEL, 'mm'),
                       (OW // 2, 970, 'WHERE ARE YOU FROM?', 70, (255, 255, 255), 'mm'),
                       (OW // 2, 1080, 'comment your country', 46, (210, 210, 220), 'mm')), OW, OH))
    return f


# ------------------------------------------------------------------ audio: music bed + hits + commentary
mix = np.zeros(int((T + 2) * SR), np.float32); mus = np.zeros_like(mix)
def put(at, s, g=1.0, buf=None):
    buf = mix if buf is None else buf
    i = int(at * SR); j = min(len(buf), i + len(s)); buf[i:j] += g * s[:j - i]
def tone(f, d, g, decay=7):
    x = np.arange(int(d * SR)) / SR
    return (np.sin(2 * np.pi * f * x) + 0.35 * np.sin(4 * np.pi * f * x)) * np.exp(-x * decay) * g
BPM = 126; beat = 60 / BPM; music_end = frames[-1]['t'] + 0.3
kick = lambda: np.sin(2 * np.pi * (55 + 90 * np.exp(-np.arange(int(0.25 * SR)) / SR * 30)) * np.arange(int(0.25 * SR)) / SR) * np.exp(-np.arange(int(0.25 * SR)) / SR * 14)
rng = np.random.default_rng(3)
hat = lambda: rng.standard_normal(int(0.05 * SR)).astype(np.float32) * np.exp(-np.arange(int(0.05 * SR)) / SR * 90)
bassline = [55.0, 55.0, 65.4, 49.0]; arp = [220.0, 261.6, 329.6, 392.0, 329.6, 261.6, 220.0, 196.0]
b, k = 1.5, 0                                            # music starts with GO
while b < music_end:
    put(b, kick(), 0.34, mus)
    put(b + beat / 2, hat(), 0.05, mus)
    put(b, tone(bassline[(k // 4) % 4], beat * 0.9, 0.12, 3), 1.0, mus)
    put(b, tone(arp[k % 8] * 2, beat * 0.45, 0.045, 9), 1.0, mus); put(b + beat / 2, tone(arp[(k + 3) % 8] * 2, beat * 0.45, 0.035, 9), 1.0, mus)
    b += beat; k += 1
last = {}
PENTA = [523.3, 587.3, 659.3, 784.0, 880.0]
for t, kind, i in events:
    if t > music_end or t - last.get(i, -1) < 0.08: continue
    last[i] = t
    if kind == 'finish':
        if i == order[0]:
            for j, fq in enumerate((523.3, 659.3, 784.0, 1046.5)): put(t + j * 0.09, tone(fq, 1.4, 0.2, 3))
        else: put(t, tone(880, 0.4, 0.12))
    else: put(t, tone(PENTA[i % 5] * (1.5 if kind == 'spin' else 1), 0.25, 0.05 if kind == 'peg' else 0.07, 14))
put(0.0, tone(440, 0.25, 0.15)); put(0.55, tone(440, 0.25, 0.15)); put(1.1, tone(880, 0.5, 0.2))      # 3-2-1 beeps
sys.path.insert(0, os.path.join(REPO, 'channel2')); import bwlkit
KK = bwlkit.kokoro()
def voice(txt):
    s, sr = KK.create(txt, voice='am_michael', speed=1.12, lang='en-us')
    return cv2.resize(s.astype(np.float32)[None, :], (int(len(s) * SR / sr), 1), interpolation=cv2.INTER_LINEAR)[0]
duck = np.ones(len(mix), np.float32)
for t, txt in [(0.0, 'Pick your country! Three, two, one, go!')] + calls:
    v = voice(txt); put(t, v, 1.0)
    i0, i1 = int(t * SR), min(len(mix), int(t * SR) + len(v)); duck[i0:i1] = 0.45
duck = np.convolve(duck, np.ones(2205) / 2205, 'same')                   # smooth ducking (50 ms ramps)
mix = mix + mus * duck
mix = mix / max(1.0, np.abs(mix).max() / 0.6)
wav = OUT + '.wav'; sf.write(wav, np.stack([mix, mix], 1)[:int(T * SR)], SR, subtype='FLOAT')

enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
                        '-i', wav, '-af', 'loudnorm=I=-15:TP=-2:LRA=9,aresample=48000,lowpass=f=15500,alimiter=limit=0.6:level=false',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                        '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for i in range(N):
    t = i / FPS
    f = render(i) if t < frames[-1]['t'] else end_card(t - frames[-1]['t'])
    enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); os.remove(wav)
json.dump(dict(seed=seed, order=[NAMES[i] for i in order], winner=winner, t_first=t_first, t_all=frames[-1]['t'], calls=calls),
          open(OUT + '.json', 'w'))
print('race2', OUT, round(T, 1), 's, winner', winner, flush=True)
