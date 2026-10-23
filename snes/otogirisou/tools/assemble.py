"""Assemble a script text (dump.py kr format) back into the plain 16-bit stream.

Newlines are layout only and ignored. "#LABEL" defines a jump target, "@LABEL" in a control
argument refers to one. Labels are the v1.0 addresses the dump printed; they are names
only, so the text may grow or shrink freely.

usage: assemble.py rom_in.sfc table.tbl script.txt rom_out.sfc
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from script import unlorom
from dump import load_table, KR_START, ENTRIES

ENTRY_TAB = 0x12627

TOKEN = re.compile(r'#([0-9A-F]{6})\n|\{([0-9A-F]{2})(?::([^}]*))?\}|<(\d{4})>|\n|(.)', re.S)


def lorom_next(addr, n):
    for _ in range(n):
        addr += 1
        if addr & 0xFFFF == 0:
            addr += 0x8000
    return addr


NBSP = '\u00a0'   # code 1248: same blank glyph as the space, but asm/wordwrap.asm does not break there
NAME_HONORIFIC = r'(나미|나오미|나오키|\{2[01]\}) (씨|님|군)'

# effect codes may sit between a mark and the bracket/wait that follows it
_WAITS_NEXT = r'(?:\{(?!1C|25|26|27)[0-9A-F]{2}(?::[^}]*)?\})*(?:[」』]|\{16\})'
CLOSE = r'(?=' + _WAITS_NEXT + ')'
OPEN_END = r'(?!' + _WAITS_NEXT + ')'


def normalize_text(text):
    """Map plain punctuation to the game's glyphs.

    The wide comma/period/exclamation glyphs already contain the following gap, so the
    typed space is dropped. Before 」, 』 or an explicit wait {16} a non-waiting form is used, because those
    already wait for a key and the player would have to press twice. Control code arguments
    never contain . ? ! or ", ", so the whole text can be rewritten at once.
    """
    # the wide ？ glyph has only 2px of gap, so the space after a question mark stays
    text = re.sub(r'([,.!]) ', r'\1', text)
    # the same gap when effect codes sit between the mark and the space
    text = re.sub(r'([,.!](?:\{(?!00|1C|25|26|27)[0-9A-F]{2}(?::[^}]*)?\})+) ', r'\1', text)
    # the space between a name and its honorific must not become a line break
    text = re.sub(NAME_HONORIFIC, '\\1' + NBSP + '\\2', text)
    # a mark right after {13} keeps its waiting form: {13} cancels the next wait, and if that
    # wait never comes it would cancel a later one instead
    text = re.sub(r'(?<!\{13\})\.' + CLOSE, '·', text)
    text = re.sub(r'\?' + OPEN_END + '|(?<=\{13\})\?', '？', text)
    # in "!?" the wide glyph's gap would split the pair; the ? that follows waits anyway
    text = re.sub(r'!(?!\?)' + OPEN_END + '|(?<=\{13\})!', '！', text)
    return text


def parse(text, table):
    inv = {}
    for code, ch in table.items():
        inv.setdefault(ch, code)
    items = []  # ('L', name) | ('S', code) | ('R', name)
    for m in TOKEN.finditer(text):
        label, ctl, args, raw, ch = m.groups()
        if label:
            items.append(('L', label))
        elif ctl:
            items.append(('S', 0x1000 | int(ctl, 16)))
            for a in (args.split(',') if args else []):
                items.append(('R', a[1:]) if a.startswith('@') else ('S', int(a)))
        elif raw:
            items.append(('S', int(raw)))
        elif ch is not None:
            if ch not in inv:
                raise SystemExit('no code for %r near %r' % (ch, text[max(0, m.start() - 20):m.start() + 20]))
            items.append(('S', inv[ch]))
    return items


def assemble(items, start=KR_START):
    labels, addr = {}, start
    for kind, v in items:
        if kind == 'L':
            labels[v] = addr
        else:
            addr = lorom_next(addr, 2 if kind == 'S' else 3)
    out = bytearray()
    for kind, v in items:
        if kind == 'S':
            out += v.to_bytes(2, 'big')
        elif kind == 'R':
            out += labels[v].to_bytes(3, 'little')
    return out, labels, addr


def write(rom, data, start=KR_START):
    """Copy the stream into the ROM following LoROM bank layout."""
    addr, i = start, 0
    while i < len(data):
        o = unlorom(addr)
        n = min(len(data) - i, 0x8000 - (o & 0x7FFF))
        rom[o:o + n] = data[i:i + n]
        i += n
        addr = lorom_next(addr, n)
    return addr


if __name__ == '__main__':
    rom_in, tbl, txt, rom_out = sys.argv[1:5]
    rom = bytearray(open(rom_in, 'rb').read())
    items = parse(normalize_text(open(txt, encoding='utf-8').read()), load_table(tbl))
    data, labels, end = assemble(items)
    if unlorom(end) > 0x200000:
        raise SystemExit('script too long: ends at $%06X' % end)
    # clear the old stream area first so stale bytes never remain after a shorter script
    write(rom, bytes(0x200000 - unlorom(KR_START)))
    write(rom, data)
    for i, e in enumerate(ENTRIES['kr']):
        rom[ENTRY_TAB + 3 * i:ENTRY_TAB + 3 * i + 3] = labels['%06X' % e].to_bytes(3, 'little')
    open(rom_out, 'wb').write(rom)
    print('script $%06X-$%06X, %d bytes, %d labels' % (KR_START, end, len(data), len(labels)))
