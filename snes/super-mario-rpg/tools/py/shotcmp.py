"""Compare screenshots as text, so an image only needs to be looked at when it differs.

usage: shotcmp.py ACTUAL REF [--crop OUT.png] [--box X,Y,W,H] [--tol N]
       shotcmp.py ACTUAL --box X,Y,W,H --crop OUT.png      (crop only)
ACTUAL/REF may be PNG files or directories (files matched by name).
--box   limit the comparison (and crop) to a region.
--tol   per-channel difference ignored as noise (default 0).
--crop  write the differing region of ACTUAL (or --box when there is no REF).
Exit status 1 if any pair differs.
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops


def region(im, box):
    return im.crop((box[0], box[1], box[0] + box[2], box[1] + box[3])) if box else im


def compare(a_path, b_path, box, tol):
    a = region(Image.open(a_path).convert('RGB'), box)
    b = region(Image.open(b_path).convert('RGB'), box)
    if a.size != b.size:
        return None, f'size {a.size} != {b.size}'
    diff = ImageChops.difference(a, b).convert('L').point(lambda v: 255 if v > tol else 0)
    bbox = diff.getbbox()
    if not bbox:
        return None, 'same'
    n = sum(1 for v in diff.getdata() if v)
    if box:
        bbox = (bbox[0] + box[0], bbox[1] + box[1], bbox[2] + box[0], bbox[3] + box[1])
    return bbox, f'diff px={n} bbox={bbox[0]},{bbox[1]},{bbox[2] - bbox[0]},{bbox[3] - bbox[1]}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('actual')
    ap.add_argument('ref', nargs='?')
    ap.add_argument('--box', type=lambda s: tuple(int(x) for x in s.split(',')))
    ap.add_argument('--tol', type=int, default=0)
    ap.add_argument('--crop')
    a = ap.parse_args()

    if not a.ref:
        if not (a.box and a.crop):
            ap.error('without REF, --box and --crop are required')
        region(Image.open(a.actual), a.box).save(a.crop)
        print(f'cropped {a.box[2]}x{a.box[3]} -> {a.crop}')
        return

    act, ref = Path(a.actual), Path(a.ref)
    if act.is_dir():
        pairs = [(f, ref / f.name) for f in sorted(act.glob('*.png')) if f.name != 'contact.png']
    else:
        pairs = [(act, ref)]
    failed = 0
    for x, y in pairs:
        if not y.exists():
            print(f'{x.name}: no reference')
            failed += 1
            continue
        bbox, msg = compare(x, y, a.box, a.tol)
        print(f'{x.name}: {msg}')
        if msg != 'same':
            failed += 1
        if bbox and a.crop and len(pairs) == 1:
            Image.open(x).crop(bbox).save(a.crop)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
