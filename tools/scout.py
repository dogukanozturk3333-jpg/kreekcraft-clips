#!/usr/bin/env python3
"""ZEIPAN studio – stage 1 (scouting). Lists recent Twitch clips of streamers whose clipping is
allowed, keeps GTA 6 ones, drops already-processed/blocked ones and ranks them.

  python3 -I tools/scout.py [--range 24hr|7d] [--top 25] > studio/candidates.md
Score = views weighted by recency and by how much the title hints at a story moment."""
import json, re, subprocess, sys, os, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STREAMERS = ['kreekcraft', 'kaicenat', 'clix', 'lacy']          # clipping allowed / paid campaigns
BLOCK = re.compile(r'gya+t|steamy|sneaky pic|thirst|girlfriend|kiss|sexy|ass\b|booty|strip|club|stripper|twerk|nude|naked|boob|onlyfans|drug|crack|weed|coke|casino|gambl|bet\b|stake|beat a girl|girl down|kill(ed)? (a )?dog|dog|cat\b', re.I)
STORY = re.compile(r'first|found|finds|secret|easter|bigfoot|skunk|ufo|crash|chase|police|cops|stars|heist|rob|fraud|plane|heli|shark|gator|croc|wasted|fail|insane|best|funniest|reaction|why|how', re.I)
rng = sys.argv[sys.argv.index('--range') + 1] if '--range' in sys.argv else '24hr'
top = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 25
done = set()
p = os.path.join(ROOT, 'tools', 'processed.txt')
if os.path.exists(p):
    for ln in open(p):
        done.add(ln.strip().split('-')[1] if '-' in ln.strip()[:4] else ln.strip())
def run(args):
    r = subprocess.run(['yt-dlp'] + args, capture_output=True, text=True, timeout=300)
    return r.stdout
rows = []
for ch in STREAMERS:
    out = run(['--flat-playlist', '-J', f'https://www.twitch.tv/{ch}/clips?filter=clips&range={rng}'])
    try: es = json.loads(out).get('entries', [])
    except Exception: es = []
    for e in es[:40]:
        url = e.get('url') or ''; slug = url.rstrip('/').split('/')[-1]
        t = e.get('title') or ''
        if any(slug.startswith(d) or d.startswith(slug.split('-')[0]) for d in done if d): continue
        if BLOCK.search(t): continue
        rows.append(dict(ch=ch, slug=slug, url=url, title=t, views=e.get('view_count') or 0, dur=e.get('duration') or 0))
# category check only for the top slice (one request per clip)
rows.sort(key=lambda r: -r['views'])
keep = []
for r in rows[:top * 2]:
    meta = run(['-O', '%(categories.0)s\t%(upload_date)s', r['url']]).strip().split('\t')
    if not meta or 'Grand Theft Auto VI' not in meta[0]: continue
    r['date'] = meta[1] if len(meta) > 1 else ''
    bonus = 1.6 if STORY.search(r['title']) else 1.0
    short = 1.2 if 15 <= r['dur'] <= 45 else 1.0
    r['score'] = round(r['views'] * bonus * short)
    keep.append(r)
keep.sort(key=lambda r: -r['score'])
print(f"# Scout report – {dt.datetime.utcnow():%Y-%m-%d %H:%M} UTC – range {rng}\n")
for i, r in enumerate(keep[:top], 1):
    print(f"{i}. **{r['ch']}** – {r['title'][:70]} – {r['views']} views, {r['dur']:.0f}s, score {r['score']}  \n   {r['url']}")
