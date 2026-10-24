"""Render JP-ROM text with its own dialogue font so it can be read visually.
usage: render_jp.py ROM OUT.png SPEC...   SPEC = d:<dialogue id hex> | b:<battle dialogue id hex>
Bytes 0x20-0xFF are drawn from the font at 0x244000 (24 bytes per glyph); other
codes are drawn as a small box with the hex value. 0x01 starts a new line."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dialogue  # noqa: E402

rom = Path(sys.argv[1]).read_bytes()
FONT = 0x244000


def glyph(c):
    g = rom[FONT + (c - 0x20) * 24:][:24]
    im = Image.new('L', (8, 12), 255)
    px = im.load()
    for y in range(12):
        for x in range(8):
            v = ((g[y * 2] >> (7 - x)) & 1) | (((g[y * 2 + 1] >> (7 - x)) & 1) << 1)
            if v:
                px[x, y] = 0 if v == 1 else 110
    return im


def lines_for(spec):
    kind, i = spec.split(':')
    i = int(i, 16)
    if kind == 'd':
        a = dialogue.address(rom, i)
        data = rom[a:a + 260]
    else:
        a = 0x390000 | int.from_bytes(rom[0x396554 + i * 2:0x396556 + i * 2], 'little')
        data = rom[a:a + 200]
    out, cur = [], []
    for c in data:
        if c in (0x06,) or (kind == 'b' and c == 0x00):
            break
        if c == 0x01:
            out.append(cur); cur = []
        else:
            cur.append(c)
    out.append(cur)
    return [l for l in out if l][:8]


rows = []
for spec in sys.argv[3:]:
    rows.append(('#' + spec, None))
    for l in lines_for(spec):
        rows.append((None, l))
W = max(len(l) for _, l in rows if l) * 9 + 10
img = Image.new('RGB', (max(W, 120), 14 * len(rows) + 4), 'white')
d = ImageDraw.Draw(img)
y = 2
for label, l in rows:
    if label:
        d.text((2, y), label, fill='blue')
    else:
        x = 2
        for c in l:
            if c >= 0x20:
                img.paste(glyph(c), (x, y))
            else:
                d.rectangle([x, y + 2, x + 7, y + 10], outline='red')
            x += 9
    y += 14
img = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
img.save(sys.argv[2])
