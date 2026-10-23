"""Write the dialogue font as a JSON glyph store keyed by glyph code, for `krpatch ocr`.

usage: fontjson.py rom.sfc first last out.json

    python3 tools/fontjson.py build/v1.0.sfc 1 1246 build/font.json
    krpatch ocr build/font.json build/ocr --per-row 10 --scale 4 --fix-mo > ocr.tsv

The font draws ㅁ with filled corners and ㅇ without, so `--fix-mo` applies.
"""
import sys

from kr_patch.glyph import store

from font import glyph, groups

rom = open(sys.argv[1], 'rb').read()
first, last = int(sys.argv[2]), int(sys.argv[3])
gs = groups(rom)
glyphs = {str(c): g for c in range(first, last + 1) if (g := glyph(rom, c, gs))}
store.save(sys.argv[4], glyphs)
print(f'{len(glyphs)} glyphs')
