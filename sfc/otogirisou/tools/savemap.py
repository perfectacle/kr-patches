"""Build the script position tables used to load v1.0 and Japanese save files in v1.1.

Saves hold the script position the game was at (right after a page clear {25}/{26}/{27},
or a page start after a choice). For each script line the control codes of the old and
the v1.1 script are aligned; every old page clear that survives gets an entry, and so does
every line start (jump targets, saves after a choice). asm/savecompat.asm takes the
largest entry not above the saved position, so any other position resumes at the start
of its page.

Tables: count (16 bit), then count x (old 24 bit, new 24 bit), sorted by old.
  $17:8000  v1.0: old = LoROM address
  $19:8000  Japanese: old = bit offset from the text base $15:E401
usage: savemap.py v10_script.txt v11_script.txt jp.sfc rom.sfc
"""
import difflib, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from assemble import normalize_text, lorom_next
from dump import KR_START, ENTRIES, items

TABLES = {'v10': 0xB8000, 'jp': 0xC8000}     # $17:8000, $19:8000
TOKEN = re.compile(r'\{([0-9A-F]{2})(?::([^}]*))?\}|<\d{4}>|(.)', re.S)
PAGE = {'25', '26', '27'}


def walk(lines, normalize):
    """Per line: start address and [(code, address after the code and its arguments)]."""
    addr, out = KR_START, []
    for line in lines:
        if line.startswith('#'):
            out.append((addr, []))
            continue
        text = normalize_text(line) if normalize else line
        start, codes = addr, []
        for m in TOKEN.finditer(text):
            code, args, ch = m.groups()
            if code is not None:
                n = 2 + sum(3 if a.startswith('@') else 2 for a in (args.split(',') if args else []))
                addr = lorom_next(addr, n)
                codes.append((code, addr))
            else:
                addr = lorom_next(addr, 2)
        out.append((start, codes))
    return out


def walk_jp(rom):
    """The same per-line view of the Japanese stream, in bit offsets. Lines break where
    dump.py breaks them (before and after a jump target label, after {25}), which is how
    tables/script-jp.txt lines up with tables/script.txt."""
    its = list(items('jp', rom))
    targets = {v for _, _, a in its for k, v in a if k == 'r'} | set(ENTRIES['jp'])
    lines = [[None, []]]
    for i, (p, s, _) in enumerate(its):
        after = its[i + 1][0] if i + 1 < len(its) else p
        if p in targets:
            lines += [[p, []], [p, []]]
        if lines[-1][0] is None:
            lines[-1][0] = p
        if s >= 0x1000:
            code = '%02X' % (s & 0xFFF)
            lines[-1][1].append((code, after))
            if code == '25':
                lines.append([after, []])
    return [(s if s is not None else 0, c) for s, c in lines]


def table(old, new):
    pairs = {}
    for (sa, ca), (sb, cb) in zip(old, new):
        if ca or cb:
            pairs[sa] = sb
        sm = difflib.SequenceMatcher(None, [c for c, _ in ca], [c for c, _ in cb], autojunk=False)
        for i, j, n in sm.get_matching_blocks():
            for k in range(n):
                if ca[i + k][0] in PAGE:
                    pairs[ca[i + k][1]] = cb[j + k][1]
    entries = sorted(pairs.items())
    data = len(entries).to_bytes(2, 'little') + b''.join(o.to_bytes(3, 'little') + n.to_bytes(3, 'little') for o, n in entries)
    assert len(data) <= 0x8000, len(data)
    return data, len(entries)


def main(v10s, v11s, jpp, romp):
    new = walk(open(v11s, encoding='utf-8').read().split('\n'), True)
    olds = {'v10': walk(open(v10s, encoding='utf-8').read().split('\n'), False),
            'jp': walk_jp(open(jpp, 'rb').read())}
    rom = bytearray(open(romp, 'rb').read())
    for name, old in olds.items():
        assert len(old) == len(new), name
        data, n = table(old, new)
        at = TABLES[name]
        rom[at:at + 0x8000] = data + bytes(0x8000 - len(data))
        print('save map %s: %d entries, %d bytes' % (name, n, len(data)))
    open(romp, 'wb').write(rom)


if __name__ == '__main__':
    main(*sys.argv[1:5])
