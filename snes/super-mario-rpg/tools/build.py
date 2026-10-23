"""Build data for the Korean name patch (items and enemies).

Character encoding used by the tables: u16 per character.
  < 0x0100       static menu-font code (korTBL2)
  0x8000 | n     dynamic glyph n (not in the menu font)

Outputs (build/):
  names.bin      256 items   x 21 bytes: [icon][10 x u16]
  skills.bin     64 specials x 21 bytes, same layout
  enemies.bin    256 enemies x 16 bytes: [8 x u16]
  dlgnames.bin   256 items   x 22 bytes: [header][dialogue-encoded name..., 0], for the
                 dialogue item-name codes; header = byte length | $80 if the name ends
                 in a final consonant (picks 을/를 at run time)
  particles.bin  [len][bytes x2] for 을, then 를, in dialogue encoding
  lvskills.bin   27 ally specials x 16 bytes: [header][dialogue-encoded name], for the
                 level-up screen; header = byte length | $80 if the name ends in a final
                 consonant; syllables the dialogue font lacks use prefix $20
  lvtext.asm     the level-up screen's "(을)를 배웠습니다." without the particle, which
                 now follows the special's name
                 dialogue item-name code ($1A); dialogue font codes come from korTBL
  hint.asm       strings of the field special screen's next-special hint (name encoding)
  glyph_offs.bin u16 per dynamic glyph: offset of its 8x12 2bpp data from $E42B00
  glyphs.asm     places the glyph data into free space reachable from $E42B00
  glyphs.txt     glyph index -> syllable
"""
import json
import os
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent / 'py'))
import textusage  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / 'build'
ITEM_TABLE, ITEM_ENTRY, ITEM_LEN = 0x3A41FC, 15, 10
ENEMY_TABLE, ENEMY_ENTRY, ENEMY_LEN = 0x398C11, 8, 8
SKILL_TABLE, SKILL_COUNT = 0x3A137F, 0x40   # ally specials; entries share the item format
FONT = ROOT / 'tools/fonts/galmuri/Galmuri11-Condensed.ttf'
# Galmuri11-Condensed at 12px sits one row lower than the V1.0 glyphs.
FONT_DY = -1
GLYPH_BYTES = 0x18
# The battle renderer reads glyphs as $E42B00 + 16-bit offset, so the data must
# live in ROM 0x242B00-0x252AFF. These runs are zero in the JP ROM and in V1.0.
GLYPH_BASE = 0x242B00
FREE_RUNS = [(0x24EDD8, 4648), (0x2511C2, 1601), (0x252534, 1484), (0x251D48, 697)]
# Free bytes right after the dialogue font's last glyph (index $3DF): glyph
# indices $3E0-$3FF, written as prefix $20 + low byte. Only the level-up
# screen's skill names use them; the dialogue engine knows no prefix $20.
DLG_EXT_BASE, DLG_EXT_COUNT = 0x249D00, 32
LV_SKILL_ENTRY = 16
# Menu-font syllables no menu text, name or name icon uses. The field special
# screen's hint is on a layer that cannot show dynamic glyphs, so its missing
# syllables replace these glyphs (shared with the battle menus).
MENU_REUSE = [0x85, 0x9B, 0xDF]
# korTBL2 lines whose menu-font glyph is something else (checked against the ROM,
# data/tbl/menu_font_audit.txt): 5F is a dot, FF is 빼. Those syllables become
# dynamic glyphs.
MENU_TBL_WRONG = {0x5F: '힐', 0xFF: '휠'}
HINT_TEXT = (('KoHintLv', '레벨 '), ('KoHintI', '이 되면 '), ('KoHintGa', '가 되면 '),
             ('KoHintLine3', '새로운 기술을 배웁니다'))
LV_TEXT_START, LV_TEXT_END = 0x2D300, 0x2D800   # level-up screen strings


def load_tbl(path):
    tbl = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        m = re.match(r'([0-9A-Fa-f]{2})=(.)$', line)
        if m:
            tbl.setdefault(m.group(2), int(m.group(1), 16))
    return tbl


def render_glyph(font, ch):
    im = Image.new('1', (8, 14), 0)
    ImageDraw.Draw(im).text((0, FONT_DY), ch, font=font, fill=1)
    px = im.load()
    out = bytearray()
    for y in range(12):
        out.append(sum(px[x, y] << (7 - x) for x in range(8)))
        out.append(0)
    return bytes(out)


