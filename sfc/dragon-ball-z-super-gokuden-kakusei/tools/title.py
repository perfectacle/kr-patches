"""Build the Korean title screen BG3 graphics and insert them into the ROM.

usage: title.py in.sfc out.sfc [--png preview.png]

Title BG3 uses two LZSS assets (see kr_patch.lzss), each referenced from a 5-byte table
entry (addr lo, addr hi, bank, size lo, size hi):
  - 2bpp tiles 0x000-0x134 at $89:9B9D, entry at file 0xD720
  - 32x32 tilemap at $89:C4F3, entry at file 0xD95F
"DRAGON BALL Z" and "(c) BANDAI 1995" are left untouched; their (c) tiles are
shared with the first line of the copyright notice.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

from kr_patch.lzss import compress, decompress
from kr_patch.sfc.tiles import planar_to_sfc, sfc_to_planar

FONT_DIR = "/System/Library/AssetsV2/com_apple_MobileAsset_Font8"
GALMURI = os.path.join(os.path.dirname(__file__), "fonts")
TITLE_FONT = f"{FONT_DIR}/a7a90316a83e0693b3d971d89b235ee578c59f0c.asset/AssetData/BMYeongSung-Regular.otf"
SUB_FONT = f"{GALMURI}/Galmuri11-Bold.ttf"
COPY_FONT = f"{GALMURI}/Galmuri11-Condensed.ttf"


class Asset:
    def __init__(self, ptr, reloc):
        self.ptr, self.reloc = ptr, reloc

    def load(self, rom):
        a = rom[self.ptr] | rom[self.ptr + 1] << 8 | rom[self.ptr + 2] << 16
        self.off = ((a >> 16) & 0x7F) * 0x8000 + (a & 0x7FFF)
        self.data, self.clen = decompress(rom, self.off)
        return self.data

    def store(self, rom, data):
        new = compress(data)
        assert decompress(new, 0)[0] == data
        if len(new) <= self.clen:
            off = self.off
        else:
            off = self.reloc
            if any(b != 0xFF for b in rom[off:off + len(new)]):
                sys.exit(f"relocation target {off:#x} is not free")
            rom[self.ptr:self.ptr + 3] = bytes([off & 0xFF, 0x80 | (off >> 8) & 0x7F, 0x80 | off >> 15])
        rom[off:off + len(new)] = new
        print(f"asset @{self.ptr:#x}: {len(new):#x} bytes at {off:#x} (was {self.clen:#x})")


# Free space in the same bank range: file 0x4C801-0x4FFFF is all 0xFF.
CHR = Asset(0xD720, 0x4D000)
MAP = Asset(0xD95F, 0x4E800)

SPARE_TILE = 0xFF            # blank, unreferenced by the title tilemap


# ---------------------------------------------------------------- glyphs

def load_font(path, size):
    return ImageFont.truetype(path, size)


def stretched_mask(path, ch, w, h, scale=8):
    """Render ch stretched to fill w*h, supersampled then thresholded."""
    big = Image.new("L", (w * scale * 2, h * scale * 2), 0)
    ImageDraw.Draw(big).text((w * scale // 2, h * scale // 2), ch, font=load_font(path, h * scale), fill=255)
    g = big.crop(big.getbbox()).resize((w * scale, h * scale), Image.LANCZOS).resize((w, h), Image.BOX)
    px = g.load()
    return [[px[x, y] >= 128 for x in range(w)] for y in range(h)]


def pixel_mask(path, size, text, spacing=0):
    """Render a bitmap-style font at its native size; returns (mask, baseline-aligned)."""
    font = load_font(path, size)
    chars = []
    for ch in text:
        im = Image.new("L", (size * 3, size * 3), 0)
        ImageDraw.Draw(im).text((size, size), ch, font=font, fill=255)
        chars.append(im)
    # Crop all glyphs to a common vertical box so baselines line up.
    boxes = [im.getbbox() for im in chars]
    top = min(b[1] for b in boxes if b)
    bot = max(b[3] for b in boxes if b)
    cols = []
    for ch, im, b in zip(text, chars, boxes):
        if ch == " " or not b:
            cols.append([[False] * (size // 3) for _ in range(bot - top)])
            continue
        px = im.load()
        cols.append([[px[x, y] >= 128 for x in range(b[0], b[2])] for y in range(top, bot)])
    rows = []
    for y in range(bot - top):
        r = []
        for i, c in enumerate(cols):
            if i:
                r += [False] * spacing
            r += c[y]
        rows.append(r)
    return rows


def dilate(mask, n):
    h, w = len(mask), len(mask[0])
    for _ in range(n):
        mask = [[mask[y][x] or (x > 0 and mask[y][x - 1]) or (y > 0 and mask[y - 1][x])
                 or (x > 0 and y > 0 and mask[y - 1][x - 1]) for x in range(w)] for y in range(h)]
    return mask


def pad(mask, l, t, r, b):
    w = len(mask[0]) + l + r
    return [[False] * w for _ in range(t)] + [[False] * l + row + [False] * r for row in mask] + \
        [[False] * w for _ in range(b)]


def neighbors(mask, x, y, offs):
    h, w = len(mask), len(mask[0])
    return any(0 <= x + dx < w and 0 <= y + dy < h and mask[y + dy][x + dx] for dx, dy in offs)


def style(mask, fill, edge=None, outline=None, shadow=None):
    """edge: colour for body pixels on the top/left border; outline: 8-neighbour
    ring; shadow: drop shadow towards bottom-right."""
    h, w = len(mask), len(mask[0])
    out = [[0] * w for _ in range(h)]
    ring8 = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
    for y in range(h):
        for x in range(w):
            if mask[y][x]:
                out[y][x] = edge if edge and not (neighbors(mask, x, y, [(-1, 0)]) and
                                                    neighbors(mask, x, y, [(0, -1)])) else fill
            elif outline and neighbors(mask, x, y, ring8):
                out[y][x] = outline
            elif shadow and neighbors(mask, x, y, [(-1, -1), (-1, 0), (0, -1)]):
                out[y][x] = shadow
    return out


# ---------------------------------------------------------------- screen

class Screen:
    """Editable BG3 pixels for selected tilemap cells."""

    def __init__(self, gfx, tmap):
        self.gfx, self.tmap = bytearray(gfx), bytearray(tmap)
        self.px = {}

    def entry(self, cx, cy):
        i = (cy * 32 + cx) * 2
        return self.tmap[i] | self.tmap[i + 1] << 8

    def set_entry(self, cx, cy, e):
        i = (cy * 32 + cx) * 2
        self.tmap[i], self.tmap[i + 1] = e & 0xFF, e >> 8

    def pixel(self, X, Y):
        e = self.entry(X // 8, Y // 8)
        t, hf, vf = e & 0x3FF, e >> 14 & 1, e >> 15 & 1
        x, y = (7 - X % 8 if hf else X % 8), (7 - Y % 8 if vf else Y % 8)
        o = t * 16 + y * 2
        return ((self.gfx[o] >> (7 - x)) & 1) | (((self.gfx[o + 1] >> (7 - x)) & 1) << 1)

    def load(self, cells):
        for cx, cy in cells:
            for y in range(8):
                for x in range(8):
                    self.px[(cx * 8 + x, cy * 8 + y)] = self.pixel(cx * 8 + x, cy * 8 + y)

    def clear(self, cells):
        for cx, cy in cells:
            for y in range(8):
                for x in range(8):
                    self.px[(cx * 8 + x, cy * 8 + y)] = 0

    def blit(self, img, ox, oy):
        for y, row in enumerate(img):
            for x, v in enumerate(row):
                if v and (ox + x, oy + y) in self.px:
                    self.px[(ox + x, oy + y)] = v

    def fill(self, x0, y0, x1, y1, v):
        for y in range(y0, y1):
            for x in range(x0, x1):
                if (x, y) in self.px:
                    self.px[(x, y)] = v

    def commit(self):
        cells = {(x // 8, y // 8) for x, y in self.px}
        owner = {}
        for cx, cy in cells:
            e = self.entry(cx, cy)
            t = e & 0x3FF
            if e & 0xC000:
                sys.exit(f"cell {cx},{cy} uses a flipped tile; give it its own tile first")
            if t in owner:
                sys.exit(f"tile {t:#x} shared by cells {owner[t]} and {(cx, cy)}")
            owner[t] = (cx, cy)
            for y in range(8):
                p0 = p1 = 0
                for x in range(8):
                    v = self.px[(cx * 8 + x, cy * 8 + y)]
                    p0 |= (v & 1) << (7 - x)
                    p1 |= (v >> 1) << (7 - x)
                self.gfx[t * 16 + y * 2] = p0
                self.gfx[t * 16 + y * 2 + 1] = p1


def cells(c0, c1, r0, r1):
    return [(c, r) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)]


def build_title(s):
    """초오공전 (12x3 cells at col 2,row 8) and 각성편 on the brush band below."""
    s.clear(cells(2, 13, 8, 10))
    for i, ch in enumerate("초오공전"):
        body = dilate(pad(stretched_mask(TITLE_FONT, ch, 21, 22), 0, 0, 1, 1), 1)
        s.blit(style(pad(body, 0, 0, 1, 1), fill=1, edge=2, shadow=3), 16 + i * 24, 64)
    sub = cells(5, 10, 11, 12)
    s.clear(sub)
    s.fill(40, 92, 88, 100, 3)                       # brush band behind the text
    for i, ch in enumerate("각성편"):
        body = pad(pixel_mask(SUB_FONT, 12, ch), 1, 1, 1, 1)
        img = style(body, fill=1, outline=2)
        s.blit(img, 40 + i * 16 + (16 - len(img[0])) // 2, 88 + (16 - len(img)) // 2)


BALL_Y, BALL_X0, BALL_PITCH, BALL_W, BALL_H = 48, 103, 13, 12, 12


def clear_balls(s):
    """Blank the katakana dragon-ball row under the logo."""
    s.set_entry(22, 7, (s.entry(22, 7) & 0x1C00) | 0x2000 | SPARE_TILE)
    # (12,6) is a flipped "Z" tile whose only visible pixels are the first ball's rim.
    s.set_entry(12, 6, s.entry(0, 0))
    s.load([(24, 6)])
    s.clear(cells(13, 23, 6, 7))
    for y in range(8):                               # last ball's right rim spills into (24,6)
        s.px[(BALL_X0 + 6 * BALL_PITCH + BALL_W - 1, BALL_Y + y)] = 0


def build_copyright(s, text):
    """Copyright line after the shared (c) tiles: cols 4-29, rows 22-23."""
    area = cells(4, 29, 22, 23)
    s.clear(area)
    g = pixel_mask(COPY_FONT, 12, text, spacing=2)
    img = style(pad(g, 0, 0, 1, 1), fill=1, shadow=3)
    w = len(img[0])
    if w > 26 * 8:
        sys.exit(f"copyright line too wide: {w}px")
    s.blit(img, 36, 176 + (16 - len(img)) // 2)


COPYRIGHT = "버드스튜디오/슈에이샤·후지TV·토에이동화"


def render(s, path):
    pals = {0: [(0, 0, 0), (232, 232, 232), (248, 248, 0), (0, 0, 0)],
            4: [(0, 0, 0), (248, 248, 248), (0, 0, 0), (0, 0, 0)],
            5: [(0, 0, 0), (248, 160, 88), (152, 96, 248), (0, 0, 104)],
            6: [(0, 0, 0), (248, 248, 248), (96, 24, 192), (136, 0, 0)]}
    pals[0][1] = (248, 0, 0)
    pals[1] = [(0, 0, 0), (248, 128, 0), (248, 248, 0), (0, 0, 0)]
    pals[2] = [(0, 0, 0), (248, 128, 0), (248, 0, 0), (0, 0, 0)]
    im = Image.new("RGB", (256, 224), (120, 230, 120))
    g = s.gfx
    for cy in range(28):
        for cx in range(32):
            e = s.entry(cx, cy)
            t, p, hf, vf = e & 0x3FF, (e >> 10) & 7, e >> 14 & 1, e >> 15 & 1
            for y in range(8):
                for x in range(8):
                    xx, yy = (7 - x if hf else x), (7 - y if vf else y)
                    o = t * 16 + yy * 2
                    v = ((g[o] >> (7 - xx)) & 1) | (((g[o + 1] >> (7 - xx)) & 1) << 1)
                    if v:
                        im.putpixel((cx * 8 + x, cy * 8 + y), pals.get(p, pals[0])[v])
    im.resize((768, 672), Image.NEAREST).save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--png")
    ap.add_argument("--no-balls", action="store_true", help="also remove the katakana dragon-ball row")
    ap.add_argument("--all", action="store_true", help="also replace the katakana and copyright line")
    a = ap.parse_args()

    rom = bytearray(open(a.src, "rb").read())
    s = Screen(planar_to_sfc(CHR.load(rom)), MAP.load(rom))
    build_title(s)
    if a.all or a.no_balls:
        clear_balls(s)
    if a.all:
        build_copyright(s, COPYRIGHT)
    s.commit()
    if a.png:
        render(s, a.png)
    CHR.store(rom, sfc_to_planar(bytes(s.gfx)))
    if bytes(s.tmap) != MAP.data:
        MAP.store(rom, bytes(s.tmap))
    open(a.dst, "wb").write(rom)


if __name__ == "__main__":
    main()
