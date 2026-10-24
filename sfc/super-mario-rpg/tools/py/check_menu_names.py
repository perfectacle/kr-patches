"""Check every item, special and enemy name as the menus draw it.

usage: check_menu_names.py [ROM]      (default build/test.sfc; run by tools/make.sh)

Reads the name tables (KoNames, KoSkills, KoEnemies) and the dynamic glyph
offsets (KoGlyphOffs) back out of the built ROM and compares each character
with the name it should spell:
  - 0x8000 | n: the glyph at $E4:2B00 + offset n must equal the Galmuri glyph
    tools/build.py renders for that syllable. The field menu converts these
    bytes, the battle menu (KoGlyphX) draws them, both from this data.
  - a menu-font code: it must be listed in data/tbl/menu_font_audit.txt for
    that character, and the ROM must still hold the audited glyph. MENU_REUSE
    codes must hold the Galmuri glyph build.py draws there.
Names without a Korean entry keep their V1.0 bytes; those only need audited
codes. Exits 1 with every mismatch listed.
"""
import hashlib
import sys
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import build  # noqa: E402

rom = (Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'build/test.sfc').read_bytes()
font = ImageFont.truetype(str(build.FONT), 12)

audit = {}
for line in (ROOT / 'data/tbl/menu_font_audit.txt').read_text(encoding='utf-8').splitlines():
    if line and not line.startswith('#'):
        audit[int(line[:2], 16)] = (line[3], line[5:])


def in_rom(path):
    data = (ROOT / 'build' / path).read_bytes()
    at = rom.find(data)
    if at < 0 or rom.find(data, at + 1) >= 0:
        sys.exit(f'{path}: not found exactly once in the ROM')
    return rom[at:at + len(data)]


def glyph(offset):
    a = build.GLYPH_BASE + offset
    return rom[a:a + build.GLYPH_BYTES]


offs = in_rom('glyph_offs.bin')
offs = [int.from_bytes(offs[i:i + 2], 'little') for i in range(0, len(offs), 2)]
added = {}
for line in (ROOT / 'build/glyphs.asm').read_text(encoding='utf-8').splitlines():
    if '; menu font ' in line:
        code, ch = line.split('; menu font ')[1].split(' = ')
        added[int(code, 16)] = ch

# entry sizes: icon byte + 10 characters x 2 (items, specials), 8 characters x 2 (enemies)
tables = [('item', 'names.bin', 21, 1, 256, build.ITEM_LEN, 'data/items_ko.json', 'item'),
          ('skill', 'skills.bin', 21, 1, build.SKILL_COUNT, build.ITEM_LEN, 'data/skills_ko.json', 'skill'),
          ('enemy', 'enemies.bin', 16, 0, 256, build.ENEMY_LEN, 'data/enemies_ko.json', 'enemy')]
bad, checked = [], 0
for kind, path, entry, skip, count, length, names_json, override in tables:
    data = in_rom(path)
    names = build.load_names(ROOT / names_json, override)
    for i in range(count):
        e = data[i * entry + skip:(i + 1) * entry]
        codes = [int.from_bytes(e[k:k + 2], 'little') for k in range(0, 2 * length, 2)]
        text = names.get(i, '')
        expect = list(text) + [' '] * (length - len(text)) if text else [None] * length
        checked += bool(text)
        for pos, (code, ch) in enumerate(zip(codes, expect)):
            if code & 0x8000:
                n = code & 0x7FFF
                ok = ch is not None and n < len(offs) and glyph(offs[n]) == build.render_glyph(font, ch)
                got = f'dynamic {n}'
            elif code in build.MENU_REUSE:
                ok = ch is not None and added.get(code) == ch and \
                    glyph((code - 0x20) * build.GLYPH_BYTES) == build.render_glyph(font, ch)
                got = f'reused {code:02X}'
            else:
                a = audit.get(code)
                ok = a is not None and (ch is None or a[0] == ch) and \
                    hashlib.sha1(glyph((code - 0x20) * build.GLYPH_BYTES)).hexdigest() == a[1]
                got = f'{code:02X}' + (f'={a[0]}' if a else ' (not audited)')
            if not ok:
                bad.append(f'{kind} {i:02X} {text!r} char {pos} {ch!r}: {got}')

for b in bad:
    print(b)
print(f'menu names: {checked} Korean names checked, {len(bad)} mismatches')
sys.exit(1 if bad else 0)
