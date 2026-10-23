"""Data for asm/qol.asm (chapter select, ending list): script positions and menu strings.

usage: qol.py script.txt kr.tbl chapters.tsv endings.tsv rom.sfc

Bank $1B layout (addresses must match asm/qol.asm):
  $1B:8000  chapter ranges: count, then (position 24 bit, chapter id) sorted by position.
            A page belongs to the last range starting at or before it; id 0 = no chapter.
  $1B:8200  chapter starts by id: (position 24 bit, flags), flags bit 0 = restore var 17
  $1B:8300  ending positions: each {1D}, where the script stands when the playthrough ends
  $1B:8400  string pointers (16 bit, bank $1B); strings are script symbols ending in $FFFF
  $1B:F000  scene code by id - 1, 8 bytes: the background code in effect at the chapter
            start when its first page does not set one, ending in $FFFF; entry 31 is empty
  $1B:F100  music by id - 1, 8 bytes: the looping sounds playing at the chapter start,
            ending in $FF; entry 31 is empty
  $1B:F200  looping sounds: 32 byte bitmap of the sound numbers that count as music
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from assemble import load_table, normalize_text, parse
from savemap import walk

RANGES, STARTS, ENDINGS, STRPTR, STRDATA, SCENES, MUSIC, LOOPS = 0xD8000, 0xD8200, 0xD8300, 0xD8400, 0xD8600, 0xDF000, 0xDF100, 0xDF200
BANK = 0x1B

S_MENU, S_NEXT, S_BACK, S_ENDLIST, S_CHLIST, S_ALL = 0, 1, 2, 3, 4, 5
S_CH, S_SEEN, S_UNSEEN, S_ENDHDR = 8, 40, 60, 80
WAITS = set('「『」』.,？！?!')       # the engine waits for a key after these
BG = re.compile(r'\{(2E|2F|30|31|32|33|36|37):[0-9,]+\}')   # codes that set the scene ($1A55)


def scene_at(lines, start, lane_lo):
    """The background code in effect where chapter line `start` begins, or None when the
    page sets its own: the last one before it in the lane, else before the first jump
    that leads into it."""
    k = start + 1 if lines[start - 1].startswith('#') else start
    if BG.search(re.match(r'((?:\{[^}]*\})*)', lines[k - 1]).group(1)):
        return None
    for j in range(k - 1, lane_lo - 1, -1):
        found = BG.findall(lines[j - 1]) and list(BG.finditer(lines[j - 1]))
        if found:
            return found[-1].group(0)
    label = lines[start - 1][1:] if lines[start - 1].startswith('#') else None
    srcs = [i + 1 for i, l in enumerate(lines) if label and '@' + label in l]
    for src in srcs:
        head = lines[src - 1][:lines[src - 1].index('@' + label)]
        for j, text in [(src, head)] + [(j, lines[j - 1]) for j in range(src - 1, 0, -1)]:
            found = list(BG.finditer(text))
            if found:
                return found[-1].group(0)
    if start != lane_lo:                 # the lane's own entry, reached by jumps from elsewhere
        return scene_at(lines, lane_lo, lane_lo) or ''
    raise SystemExit('no scene for line %d' % start)


def quick(code):
    """The scene code with the quickest change: a chapter start can fade in slowly
    ({32:16,1} is 16 frames a step, some 9 seconds of black), which a jump need not copy."""
    m = re.match(r'\{(\w+):(\d+),(\d+)\}$', code or '')
    return '{%s:1,%s}' % (m.group(1), m.group(3)) if m else code


SOUND = re.compile(r'\{(39|3A|3B|3C|3D):([0-9,]+)\}')


def sound_events(text):
    """(id, started) for each sound code in text, in order."""
    out = []
    for code, args in SOUND.findall(text):
        a = [int(x) for x in args.split(',')]
        out.append((a[-1] if code in ('3A', '3C') else a[0], code in ('39', '3A', '3D')))
    return out


def looping(lines):
    """Music and ambient loops: sounds the script stops about as often as it starts them.
    Sound effects (numbers from 85 up) are started often and almost never stopped."""
    starts, stops = {}, {}
    for l in lines:
        for i, on in sound_events(l):
            d = starts if on else stops
            d[i] = d.get(i, 0) + 1
    return {i for i, n in stops.items() if i < 80 and n >= 0.5 * starts.get(i, 0)}


def music_at(lines, start, lane_lo, loops, _depth=0):
    """The looping sounds playing where line `start` begins: for each, the nearest
    start or stop before it in the lane, else before the first jump into the lane."""
    state = {}
    for j in range(start - 1, lane_lo - 1, -1):
        for i, on in reversed(sound_events(lines[j - 1])):
            if i in loops and i not in state:
                state[i] = on
    entry = lines[lane_lo - 1]
    if entry.startswith('#') and _depth < 4:
        label = entry[1:]
        for k, l in enumerate(lines):
            if '@' + label in l and not (lane_lo <= k + 1 < start):
                head = l[:l.index('@' + label)]
                for i, on in reversed(sound_events(head)):
                    if i in loops and i not in state:
                        state[i] = on
                src_lo = k + 1
                while src_lo > 1 and not lines[src_lo - 1].startswith('#'):
                    src_lo -= 1
                for i, on in music_at(lines, k + 1, src_lo, loops, _depth + 1).items():
                    state.setdefault(i, on)
                break
    return state if _depth else sorted(i for i, on in state.items() if on)


def rows(path):
    return [l.rstrip('\n').split('\t') for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#')]


def encode(text, table):
    assert not WAITS & set(text), text
    out = bytearray()
    for kind, v in parse(normalize_text(text), table):
        assert kind == 'S', text
        out += v.to_bytes(2, 'big')
    return bytes(out) + b'\xff\xff'


def main(script, tbl, chapters, endings, romp):
    lines = open(script, encoding='utf-8').read().split('\n')
    pos = walk(lines, True)
    start = lambda n: pos[n - 1][0]
    chs, ends = rows(chapters), rows(endings)

    ranges = {}
    for _, _, _, _, _, lane, _ in chs:
        ranges.setdefault(start(int(lane.split('-')[0])), 0)
    for cid, _, _, line, _, _, _ in chs:
        ranges[start(int(line))] = int(cid)
    rng = sorted(ranges.items())

    table = load_table(tbl)
    strings = {S_MENU: '어디부터 다시 읽을까요', S_NEXT: '다음', S_BACK: '돌아가기',
               S_ENDLIST: '엔딩 목록', S_CHLIST: '장 목록',
               S_ALL: '지금까지 읽은 모든 장'}
    for cid, num, title, *_ in chs:
        strings[S_CH + int(cid)] = '제%s장 %s' % (num, title)
    for k, (_, title) in enumerate(ends):
        strings[S_SEEN + k] = '(%d) %s' % (k + 1, title)
        strings[S_UNSEEN + k] = '(%d) 아직 보지 않음' % (k + 1)
    for n in range(len(ends) + 1):
        strings[S_ENDHDR + n] = '본 엔딩 %d개 (전체 %d개)' % (n, len(ends))

    rom = bytearray(open(romp, 'rb').read())
    rom[RANGES:RANGES + 0x2000] = bytes(0x2000)
    rom[RANGES:RANGES + 2] = len(rng).to_bytes(2, 'little')
    for i, (a, cid) in enumerate(rng):
        rom[RANGES + 2 + 4 * i:RANGES + 6 + 4 * i] = a.to_bytes(3, 'little') + bytes([cid])
    for cid, _, _, line, _, _, flag in chs:
        o = STARTS + 4 * int(cid)
        rom[o:o + 4] = start(int(line)).to_bytes(3, 'little') + bytes([1 if flag == 'y' else 0])
    rom[SCENES:SCENES + 256] = b'\xff' * 256
    rom[MUSIC:MUSIC + 256] = b'\xff' * 256
    loops = looping(lines)
    rom[LOOPS:LOOPS + 32] = bytes(sum(1 << (b & 7) for b in loops if b >> 3 == k) for k in range(32))
    for cid, _, _, line, _, lane, _ in chs:
        ids = music_at(lines, int(line), int(lane.split('-')[0]), loops)
        assert len(ids) < 8, (line, ids)
        o = MUSIC + 8 * (int(cid) - 1)
        rom[o:o + len(ids) + 1] = bytes(ids) + b'\xff'
    for cid, _, _, line, _, lane, _ in chs:
        code = quick(scene_at(lines, int(line), int(lane.split('-')[0])))
        data = b''
        if code:
            for kind, v in parse(code, table):
                data += v.to_bytes(2, 'big')
        data += b'\xff\xff'
        assert len(data) <= 8, code
        o = SCENES + 8 * (int(cid) - 1)
        rom[o:o + 8] = data + bytes(8 - len(data))
    for k, (line, _) in enumerate(ends):
        after = [a for c, a in pos[int(line) - 1][1] if c == '1D']
        assert len(after) == 1 and after[0] & 0x7FFF >= 2, line
        rom[ENDINGS + 4 * k:ENDINGS + 4 * k + 3] = (after[0] - 2).to_bytes(3, 'little')
    at = STRDATA
    for sid, text in sorted(strings.items()):
        data = encode(text, table)
        rom[STRPTR + 2 * sid:STRPTR + 2 * sid + 2] = (0x8000 | (at & 0x7FFF)).to_bytes(2, 'little')
        rom[at:at + len(data)] = data
        at += len(data)
    assert at < SCENES
    open(romp, 'wb').write(rom)
    print('qol: %d chapters, %d ranges, %d endings, strings %d bytes' % (len(chs), len(rng), len(ends), at - STRDATA))


if __name__ == '__main__':
    main(*sys.argv[1:6])
