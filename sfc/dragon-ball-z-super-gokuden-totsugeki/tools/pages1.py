"""Fully printed dialogue pages from a lua/scenario.lua run with SHOTS=1.

usage: pages1.py run_dir line_id(hex)   -> frames of q*.png shots, one per page

A page counts as finished on the last shot before white text in the lower half of
the screen starts to disappear (the page is cleared for the next one).
"""
import os
import sys

import numpy as np
from PIL import Image


def ink(path):
    a = np.asarray(Image.open(path).convert("RGB"))[112:224]
    return a.min(axis=2) >= 240


def pages(d, tid):
    ev = [(int(a), int(b, 16)) for a, b in (l.split() for l in open(f"{d}/ids.txt"))]
    shots = sorted(int(x[1:6]) for x in os.listdir(d) if x.startswith("q"))
    for k, (f, i) in enumerate(ev):
        if i != tid:
            continue
        end = ev[k + 1][0] if k + 1 < len(ev) else 10**9
        fs = [s for s in shots if f <= s < end + 6]
        m = [ink(f"{d}/q{s:05d}.png") for s in fs]
        out = []
        for j in range(len(fs) - 1):
            cur, nxt = m[j], m[j + 1]
            # text right of the face column, some of it gone in the next shot, not a closing-step repeat
            if cur[:, 84:].sum() > 60 and (cur & ~nxt).sum() > 20 and not (out and fs[j] - out[-1] <= 9):
                out.append(fs[j])
        return out
    return None


if __name__ == "__main__":
    print(pages(sys.argv[1], int(sys.argv[2], 16)))
