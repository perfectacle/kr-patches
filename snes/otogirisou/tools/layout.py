"""Simulate dialogue line layout along every script path and report overflowing pages.

Mirrors the engine: x starts at LEFT, a character wraps when x + width reaches RIGHT
(characters in the hang list may pass it), x advances by width + SPACING, {00} and {1C}
start a new line, {25}/{26}/{27} start a new page. Jumps, conditional jumps and choices are followed;
a choice prints each option label (the text at its target up to {1C}, after a leading
{03}) below the current text, then the chosen branch starts a new page.
With --word the asm/wordwrap.asm rule is applied as well.

usage: layout.py rom.sfc table.tbl script.txt [--word] [--name N] [--max-lines 9]
Prints "label<TAB>lines<TAB>page text" for each overflowing page.
"""
import argparse, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from font import groups
from dump import load_table, ENTRIES
from assemble import normalize_text

LEFT, RIGHT, TOP, LINE, SPACING = 12, 242, 16, 23, 2
OPTION_INDENT = 18  # choice text starts after the A/B label and wraps to the same column (measured on screen)
SPACE, COMMA, PERIOD, EXCLAIM = 1247, 1478, 1479, 1482
HANG_LIST = 0x75CE
TOKEN = re.compile(r'#([0-9A-F]{6})\n|\{([0-9A-F]{2})(?::([^}]*))?\}|<(\d{4})>|\n|(.)', re.S)


def widths_of(rom):
    w = {}
    for first, cnt, gw, h, base in groups(rom):
        for c in range(first, first + cnt):
            w[c] = gw
    return w


def hang_list(rom):
    out, o = set(), HANG_LIST
    while rom[o] | rom[o + 1] << 8 != 0xFFFF:
        out.add(rom[o] | rom[o + 1] << 8)
        o += 2
    return out


def parse(text, inv):
    toks, labels, owner = [], {}, []
    cur = None
    for m in TOKEN.finditer(text):
        label, ctl, args, raw, ch = m.groups()
        if label:
            labels[label] = len(toks)
            cur = label
        elif ctl:
            a = [x for x in args.split(',')] if args else []
            toks.append(('C', int(ctl, 16), a, '{%s}' % ctl))
            owner.append(cur)
        elif raw or ch is not None:
            code = int(raw) if raw else inv[ch]
            toks.append(('S', code, None, ch or '?'))
            owner.append(cur)
    return toks, labels, owner


class Layout:
    def __init__(self, toks, labels, owner, W, hang, word, name_w):
        self.t, self.labels, self.owner = toks, labels, owner
        self.W, self.hang, self.word, self.name_w = W, hang, word, name_w
        self.pages = {}  # page start index -> (lines, text)
        self.pending = False
        self.left = LEFT

    def place(self, i, x, y, text):
        """Lay out one character; returns new x, y."""
        c = self.t[i][1]
        w = self.W.get(c, 12)
        if self.pending:
            self.pending = False
            x, y = self.left, y + LINE
            text.append('/')
        if self.word and c in (SPACE, COMMA, PERIOD, EXCLAIM):
            total, n = x + w + SPACING, 0
            for u in self.t[i + 1:i + 41]:
                if u[0] != 'S' or u[1] == SPACE:
                    break
                n += 1
                if u[1] not in self.hang:
                    total += self.W.get(u[1], 12) + SPACING
            if n and total - SPACING >= RIGHT:
                if c == SPACE:
                    x, y = self.left - w - SPACING, y + LINE
                    text.append('/')
                else:
                    self.pending = True
        if x + w >= 256 or (x + w >= RIGHT and c not in self.hang):
            x, y = self.left, y + LINE
            text.append('/')
        text.append(self.t[i][3])
        return x + w + SPACING, y

    def label_text(self, i):
        if self.t[i][0] == 'C' and self.t[i][1] == 0x03:
            i += 1
        start = i
        while i < len(self.t) and not (self.t[i][0] == 'C' and self.t[i][1] in (0x1C, 0x25, 0x26, 0x27)):
            i += 1
        return start, i

    def run(self, starts):
        seen = set()
        work = [(s, LEFT, TOP, s, ()) for s in starts]
        while work:
            i, x, y, page, text = work.pop()
            text = list(text)
            lowest = None
            while i < len(self.t):
                key = (i, x, y)
                if key in seen:
                    break
                seen.add(key)
                kind, code, args, _ = self.t[i]
                if kind == 'S':
                    x, y = self.place(i, x, y, text)
                    lowest = y if lowest is None else max(lowest, y)
                    self.note(page, lowest, text)
                    i += 1
                    continue
                if code in (0x00, 0x1C):
                    x, y = LEFT, y + LINE
                    text.append('/')
                elif code in (0x25, 0x26, 0x27):
                    page, x, y, text, lowest = i + 1, LEFT, TOP, [], None
                elif code == 0x20:
                    x += self.name_w
                    text.append('{이름}')
                elif code == 0x1E and args:
                    x = int(args[0])
                elif code == 0x1F and args:
                    y = int(args[0])
                elif code == 0x03:
                    tgt = self.labels[args[0][1:]]
                    if tgt == i:
                        break
                    i = tgt
                    continue
                elif code in (0x04, 0x05):
                    work.append((self.labels[args[2][1:]], x, y, page, tuple(text)))
                elif code in (0x19, 0x1A):
                    targets = [self.labels[a[1:]] for a in args if a.startswith('@')]
                    if x == LEFT:          # the prompt already ended with a line break
                        y -= LINE
                    self.left = LEFT + OPTION_INDENT
                    for tgt in targets:
                        s, e = self.label_text(tgt)
                        x, y = self.left, y + LINE
                        text.append('/▶')
                        for j in range(s, e):
                            if self.t[j][0] == 'S':
                                x, y = self.place(j, x, y, text)
                                lowest = y if lowest is None else max(lowest, y)
                    self.left = LEFT
                    self.note(page, lowest, text)
                    for tgt in targets:
                        s, e = self.label_text(tgt)
                        nxt = self.labels[self.t[tgt][2][0][1:]] if self.t[tgt][1] == 0x03 and self.t[tgt][0] == 'C' else e + 1
                        work.append((nxt, LEFT, TOP, nxt, ()))
                    break
                i += 1

    def note(self, page, lowest, text):
        if lowest is None:
            return
        n = (lowest - TOP) // LINE + 1
        if n > self.pages.get(page, (0, ''))[0]:
            self.pages[page] = (n, ''.join(text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom'); ap.add_argument('table'); ap.add_argument('script')
    ap.add_argument('--word', action='store_true')
    ap.add_argument('--name', type=int, default=4, help='name length in Hangul syllables')
    ap.add_argument('--max-lines', type=int, default=9)
    a = ap.parse_args()
    rom = open(a.rom, 'rb').read()
    inv = {}
    for code, ch in load_table(a.table).items():
        inv.setdefault(ch, code)
    toks, labels, owner = parse(normalize_text(open(a.script, encoding='utf-8').read()), inv)
    W = widths_of(rom)
    lay = Layout(toks, labels, owner, W, hang_list(rom), a.word, a.name * (W.get(inv['가'], 10) + SPACING))
    lay.run([labels['%06X' % e] for e in ENTRIES['kr']])
    over = sorted((p, n, txt) for p, (n, txt) in lay.pages.items() if n > a.max_lines)
    for p, n, txt in over:
        print('%s\t%d\t%s' % (owner[p] if p < len(owner) else '-', n, txt))
    print('pages %d, over %d lines: %d' % (len(lay.pages), a.max_lines, len(over)), file=sys.stderr)


if __name__ == '__main__':
    main()
