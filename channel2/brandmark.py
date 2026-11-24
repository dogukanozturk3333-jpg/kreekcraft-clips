"""Brain Warp Lab watermark: a faint diagonal @brainwarplab across the middle of the picture (hard to crop
out without losing the puzzle) plus a small logo + handle tag near the bottom. Shared by every BWL renderer."""
import os, functools, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
HANDLE = '@brainwarplab'
HERE = os.path.dirname(os.path.abspath(__file__))


@functools.lru_cache(None)
def _font(name, s):
    return ImageFont.truetype(subprocess.run(['fc-match', '-f', '%{file}', name], capture_output=True, text=True).stdout, s)


@functools.lru_cache(None)
def layer(diag_alpha=0, diag_col=(90, 60, 150), tag_alpha=110, tag_col=(255, 255, 255)):   # no big diagonal (user: too distracting)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    # diagonal handle through the centre
    t = Image.new('RGBA', (1400, 160), (0, 0, 0, 0))
    ImageDraw.Draw(t).text((700, 80), HANDLE, font=_font('Inter Black', 118), fill=diag_col + (diag_alpha,), anchor='mm')
    t = t.rotate(28, expand=True, resample=Image.BICUBIC)
    if diag_alpha: im.alpha_composite(t, (W // 2 - t.width // 2, 930 - t.height // 2))
    # bottom tag: round logo + handle
    lg = Image.open(os.path.join(HERE, '..', 'studio', 'art', 'brainwarplab-logo.png')).convert('RGBA').resize((40, 40), Image.LANCZOS)
    m = Image.new('L', (40, 40), 0); ImageDraw.Draw(m).ellipse([0, 0, 39, 39], fill=tag_alpha); lg.putalpha(m)
    f = _font('Inter Display SemiBold', 26); d = ImageDraw.Draw(im); tw = d.textlength(HANDLE, font=f)
    x0 = int(W / 2 - (40 + 10 + tw) / 2); y = 1780   # below every caption, hint and timer
    im.alpha_composite(lg, (x0, y - 20))
    d.text((x0 + 50, y), HANDLE, font=f, fill=tuple(tag_col) + (tag_alpha,), anchor='lm')
    return im


def apply_pil(img_rgba, **kw):
    img_rgba.alpha_composite(layer(**kw)); return img_rgba


def apply_np(frame_rgb_float, **kw):
    L = np.asarray(layer(**kw), np.float32); a = L[..., 3:4] / 255.0
    return frame_rgb_float * (1 - a) + L[..., :3] * a
