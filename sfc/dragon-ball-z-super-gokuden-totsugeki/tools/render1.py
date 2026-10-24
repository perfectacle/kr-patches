"""Render text with the ROM's VWF font: render1.py rom table.txt out.png "text" ["text" ...]"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import dialogue1 as D  # noqa: E402
import font1  # noqa: E402
import kr1  # noqa: E402
import width1  # noqa: E402

PAL = {0: (16, 24, 96), 1: (248, 248, 248), 2: (40, 40, 40), 3: (40, 40, 40)}


def render(rom, enc, text, scale=3):
    lines = text.split("/")
    W = max(sum(width1.char_width(c) for c in enc.encode(l)) for l in lines) + 8
    im = Image.new("RGB", (W, 16 * len(lines) + 4), PAL[0])
    for k, l in enumerate(lines):
        x = 4
        for c in enc.encode(l):
            if c != 0x2C5 and font1.valid(c):
                g0, g1 = font1.glyph(rom, c, 0), font1.glyph(rom, c, 1)
                for y in range(16):
                    for xx in range(len(g0[0])):
                        v = g0[y][xx] | (g1[y][xx] << 1)
                        if v:
                            im.putpixel((x + xx, 2 + k * 16 + y), PAL[v])
            x += width1.char_width(c)
    return im.resize((im.width * scale, im.height * scale), Image.NEAREST)


def main():
    rom = open(sys.argv[1], "rb").read()
    enc = kr1.Encoder(D.load_table(sys.argv[2]))
    ims = [render(rom, enc, t) for t in sys.argv[4:]]
    out = Image.new("RGB", (max(i.width for i in ims), sum(i.height + 6 for i in ims)), (0, 0, 0))
    y = 0
    for i in ims:
        out.paste(i, (0, y))
        y += i.height + 6
    out.save(sys.argv[3])


if __name__ == "__main__":
    main()
