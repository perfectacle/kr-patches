"""Screenshots of any dialogue, before (V1.0) and after (this patch).

usage: dlg_shots.py SPEC [SPEC ...]     SPEC = ID[:ITEM]   (hex)
  ID     dialogue id; the harness ROMs (tools/make_harness.sh) show it in place
         of the shopkeeper's first line in test/states/shop.mss
  ITEM   item id for the dialogue's item-name codes ($0234)

Writes test/out/verify_shots/dlg_<ID>[_item<ITEM>]_<n>_v1.png / _new.png, one file per box;
the box count comes from each ROM's own text (box breaks $02-$04).
"""
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
# Verification only: the shopkeeper speaking any line is not real play.
OUT = ROOT / 'test/out/verify_shots'
WORK = ROOT / 'test/out/dlg'
STATE = ROOT / 'test/states/shop.mss'
ROMS = {'v1': ROOT / 'build/harness_v1.sfc', 'new': ROOT / 'build/harness.sfc'}
sys.path.insert(0, str(ROOT / 'tools/py'))
import dialogue  # noqa: E402
import dlg_rewrite  # noqa: E402


def box_count(rom, i):
    toks = dlg_rewrite.tokens(rom[dialogue.address(rom, i):][:600])
    toks = toks[:toks.index(b'\0')] if b'\0' in toks else toks
    return 1 + sum(1 for t in toks if len(t) == 1 and t[0] in (2, 3, 4))


STEP = 90      # frames per box: text finishes printing well within this
EVERY = 15     # capture interval; the best frame of each box is kept


def run(rom, out, pokes, boxes):
    seq = ','.join(['wait:5,a:3'] + [f'wait:{STEP - 3},a:3'] * boxes + [f'wait:{STEP - 3}'])
    subprocess.run(['tools/run_seq.sh', str(rom), str(STATE), str(out), seq, str(EVERY), '1'], cwd=ROOT,
                   env={**os.environ, 'POKE': pokes, 'SHOTS': '1'},
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    # box k is on screen between presses k and k+1; item banners close by
    # themselves, so keep the frame with the most text in that span
    best = []
    for k in range(boxes):
        frames = [out / f'q{f:05d}.png' for f in range(STEP * k + EVERY, STEP * (k + 1) + 1, EVERY)]
        frames = [f for f in frames if f.exists()]
        if frames:
            best.append(max(frames, key=lambda f: text_pixels(Image.open(f).convert('RGB'))))
    return best


def text_pixels(img):
    """Dark glyph pixels on the dialogue parchment plus white banner text."""
    dark = sum(1 for y in range(8, 72, 2) for x in range(8, 248, 2) if sum(img.getpixel((x, y))) < 180)
    white = sum(1 for y in range(0, 224, 2) for x in range(0, 256, 2) if min(img.getpixel((x, y))) > 200)
    return dark + white


def same(a, b):
    return ImageChops.difference(a, b).getbbox() is None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for spec in sys.argv[1:]:
        did, _, item = spec.partition(':')
        i = int(did, 16)
        pokes = f'7E17F0=5A;7E17F1=A5;7E17F2={i & 0xFF:02X};7E17F3={i >> 8:02X}'
        if item:
            pokes += f';7E0234={int(item, 16):02X}'
        name = did + (f'_item{item}' if item else '')
        for tag, rom in ROMS.items():
            boxes = box_count(rom.read_bytes(), i)
            files = run(rom, WORK / f'{name}_{tag}', pokes, boxes)
            prev, n = None, 0
            for f in files:
                if not f.exists():
                    break
                img = Image.open(f).convert('RGB')
                if prev is not None and same(img, prev):
                    continue
                n += 1
                img.save(OUT / f'dlg_{name}_{n}_{tag}.png')
                prev = img
            print(f'{name} {tag}: {n} box(es)')


if __name__ == '__main__':
    main()