USED_DLG_CODES = set()
OVERRIDES = json.loads((ROOT / 'data/name_overrides.json').read_text())


def load_names(path, kind=None):
    if not path.exists():
        return {}
    # Spaces are dropped: names are short and each space costs a full 8px cell.
    names = {int(x['id_hex'], 16): x['ko'].replace(' ', '') for x in json.loads(path.read_text())}
    for h, ko in OVERRIDES.get(kind, {}).items():
        names[int(h, 16)] = ko
    return names


class Encoder:
    def __init__(self, tbl):
        self.tbl = tbl
        self.dyn = {}

    def encode(self, label, text, length, fallback):
        if not text:
            return [c if c >= 0x20 else 0x20 for c in fallback[:length]]
        if len(text) > length:
            sys.exit(f'{label} {text!r}: longer than {length}')
        out = []
        for ch in text:
            if ch in self.tbl:
                out.append(self.tbl[ch])
            elif '가' <= ch <= '힣':
                out.append(0x8000 | self.dyn.setdefault(ch, len(self.dyn)))
            else:
                sys.exit(f'{label} {text!r}: no glyph for {ch!r}')
        return out + [0x20] * (length - len(out))


DLG_ENTRY = 22
DLG_FONT = 0x244000     # dialogue font: 24 bytes per glyph, index below
# 2-byte dialogue codes that no parsed text uses (dialogues, battle dialogue and
# messages, item descriptions, menu texts, enemy attack names). Their glyphs are
# replaced by syllables the names need but V1.0's dialogue font lacks.
# Ordered by preference; build fails if V1.0 text uses any of them (textusage.py).
DLG_REUSE = [0x1DD4, 0x1DF5, 0x1E00, 0x1E1C, 0x1E47, 0x1E9A, 0x1EFE, 0x1F04, 0x1F13, 0x1F15,
             0x1F87, 0x1F8D, 0x1F93, 0x1FA0, 0x1FA7, 0x1D12, 0x1F44, 0x1FBD, 0x1FF2,
             0x1F5B, 0x1F5C]
# Codes the V1.0 text uses only for 줏 and 궈, which appear only in the misspellings
# dialogue_fixes.json corrects (줏어 -> 주워, 잠궈 -> 잠가); no rebuilt text uses them.
DLG_REUSE_FIXED = [0x1F7F, 0x1FA9]
DLG_FIXED_GONE = '줏궈'
# Syllables drawn on those codes in v1.2. 셸 is no longer in any name but keeps
# its code, so text built for v1.2 never changes meaning.
DLG_PINNED = {0x1D12: '캔', 0x1DD4: '깃', 0x1DF5: '널', 0x1E00: '닉', 0x1E1C: '링', 0x1E47: '몽', 0x1E9A: '샷',
              0x1EFE: '샹', 0x1F04: '셜', 0x1F13: '셸', 0x1F15: '쉘', 0x1F44: '캡', 0x1F5B: '핸', 0x1F5C: '훈',
              0x1F7F: '콰', 0x1F87: '슐', 0x1F8D: '싹', 0x1F93: '쑥', 0x1FA0: '잣', 0x1FA7: '츠', 0x1FA9: '힐',
              0x1FBD: '퀸', 0x1FF2: '탕'}


def dlg_glyph_index(code):
    return code - 0x20 if code < 0x100 else 0xE0 + ((code >> 8) - 0x1D) * 0x100 + (code & 0xFF)


def load_dlg_tbl(path):
    tbl = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        m = re.match(r'([0-9A-Fa-f]{2,4})=(.)$', line)
        if m:
            tbl.setdefault(m.group(2), bytes.fromhex(m.group(1)))
    return tbl


