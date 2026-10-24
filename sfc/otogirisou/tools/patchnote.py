"""Patch-note images: one row per version (label on the left), 2x scale, red boxes
around the words each example is about.

usage: patchnote.py capture_root v10_addr.tsv v11_addr.tsv freeze_v10.png outdir
Capture dirs (under capture_root) come from work/pages.lua (p<addr>.png + pages.txt);
the address maps from tools/addrmap.py (--raw for v1.0). The early scenes are from one
playthrough per version (k10, k11); later ones from saves made to resume just before them
(work/jumpsave.py, dirs jump/j<line>_10 and _11).
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

FONT = '/System/Library/Fonts/AppleSDGothicNeo.ttc'
SCALE, GAP, LABEL_W = 2, 8, 110
BG, RED = (24, 24, 28), (255, 40, 40)
WORD_GAP = 6        # px; a wider run of empty columns ends a word

# (file, script line, words to box on the v1.0 screen, on the v1.1 screen,
#  capture dirs, page of the line: index into its captured pages)
# Words are counted in reading order as words() splits them; only the point of each
# example is boxed, not every word the retranslation changed.
PLAY = ('k10', 'k11')
SHOTS = [
    ('wrap-brake.png', 78, [5, 6, 25, 26], [6, 23, 24], PLAY, (-1, -1)),
    ('wrap-legend.png', 44, [4, 5, 11, 12], [6, 22], PLAY, (-1, -1)),
    ('fix-sign.png', 79, [13, 14, 15], [15, 16], PLAY, (-1, -1)),
    ('fix-pun.png', 30, [21, 25, 26], [21, 22, 24, 25], PLAY, (-1, -1)),
    ('fix-missing.png', 46, [2, 29], [2, 3, 31, 32, 33, 34, 35], PLAY, (-1, -1)),
    ('fix-tone.png', 104, [18, 24, 25, 26, 27, 28, 29, 30], [21, 22, 28, 29, 30, 31], PLAY, (-1, -1)),
    ('overflow.png', 2294, 'last', 'last', ('jump/j2294_10', 'jump/j2294_11'), (-1, -1)),
    ('broken-bun.png', 4057, [], [], ('jump/j4057_10', 'jump/j4057_11'), (-1, -1)),
    ('broken-name.png', 5352, [7, 8], [11, 12], ('jump/j5352_10', 'jump/j5352_11'), (-1, -1)),
    # the lightning flash on the next page whitens the background
    ('broken-mummy.png', 871, [0, 1], [0, 1], ('jump/j871_10', 'jump/j871_11'), (3, 2)),
    ('term-mummy.png', 267, [3], [4], ('jump/j267_10', 'jump/j267_11'), (-1, -1)),
    ('term-knife.png', 1126, [12], [11], ('jump/j1126_10', 'jump/j1126_11'), (-1, -1)),
    ('term-112.png', 3799, [10], [10], ('jump/j3799_10', 'jump/j3799b_11'), (-1, -1)),
]
# A page end without a key wait: frames after the last sentence finished printing, with no
# key pressed (work/waitdemo.lua, one screenshot per frame from the stop point).
WAIT_DEMO = ('a-wait.png', ('jump/jw_10', 'jump/jw_11'), ((36, 150), (48, 150)),
             ('문장이 다 나온 직후', '버튼을 누르지 않고 2초 뒤'))
FREEZE_FROM = 1351  # first line of the scenario that froze in v1.0


def is_text(p):
    return min(p) > 190


def text_mask(img):
    m = Image.new('1', img.size)
    m.putdata([is_text(p) for p in img.getdata()])
    return m


def words(img):
    """Words in reading order: (box, glyph bitmap). A word is a run of glyph columns on a
    text line with gaps narrower than WORD_GAP."""
    m = text_mask(img)
    w, h = m.size
    px = m.load()
    rows = [y for y in range(h) if any(px[x, y] for x in range(w))]
    lines, start, prev = [], None, None
    for y in rows + [None]:
        if start is not None and (y is None or y - prev > 3):
            lines.append((start, prev))
            start = None
        if y is not None:
            start = y if start is None else start
            prev = y
    out = []
    for y0, y1 in lines:
        ink = [any(px[x, y] for y in range(y0, y1 + 1)) for x in range(w)]
        x = 0
        while x < w:
            if not ink[x]:
                x += 1
                continue
            s, gap, e = x, 0, x
            while x < w and gap < WORD_GAP:
                e, gap = (x, 0) if ink[x] else (e, gap + 1)
                x += 1
            out.append(((s, y0, e, y1), m.crop((s, y0, e + 1, y1 + 1)).tobytes()))
    return out


def boxes_for(img, picks):
    """One box per run of picked words on a line; 'last' picks the bottom text line."""
    ws = words(img)
    if picks == 'last':
        text = [(i, b) for i, (b, _) in enumerate(ws)]
        if text[-1][1][2] - text[-1][1][0] <= 10:      # the page-end icon
            text.pop()
        bottom = max(b[1] for _, b in text)
        picks = [i for i, b in text if b[1] == bottom]
    out = []
    for i in sorted(picks):
        x0, y0, x1, y1 = ws[i][0]
        last = out[-1] if out else None
        if last and last[1] == y0 - 3 and i - 1 in picks:
            out[-1] = (last[0], last[1], x1 + 3, y1 + 3)
        else:
            out.append((x0 - 3, y0 - 3, x1 + 3, y1 + 3))
    return out


def compose(top, bottom, picks=([], []), labels=('v1.0', 'v1.1')):
    font = ImageFont.truetype(FONT, 30)
    w, h = 256 * SCALE, 224 * SCALE
    img = Image.new('RGB', (LABEL_W + w + GAP, 2 * (h + GAP) + GAP), BG)
    d = ImageDraw.Draw(img)
    shots = [Image.open(p).convert('RGB') for p in (top, bottom)]
    boxes = [boxes_for(im, p) for im, p in zip(shots, picks)]
    for r, (label, im) in enumerate(zip(labels, shots)):
        d.text((14, GAP + r * (h + GAP) + h // 2 - 18), label, fill=(235, 235, 235), font=font)
        big = im.resize((w, h), Image.NEAREST)
        bd = ImageDraw.Draw(big)
        for x0, y0, x1, y1 in boxes[r]:
            bd.rectangle((x0 * SCALE, y0 * SCALE, x1 * SCALE, y1 * SCALE), outline=RED, width=4)
        img.paste(big, (LABEL_W, GAP + r * (h + GAP)))
    return img


def compose_grid(rows, headers, labels=('v1.0', 'v1.1')):
    """rows: per version, the screenshots for each column; headers name the columns."""
    font = ImageFont.truetype(FONT, 30)
    small = ImageFont.truetype(FONT, 26)
    w, h = 256 * SCALE, 224 * SCALE
    top = 50
    cols = len(headers)
    img = Image.new('RGB', (LABEL_W + cols * (w + GAP), top + len(rows) * (h + GAP) + GAP), BG)
    d = ImageDraw.Draw(img)
    for c, t in enumerate(headers):
        d.text((LABEL_W + c * (w + GAP) + 8, 12), t, fill=(235, 235, 235), font=small)
    for r, (label, shots) in enumerate(zip(labels, rows)):
        y = top + GAP + r * (h + GAP)
        d.text((14, y + h // 2 - 18), label, fill=(235, 235, 235), font=font)
        for c, p in enumerate(shots):
            img.paste(Image.open(p).convert('RGB').resize((w, h), Image.NEAREST), (LABEL_W + c * (w + GAP), y))
    return img


def line_pages(capdir, addr_tsv):
    spans = [(int(s, 16), int(e, 16), int(n)) for n, s, e in (l.split('\t') for l in open(addr_tsv) if l.strip())]
    out = {}
    for l in open(os.path.join(capdir, 'pages.txt')):
        if l.strip():
            a = int(l.split()[1], 16)
            for s, e, n in spans:
                if s <= a < e:
                    out.setdefault(n, []).append(os.path.join(capdir, 'p%06X.png' % a))
    return out


def main(root, a10, a11, freeze, outdir):
    for name, n, p10, p11, dirs, page in SHOTS:
        top, bottom = (line_pages(os.path.join(root, d), a)[n][i] for d, a, i in zip(dirs, (a10, a11), page))
        compose(top, bottom, (p10, p11)).save(os.path.join(outdir, name))
        print(name, os.path.basename(top), os.path.basename(bottom))
    name, dirs, frames, headers = WAIT_DEMO
    rows = [[os.path.join(root, d, 'w%04d.png' % f) for f in fs] for d, fs in zip(dirs, frames)]
    compose_grid(rows, headers).save(os.path.join(outdir, name))
    print(name)
    # the v1.1 page with the most text among the first pages of the scenario
    v11 = line_pages(os.path.join(root, PLAY[1]), a11)
    cands = [p for n in sorted(v11) if n >= FREEZE_FROM for p in v11[n]][:6]
    best = max(cands, key=lambda p: sum(is_text(q) for q in Image.open(p).convert('RGB').getdata()))
    compose(freeze, best).save(os.path.join(outdir, 'freeze-lap2.png'))
    print('freeze-lap2.png', os.path.basename(best))


if __name__ == '__main__':
    main(*sys.argv[1:6])
