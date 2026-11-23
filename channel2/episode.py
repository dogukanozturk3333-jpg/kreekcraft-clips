#!/usr/bin/env python3
"""Brain Warp Lab long-form episode N: renders FRESH puzzles (seeds 100*N+k, never used for Shorts), then
builds the 16:9 episode with compile_long.py. Only the finished episode, its chapters and its thumbnail
land in the repo (channel2/episodes/); the puzzle renders stay in a scratch folder.
  python3 -I channel2/episode.py N [--workers 2]"""
import sys, os, json, subprocess, concurrent.futures as cf
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
N = int(sys.argv[1]); WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 2
SCR = os.environ.get('BWL_SCRATCH', '/tmp/claude-0/-home-user/d825807f-e0e5-55ce-ac85-8ebee4d46dbb/scratchpad/episodes')
work = os.path.join(SCR, f'ep{N:02d}'); os.makedirs(work, exist_ok=True)
base = 100 * N

ROUNDS = [  # (round name, generator, mode/arg, count) — easy formats first, the brain-burners last
    ('SHARP EYES', 'oddone2.py', 'emoji', 6),
    ('COLOR VISION', 'oddone2.py', 'color', 6),
    ('LETTERS & NUMBERS', 'oddone2.py', 'text', 6),
    ('SPOT THE DIFFERENCE', 'spotdiff.py', None, 5),
    ('BRAIN MATH', 'emojimath.py', None, 5),
]
BONUS = [('illusion.py', 'lilac'), ('illusion.py', 'spiral')]
PREFIX = {'emoji': 'odd', 'color': 'col', 'text': 'txt', 'spotdiff.py': 'diff', 'emojimath.py': 'math'}

jobs, spec = [], {'title': [f'{sum(r[3] for r in ROUNDS) + len(BONUS)} BRAIN PUZZLES', 'HOW MANY CAN YOU SOLVE?'],
                  'episode': N, 'rounds': []}
for name, gen, mode, count in ROUNDS:
    items = []
    for k in range(count):
        seed = base + k + 1; pre = PREFIX[mode] if mode else PREFIX[gen]
        out = os.path.join(work, f'{pre}-{seed}.mp4'); items.append(out)
        cmd = ['python3', '-I', os.path.join(HERE, gen), str(seed), out] + ([mode] if mode else [])
        jobs.append((cmd, out))
    spec['rounds'].append({'name': name, 'items': items})
bonus = []
for gen, kind in BONUS:
    out = os.path.join(work, f'{kind}-ep{N}.mp4'); bonus.append(out)
    photo = os.path.join(REPO, 'ambient', 'img', ['short-fireplace.jpg', 'short-snow.jpg'][N % 2])
    jobs.append((['python3', '-I', os.path.join(HERE, gen), kind, out] + (['--photo', photo] if kind == 'spiral' else []), out))
spec['rounds'].append({'name': 'BONUS: ILLUSIONS', 'items': bonus})


def run(job):
    cmd, out = job
    if os.path.exists(out): return out, 'cached'
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    return out, ('ok' if r.returncode == 0 and os.path.exists(out) else 'FAIL ' + r.stderr[-300:])

with cf.ThreadPoolExecutor(WORKERS) as ex:
    for out, st in ex.map(run, jobs): print(os.path.basename(out), st, flush=True)

os.makedirs(os.path.join(HERE, 'episodes'), exist_ok=True)
json.dump(spec, open(os.path.join(work, 'spec.json'), 'w'), indent=1)
final = os.path.join(HERE, 'episodes', f'brainwarplab-ep{N:02d}.mp4'); tmp = os.path.join(work, os.path.basename(final))
subprocess.run(['python3', '-I', os.path.join(HERE, 'compile_long.py'), os.path.join(work, 'spec.json'), tmp], cwd=REPO, check=True)
for ext in ('', '.chapters.txt', '.thumb.jpg'): os.replace(tmp + ext, final + ext)   # only finished files enter the repo
print('episode', N, final)