def extend_menu_tbl(rom, tbl, needed):
    """Map syllables missing from the menu font onto MENU_REUSE codes."""
    used = set()
    for i in range(textusage.MENU_TEXT_COUNT):
        a = textusage.MENU_TEXT_BASE + int.from_bytes(rom[textusage.MENU_TEXT_PTRS + i * 2:][:2], 'little')
        used |= set(rom[a:rom.index(0, a)])
    for i in range(256):
        used |= set(rom[ITEM_TABLE + i * ITEM_ENTRY:][:ITEM_ENTRY])
    for i in range(SKILL_COUNT):
        used |= set(rom[SKILL_TABLE + i * ITEM_ENTRY:][:ITEM_ENTRY])
    for i in range(256):
        used |= set(rom[ENEMY_TABLE + i * ENEMY_ENTRY:][:ENEMY_ENTRY])
    clash = [f'{c:02X}' for c in MENU_REUSE if c in used]
    if clash:
        sys.exit(f'MENU_REUSE codes used by V1.0 text: {clash}')
    for ch in [ch for ch, c in tbl.items() if c in MENU_REUSE]:
        del tbl[ch]
    added = {}
    reuse = iter(MENU_REUSE)
    for ch in sorted(c for c in needed if '가' <= c <= '힣' and c not in tbl):
        code = next(reuse, None)
        if code is None:
            sys.exit('MENU_REUSE exhausted')
        tbl[ch] = added[ch] = code
    return added


def extend_dlg_tbl(dlg_tbl, needed):
    """Map syllables missing from the dialogue font onto DLG_REUSE codes.

    A syllable whose own code is one of them would be drawn with the new glyph
    (힐 was drawn as 캡), so it counts as missing too. Released ROMs keep their
    code for every syllable in DLG_PINNED, needed or not; other missing
    syllables take the codes left over."""
    codes = DLG_REUSE + DLG_REUSE_FIXED
    clash = [f'{c:04X}' for c in DLG_REUSE if c in USED_DLG_CODES]
    if clash:
        sys.exit(f'reused dialogue codes appear in V1.0 text: {clash}')
    lost = [ch for ch, c in dlg_tbl.items() if len(c) == 2 and int.from_bytes(c, 'big') in codes]
    for ch in lost:
        del dlg_tbl[ch]
    added = {}
    for code, ch in DLG_PINNED.items():
        dlg_tbl[ch] = code.to_bytes(2, 'big')
        added[ch] = code
    reuse = iter(c for c in codes if c not in DLG_PINNED)
    for ch in sorted(needed - set(dlg_tbl)):
        code = next(reuse, None)
        if code is None:
            sys.exit(f'out of reusable dialogue codes for {ch}' + (' (its own code was reused)' if ch in lost else ''))
        dlg_tbl[ch] = code.to_bytes(2, 'big')
        added[ch] = code
    return added


def dlg_entry(dlg_tbl, label, text, fallback, missing):
    if not text:
        name = bytes(c for c in fallback if c >= 0x20).rstrip(b' ')
        return bytes([len(name)]) + name + b'\0'
    out = b''
    for ch in text:
        code = dlg_tbl.get(ch)
        if code is None:
            missing.setdefault(ch, []).append(label)
            code = dlg_tbl['?']
        out += code
    batchim = bool(text) and '가' <= text[-1] <= '힣' and (ord(text[-1]) - 0xAC00) % 28 != 0
    return bytes([len(out) | (0x80 if batchim else 0)]) + out + b'\0'


def u16s(chars):
    return b''.join(c.to_bytes(2, 'little') for c in chars)


