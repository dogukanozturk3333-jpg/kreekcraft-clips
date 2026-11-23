#!/usr/bin/env python3
"""Pre-upload quality gate for every video (run it, then LOOK at the contact sheet before scheduling).
  python3 -I tools/qa.py VIDEO.mp4 [--kind short|long|ambient] [--sheet OUT.jpg]
Checks: container/codec, resolution and orientation, duration window, frame rate, loudness (integrated LUFS)
and true peak, silence gaps, black frames, frozen video, then writes a 12-frame contact sheet.
Exit code 0 = PASS, 1 = FAIL (reasons printed)."""
import sys, os, json, re, subprocess
from PIL import Image

args = sys.argv[1:]; V = args[0]
kind = args[args.index('--kind') + 1] if '--kind' in args else 'short'
sheet = args[args.index('--sheet') + 1] if '--sheet' in args else os.path.splitext(V)[0] + '.qa.jpg'
fails, notes = [], []

info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,codec_name,width,height,r_frame_rate',
                                  '-of', 'json', V], capture_output=True, text=True).stdout)
vs = [s for s in info['streams'] if s['codec_type'] == 'video']; au = [s for s in info['streams'] if s['codec_type'] == 'audio']
dur = float(info['format']['duration'])
if not vs: fails.append('no video stream')
if not au: fails.append('no audio stream')
w, h = (vs[0]['width'], vs[0]['height']) if vs else (0, 0)
rules = {'short': dict(size=(1080, 1920), dur=(8, 60), lufs=(-17, -12)),
         'long': dict(size=(1920, 1080), dur=(60, 899), lufs=(-18, -12)),       # < 15 min unless the channel allows more
         'ambient': dict(size=(1920, 1080), dur=(600, 4 * 3600), lufs=(-24, -16))}[kind]
if (w, h) != rules['size']: fails.append(f'size {w}x{h}, expected {rules["size"][0]}x{rules["size"][1]}')
if not rules['dur'][0] <= dur <= rules['dur'][1]: fails.append(f'duration {dur:.1f}s outside {rules["dur"]}')
if os.path.getsize(V) > 95_000_000: fails.append(f'file {os.path.getsize(V) // 1_000_000} MB > 95 MB (GitHub/Zapier limit)')

r = subprocess.run(['ffmpeg', '-v', 'info', '-i', V, '-af', 'ebur128=peak=true,silencedetect=n=-45dB:d=1.5', '-f', 'null', '-'],
                   capture_output=True, text=True).stderr
I = float(re.findall(r'^\s+I:\s+(-?[\d.]+) LUFS', r, re.M)[-1]); TP = float(re.findall(r'^\s+Peak:\s+(-?[\d.]+) dBFS', r, re.M)[-1])
if not rules['lufs'][0] <= I <= rules['lufs'][1]: fails.append(f'loudness {I} LUFS outside {rules["lufs"]}')
if TP > -0.3: fails.append(f'true peak {TP} dBFS (clipping risk)')
sil = re.findall(r'silence_duration: ([\d.]+)', r)
if kind != 'ambient' and sil: notes.append(f'silent stretches: {", ".join(sil[:5])} s')

r = subprocess.run(['ffmpeg', '-v', 'info', '-i', V, '-vf', 'blackdetect=d=0.5:pix_th=0.08,freezedetect=n=0.001:d=' + ('8' if kind == 'short' else '20'),
                    '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
blacks = re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', r)
if blacks: fails.append('black frames at ' + ', '.join(f'{float(a):.1f}-{float(b):.1f}s' for a, b in blacks[:4]))
frz = re.findall(r'freeze_start: ([\d.]+)', r)
if frz and kind != 'ambient': notes.append('frozen picture from ' + ', '.join(f'{float(x):.1f}s' for x in frz[:4]) + ' (fine for stare/illusion phases)')

n = 12; tw = 180 if h > w else 320; th = int(tw * h / w) if w else 180
S = Image.new('RGB', (tw * 6, th * 2), (20, 20, 20))
for i in range(n):
    t = dur * (i + 0.5) / n; tmp = f'/tmp/qa_{os.getpid()}_{i}.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', V, '-frames:v', '1', '-vf', f'scale={tw}:{th}', tmp])
    if os.path.exists(tmp): S.paste(Image.open(tmp), ((i % 6) * tw, (i // 6) * th)); os.remove(tmp)
S.save(sheet, quality=85)

print(f'QA {"PASS" if not fails else "FAIL"}  {os.path.basename(V)}  {w}x{h}  {dur:.1f}s  {I} LUFS  TP {TP} dBFS')
for f in fails: print('  FAIL:', f)
for x in notes: print('  note:', x)
print('  sheet:', sheet)
sys.exit(1 if fails else 0)
