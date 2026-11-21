#!/usr/bin/env python3
"""Themed compilation Shorts: several streamers' moments on one theme, cut together with the Zeipan package.

usage: compile.py <workdir> <compilation.json>
compilation.json: {"name": "...", "hook": "LINE 1|LINE 2", "segments": [<render.py clip>, ...]}
Each segment is rendered by render.py without an ending, intro sting or progress bar and with a
"#N STREAMER" label; the first one carries the compilation hook. The segments are joined and a 2 s
outro is added: blurred last frame, big Zeipan logo, "FOLLOW FOR MORE" and every streamer's twitch.tv link.
Output: <workdir>/out/<name>.mp4
"""
import json, os, subprocess, sys

import yaml

S, CFG = sys.argv[1], json.load(open(sys.argv[2]))
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND = yaml.safe_load(open(os.environ.get('BRAND', REPO + '/brand.yaml')))
OUT = os.path.join(S, 'out'); os.makedirs(OUT, exist_ok=True)
W, H, OUTRO = 1080, 1920, 2.0
name = CFG['name']

segs, links = [], []
for i, seg in enumerate(CFG['segments'], 1):
    seg = dict(seg)
    st = BRAND['streamers'][seg['streamer']]
    seg.update(name=f"{name}__seg{i}", ending='none', intro=False, bar=False,
               label=seg.get('label', f"#{i} {st['name'].upper()}"))
    if i == 1:
        seg['hook'] = CFG['hook']
    else:
        seg.pop('hook', None)
    segs.append(seg)
    if st['twitch'] not in links:
        links.append(st['twitch'])
cfg_path = os.path.join(S, f'{name}__segments.json')
json.dump(segs, open(cfg_path, 'w'))
subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'render.py'), S, cfg_path], check=True)

# outro: blurred last frame + logo + follow line + streamer links
last = os.path.join(S, f'{name}__last.png')
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-sseof', '-0.1', '-i', f"{OUT}/{segs[-1]['name']}.mp4",
                '-frames:v', '1', '-update', '1', last], check=True)
col = BRAND['frame']['color'].lstrip('#')
ass = os.path.join(S, 'ass', f'{name}__outro.ass')
lines = '\\N'.join(l for l in links)
open(ass, 'w').write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: F,Inter Black,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,6,3,5,40,40,0,1
Style: L,Inter Black,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,5,2,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 1,0:00:00.00,0:00:{OUTRO:05.2f},F,,0,0,0,,{{\\pos(540,1130)\\fad(120,0)}}FOLLOW FOR MORE
Dialogue: 1,0:00:00.05,0:00:{OUTRO:05.2f},L,,0,0,0,,{{\\an8\\pos(540,1250)\\fad(150,0)}}{lines}
""")
logo = os.path.join(REPO, BRAND['channel']['logo'])
pop = os.path.join(REPO, BRAND['sfx']['dir'], (BRAND.get('intro', {}).get('sfx') or 'pop') + '.wav')
outro = os.path.join(S, f'{name}__outro.mp4')
fw = BRAND['frame']['width']
subprocess.run([
    'ffmpeg', '-v', 'error', '-y', '-loop', '1', '-t', f'{OUTRO}', '-framerate', '30', '-i', last,
    '-loop', '1', '-t', f'{OUTRO}', '-framerate', '30', '-i', logo, '-i', pop,
    '-filter_complex',
    f"[0:v]scale={W}:{H},gblur=sigma=30,eq=brightness=-0.3,drawbox=x=0:y=0:w=iw:h=ih:color=0x{col}:t={fw}[bg];"
    f"[1:v]format=rgba,scale=w='820*(0.7+0.3*min(1,t/0.15))':h=-2:eval=frame[lg];"
    f"[bg][lg]overlay=x=(W-w)/2:y=900-h/2,ass={ass},format=yuv420p[v];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.8,apad=whole_dur={OUTRO}[a]",
    '-map', '[v]', '-map', '[a]', '-t', f'{OUTRO}', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
    '-r', '30', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', outro], check=True)

# join segments + outro (re-encode so every boundary is clean)
parts = [f"{OUT}/{s['name']}.mp4" for s in segs] + [outro]
inp = sum((['-i', p] for p in parts), [])
n = len(parts)
cat = (''.join(f'[{i}:v]setsar=1[v{i}];' for i in range(n)) +
       ''.join(f'[v{i}][{i}:a]' for i in range(n)) + f'concat=n={n}:v=1:a=1[v][a]')
out = f'{OUT}/{name}.mp4'
subprocess.run(['ffmpeg', '-v', 'error', '-y'] + inp + [
    '-filter_complex', cat, '-map', '[v]', '-map', '[a]',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-maxrate', '11M', '-bufsize', '22M',
    '-profile:v', 'high', '-level', '4.1', '-r', '30', '-g', '60', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', out], check=True)
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out],
                           capture_output=True, text=True).stdout)
print('compiled', out, f'{dur:.1f}s', os.path.getsize(out) // 1024 // 1024, 'MB')