def place_glyphs(glyphs):
    """Fill the free runs in order; returns per-glyph offsets and (rom, bytes) chunks."""
    offs, chunks, gi = [], [], 0
    for start, size in FREE_RUNS:
        n = min(size // GLYPH_BYTES, len(glyphs) - gi)
        if n <= 0:
            continue
        chunks.append((start, b''.join(glyphs[gi:gi + n])))
        offs += [start + k * GLYPH_BYTES - GLYPH_BASE for k in range(n)]
        gi += n
    if gi < len(glyphs):
        sys.exit(f'glyph space full: {len(glyphs)} glyphs, room for {gi}')
    return offs, chunks


def main():
    rom = (ROOT / 'rom/smrpg_kr_v1.sfc').read_bytes()
    global USED_DLG_CODES
    USED_DLG_CODES = textusage.used_codes(rom)
    enc = Encoder({ch: c for ch, c in load_tbl(ROOT / 'data/tbl/korTBL2.utf8.tbl').items()
                   if MENU_TBL_WRONG.get(c) != ch})
    menu_added = extend_menu_tbl(rom, enc.tbl, {c for _, t in HINT_TEXT for c in t})
    items = load_names(ROOT / 'data/items_ko.json', 'item')
    enemies = load_names(Path(os.environ.get('ENEMIES_JSON', ROOT / 'data/enemies_ko.json')), 'enemy')

    names = bytearray()
    for i in range(256):
        orig = rom[ITEM_TABLE + i * ITEM_ENTRY:][:ITEM_ENTRY]
        names.append(orig[0])
        names += u16s(enc.encode(f'item {i:02X}', items.get(i, ''), ITEM_LEN, orig[1:]))

    dlg_tbl = load_dlg_tbl(ROOT / 'data/tbl/korTBL.utf8.tbl')
    font = ImageFont.truetype(str(FONT), 12)
    extra = json.loads((ROOT / 'data/dialogue_names.json').read_text())
    fixes = json.loads((ROOT / 'data/dialogue_fixes.json').read_text())
    skills = load_names(Path(os.environ.get('SKILLS_JSON', ROOT / 'data/skills_ko.json')), 'skill')
    dlg_text = (list(items.values()) + list(extra['bracketed'].values()) + list(extra['bare'].values())
                + [f['replace'] for f in fixes])
    gone = sorted({c for n in dlg_text + list(skills.values()) for c in n if c in DLG_FIXED_GONE})
    if gone:
        sys.exit(f'syllables whose dialogue code was reused appear in new text: {gone}')
    # Skill names go to the dialogue font extension when a syllable is missing,
    # except syllables that lost their code to DLG_REUSE (drawn on a new code).
    reused = {ch for ch, c in dlg_tbl.items() if len(c) == 2 and int.from_bytes(c, 'big') in DLG_REUSE + DLG_REUSE_FIXED}
    needed = {c for n in dlg_text for c in n if '가' <= c <= '힣'}
    needed |= {c for n in skills.values() for c in n if c in reused}
    dlg_added = extend_dlg_tbl(dlg_tbl, needed)
    bad = sorted({(ch, f'{int.from_bytes(dlg_tbl[ch], "big"):04X}') for n in dlg_text + list(skills.values()) for ch in n
                  if ch in dlg_tbl and len(dlg_tbl[ch]) == 2
                  and int.from_bytes(dlg_tbl[ch], 'big') in DLG_REUSE + DLG_REUSE_FIXED and dlg_added.get(ch) is None})
    if bad:
        sys.exit(f'name syllables on a reused dialogue code: {bad}')
    missing = {}
    dlg_bin = bytearray()
    for i in range(256):
        orig = rom[ITEM_TABLE + i * ITEM_ENTRY:][:ITEM_ENTRY]
        e = dlg_entry(dlg_tbl, f'{i:02X}', items.get(i, ''), orig[1:1 + ITEM_LEN], missing)
        if len(e) > DLG_ENTRY:
            sys.exit(f'dialogue name {i:02X} too long')
        dlg_bin += e.ljust(DLG_ENTRY, b'\0')

    skill_bin = bytearray()
    for i in range(SKILL_COUNT):
        orig = rom[SKILL_TABLE + i * ITEM_ENTRY:][:ITEM_ENTRY]
        skill_bin.append(orig[0])
        skill_bin += u16s(enc.encode(f'skill {i:02X}', skills.get(i, ''), ITEM_LEN, orig[1:]))

    lv_bin, lv_ext = bytearray(), {}
    for i in range(SKILL_COUNT):
        out = b''
        for ch in skills.get(i, ''):
            if ch in dlg_tbl:
                out += dlg_tbl[ch]
            else:
                if ch not in lv_ext:
                    lv_ext[ch] = len(lv_ext)
                out += bytes([0x20, lv_ext[ch]])
        if len(out) >= LV_SKILL_ENTRY:
            sys.exit(f'level-up skill name {i:02X} too long')
        name = skills.get(i, '')
        batchim = bool(name) and '가' <= name[-1] <= '힣' and (ord(name[-1]) - 0xAC00) % 28 != 0
        lv_bin += (bytes([len(out) | (0x80 if batchim else 0)]) + out).ljust(LV_SKILL_ENTRY, b'\0')
    if len(lv_ext) > DLG_EXT_COUNT:
        sys.exit('dialogue font extension full')

    enemy_bin = bytearray()
    for i in range(256):
        orig = rom[ENEMY_TABLE + i * ENEMY_ENTRY:][:ENEMY_ENTRY]
        enemy_bin += u16s(enc.encode(f'enemy {i:02X}', enemies.get(i, ''), ENEMY_LEN, orig))

    hint = ['; generated by tools/build.py']
    for label, text in HINT_TEXT:
        codes = enc.encode(label, text, len(text), b'') + [0]
        hint += [f'{label}:', '    dw ' + ','.join(f'${c:04X}' for c in codes)]

    order = sorted(enc.dyn, key=enc.dyn.get)
    offs, chunks = place_glyphs([render_glyph(font, ch) for ch in order])

    BUILD.mkdir(exist_ok=True)
    (BUILD / 'names.bin').write_bytes(names)
    (BUILD / 'enemies.bin').write_bytes(enemy_bin)
    (BUILD / 'skills.bin').write_bytes(skill_bin)
    (BUILD / 'dlgnames.bin').write_bytes(dlg_bin)
    (BUILD / 'particles.bin').write_bytes(b''.join(bytes([len(dlg_tbl[c])]) + dlg_tbl[c].ljust(2, b'\0') for c in '을를'))
    (BUILD / 'lvskills.bin').write_bytes(lv_bin)
    (BUILD / 'hint.asm').write_text('\n'.join(hint) + '\n')
    enc_d = lambda text: b''.join(dlg_tbl[c] for c in text)
    learned = enc_d('(을)를 배웠습니다.') + b'\0'
    at = rom.find(learned, LV_TEXT_START, LV_TEXT_END)
    if at < 0 or rom.find(learned, at + 1, LV_TEXT_END) >= 0:
        sys.exit('level-up "learned" line not found once')
    new = (enc_d('배웠습니다.') + b'\0').ljust(len(learned), b'\0')
    (BUILD / 'lvtext.asm').write_text(f'org ${0xC00000 | at:06X}\n    db ' + ','.join(f'${b:02X}' for b in new) + '\n')
    # 줏/궈 go last: dlg_rewrite.py decodes the V1.0 text with the last entry per
    # code, and its fixes look for the misspellings (잠궈 -> 잠가).
    gone_codes = {ch: c.to_bytes(2, 'big') for ch, c in zip(DLG_FIXED_GONE, DLG_REUSE_FIXED)}
    (BUILD / 'dlg_tbl.json').write_text(json.dumps({k: v.hex() for k, v in {**dlg_tbl, **gone_codes}.items()}, ensure_ascii=False))
    (BUILD / 'glyph_offs.bin').write_bytes(b''.join(o.to_bytes(2, 'little') for o in offs))
    asm = ['; generated by tools/build.py']
    for k, (start, data) in enumerate(chunks):
        (BUILD / f'glyphs{k}.bin').write_bytes(data)
        snes = 0xC00000 | start
        asm += [f'org ${snes:06X}', f'    incbin "glyphs{k}.bin"', f'assert pc() <= ${snes + len(data):06X}']
    for ch, code in sorted(dlg_added.items(), key=lambda kv: kv[1]):
        snes = 0xC00000 | (DLG_FONT + dlg_glyph_index(code) * GLYPH_BYTES)
        data = ','.join(f'${b:02X}' for b in render_glyph(font, ch))
        asm += [f'org ${snes:06X}   ; dialogue {code:04X} = {ch}', f'    db {data}']
    for ch, code in menu_added.items():
        data = ','.join(f'${b:02X}' for b in render_glyph(font, ch))
        asm += [f'org ${0xC00000 | (GLYPH_BASE + (code - 0x20) * GLYPH_BYTES):06X}   ; menu font {code:02X} = {ch}', f'    db {data}']
    for ch, n in lv_ext.items():
        data = ','.join(f'${b:02X}' for b in render_glyph(font, ch))
        asm += [f'org ${0xC00000 | (DLG_EXT_BASE + n * GLYPH_BYTES):06X}   ; dialogue font extension {n:02X} = {ch}', f'    db {data}']
    (BUILD / 'glyphs.asm').write_text('\n'.join(asm) + '\n')
    (BUILD / 'dlg_added.txt').write_text(''.join(f'{v:04X}={k}\n' for k, v in sorted(dlg_added.items(), key=lambda kv: kv[1])), encoding='utf-8')
    (BUILD / 'glyphs.txt').write_text(''.join(f'{v:03X} {k}\n' for k, v in enc.dyn.items()), encoding='utf-8')
    if missing:
        print('not in the dialogue font (shown as ?):', ''.join(sorted(missing)))
    print(f'items {len(items)}, skills {len(skills)}, enemies {len(enemies)}, dynamic glyphs {len(order)} in {len(chunks)} chunk(s)')


if __name__ == '__main__':
    main()
