"""Flowchart data for asm/flow.asm: every choice and ending as a node, numbered breadth
first from the three scenario starts, laid out per chapter.

usage: flow.py script.txt kr.tbl chapters.tsv endings.tsv rom.sfc

Bank $1C layout (addresses must match asm/flow.asm):
  $1C:8000  node count
  $1C:8010  nodes, 16 bytes each, in number order:
            +0 kind (0 choice, 1 ending), +1 chapter id, +2 var (choice) or ending index,
            +4 option count, +5 row in its chapter, +6 children offset (bank $1C),
            +8 child count, +10 jump target (24 bit, start of the page with the choice),
            +13 unused
  $1C:A000  children: node indices (16 bit)
  $1C:C000  scene code by node, 8 bytes: the background code in effect at the jump
            target when its page sets none, ending in $FFFF
  $1C:D000  music by node, 8 bytes: looping sounds playing at the jump target, $FF ends
  $1C:E000  chapters by id - 1: offset of the chapter's rows (16 bit); rows are
            (count, node indices...), the list ending in a zero count
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from assemble import load_table, parse
from savemap import walk
from qol import rows as tsv_rows, scene_at, music_at, looping, quick

NODES, CHILDREN, SCENES, MUSIC, CHAPTERS = 0xE0000, 0xE2000, 0xE4000, 0xE5000, 0xE6000
BANK = 0x1C
CHOICE = re.compile(r'\{(19|1A):([^}]*)\}')
JUMP = re.compile(r'\{(03|04|05):([^}]*)\}')
PAGE_END = re.compile(r'\{(25|26|27(:\d+)?)\}$')


class Script:
    def __init__(self, lines):
        self.L = lines
        self.lab = {l[1:]: i + 1 for i, l in enumerate(lines) if l.startswith('#')}
        self.ends = [i + 1 for i, l in enumerate(lines) if '{1D}' in l]
        self.choices = {}
        for i, l in enumerate(lines):
            m = CHOICE.search(l)
            if m:
                a = m.group(2).split(',')
                self.choices[i + 1] = [self.lab[x[1:]] for x in a if x.startswith('@')]

    def next_lines(self, n):
        """Lines the script can go on to after line n (conditional jumps both ways)."""
        for m in JUMP.finditer(self.L[n - 1]):
            tg = [self.lab[x[1:]] for x in m.group(2).split(',') if x.startswith('@')]
            if m.group(1) == '03':
                return tg
            return tg + [n + 1]
        return [n + 1] if n < len(self.L) else []

    def reach(self, starts):
        """Nodes (choice or ending lines) reached first from the given lines."""
        seen, todo, out = set(), list(starts), []
        while todo:
            x = todo.pop(0)
            if x in seen or not 1 <= x <= len(self.L):
                continue
            seen.add(x)
            if x in self.choices or x in self.ends:
                out.append(x)
                continue
            todo += self.next_lines(x)
        return out

    def children(self, n):
        if n in self.ends:
            # bonus endings: {04:var,1,@X} on the ending line, before its {1D}
            line = self.L[n - 1]
            tg = [self.lab[x[1:]] for m in JUMP.finditer(line[:line.index('{1D}')])
                  for x in m.group(2).split(',') if x.startswith('@')]
            return self.reach(tg)
        out = []
        for t in self.choices[n]:
            for r in self.reach([t]):
                if r not in out:
                    out.append(r)
        return out

    def page_start(self, n):
        """Start line of the page that line n is on."""
        k = n
        while k > 1:
            prev = self.L[k - 2]
            if self.L[k - 1].startswith('#') or prev.startswith('#') or PAGE_END.search(prev):
                break
            k -= 1
        return k


def main(script, tbl, chapters, endings, romp):
    lines = open(script, encoding='utf-8').read().split('\n')
    sc = Script(lines)
    pos = walk(lines, True)
    chs = tsv_rows(chapters)
    ranges = []
    for cid, _, _, line, _, lane, _ in chs:
        lo, hi = map(int, lane.split('-'))
        ranges.append((int(line), hi, int(cid), lo))

    def chapter_of(n):
        best = None
        for s, hi, cid, lo in ranges:
            if s <= n <= hi and (best is None or s > best[0]):
                best = (s, cid, lo)
        assert best, n
        return best

    # numbering: breadth first from the scenario starts
    roots = [sc.reach([s])[0] for s in (2, 1351, 4430)]
    order, seen = [], set()
    queue = list(roots)
    seen.update(roots)
    while queue:
        n = queue.pop(0)
        order.append(n)
        for c in sc.children(n):
            if c not in seen:
                seen.add(c)
                queue.append(c)
    rest = sorted(set(sc.choices) | set(sc.ends) - seen)
    order += [n for n in rest if n not in seen]
    index = {n: i for i, n in enumerate(order)}

    # rows per chapter: breadth first inside the chapter from its nodes without a parent there
    by_ch = {}
    for n in order:
        by_ch.setdefault(chapter_of(n)[1], []).append(n)
    row = {}
    for cid, ns in by_ch.items():
        inside = set(ns)
        parents = {n: [p for p in ns if n in sc.children(p)] for n in ns}
        q = [n for n in ns if not parents[n]] or ns[:1]
        for n in q:
            row[n] = 0
        qi = 0
        while qi < len(q):
            p = q[qi]; qi += 1
            for c in sc.children(p):
                if c in inside and c not in row:
                    row[c] = row[p] + 1
                    q.append(c)
        for n in ns:                     # reachable only through a cycle
            row.setdefault(n, 0)

    rom = bytearray(open(romp, 'rb').read())
    rom[NODES:NODES + 0x8000] = bytes(0x8000)
    rom[NODES:NODES + 2] = len(order).to_bytes(2, 'little')
    table = load_table(tbl)
    ending_index = {e: k for k, (line, _) in enumerate(tsv_rows(endings)) for e in [int(line)]}
    child_at = CHILDREN
    loops = looping(lines)
    for i, n in enumerate(order):
        cid = chapter_of(n)[1]
        kids = [index[c] for c in sc.children(n) if c in index]
        if n in sc.ends:
            kind, var, opts = 1, ending_index[n], 0
        else:
            m = CHOICE.search(lines[n - 1]).group(2).split(',')
            kind, var, opts = 0, int(m[2]), len(sc.choices[n])
        start = sc.page_start(n)
        o = NODES + 0x10 + 16 * i
        rom[o:o + 16] = (bytes([kind, cid]) + var.to_bytes(2, 'little') + bytes([opts, row[n]])
                         + ((child_at - NODES) | 0x8000).to_bytes(2, 'little') + bytes([len(kids), 0])
                         + pos[start - 1][0].to_bytes(3, 'little') + bytes(3))
        for k in kids:
            rom[child_at:child_at + 2] = k.to_bytes(2, 'little')
            child_at += 2
        code = quick(scene_at(lines, start, chapter_of(start)[2]))
        data = b''.join(v.to_bytes(2, 'big') for _, v in parse(code, table)) if code else b''
        data += b'\xff\xff'
        assert len(data) <= 8
        s = SCENES + 8 * i
        rom[s:s + 8] = data + bytes(8 - len(data))
        ids = music_at(lines, start, chapter_of(start)[2], loops)[:7]
        mo = MUSIC + 8 * i
        rom[mo:mo + 8] = bytes(ids) + b'\xff' * (8 - len(ids))
    assert child_at < SCENES and len(order) * 8 <= MUSIC - SCENES
    at = CHAPTERS + 2 * 32
    for cid in range(1, len(chs) + 1):
        rom[CHAPTERS + 2 * (cid - 1):CHAPTERS + 2 * cid] = (0x8000 | (at & 0x7FFF)).to_bytes(2, 'little')
        ns = by_ch.get(cid, [])
        for r in range(max([row[n] for n in ns], default=-1) + 1):
            rr = [index[n] for n in ns if row[n] == r]
            rom[at:at + 2] = len(rr).to_bytes(2, 'little')
            at += 2
            for k in rr:
                rom[at:at + 2] = k.to_bytes(2, 'little')
                at += 2
        rom[at:at + 2] = bytes(2)
        at += 2
    assert at < CHAPTERS + 0x2000
    open(romp, 'wb').write(rom)
    print('flow: %d nodes, %d edges, %d chapters, rows %d bytes' % (
        len(order), (child_at - CHILDREN) // 2, len(chs), at - CHAPTERS))


if __name__ == '__main__':
    main(*sys.argv[1:6])
