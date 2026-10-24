"""Compare the glyph codes logged while name banners were drawn (glyphs.txt from
test/banner_ids.lua) with the expected names: data/*_ko.json with name_overrides.json,
or the V1.0 English entry for ids without a Korean name.

usage: check_banner.py ROOT glyphs.txt item|skill IDS      (IDS: hex, comma separated, as given to banner_ids.lua)
"""
import json, re, sys
from pathlib import Path
work, log, kind, ids = Path(sys.argv[1]), sys.argv[2], sys.argv[3], [int(x, 16) for x in sys.argv[4].split(',')]
rev = {}
for line in (work / 'data/tbl/korTBL.utf8.tbl').read_text(encoding='utf-8').splitlines():
    m = re.match(r'([0-9A-Fa-f]{2,4})=(.)$', line)
    if not m: continue
    h = int(m.group(1), 16)
    code = h if h < 0x100 else (((h >> 8) - 0x1C) << 8) | (h & 0xFF)
    rev.setdefault(code, m.group(2))
for line in (work / 'build/dlg_added.txt').read_text(encoding='utf-8').splitlines():
    h, ch = line.split('=')
    h = int(h, 16); rev[(((h >> 8) - 0x1C) << 8) | (h & 0xFF)] = ch
for p in (work / 'build').glob('*.asm'):
    for m in re.finditer(r'dialogue font extension ([0-9A-F]{2}) = (.)', p.read_text(encoding='utf-8')):
        rev[0x400 | int(m.group(1), 16)] = m.group(2)
names = {int(e['id_hex'], 16): e['ko'].replace(' ', '') for e in json.load(open(work / f'data/{kind}s_ko.json'))}
for h, n in json.load(open(work / 'data/name_overrides.json')).get(kind, {}).items():
    names[int(h, 16)] = n
rom = open(work / 'rom/smrpg_kr_v1.sfc', 'rb').read()   # V1.0: English item/special tables
table = 0x3A41FC if kind == 'item' else 0x3A137F
for i in ids:
    if not names.get(i):   # no Korean name: the V1.0 English entry, icon byte dropped
        names[i] = rom[table + i * 15 + 1:table + i * 15 + 11].decode('ascii', 'replace').rstrip(' ')
banners, cur = [], None
for line in open(log):
    if line.startswith('B'):
        cur = []; banners.append(cur)
    elif line.startswith('G') and cur is not None:
        cur.append(int(line.split()[1], 16))
ok = bad = 0
for i, codes in zip(ids, banners):
    got = ''.join(rev.get(c, f'<{c:03X}>') for c in codes)
    exp = names.get(i)
    if got == exp: ok += 1
    else:
        bad += 1; print(f'{i:02X} expected {exp!r} got {got!r}')
print(f'{kind}: {ok} match, {bad} differ, banners logged {len(banners)} for {len(ids)} ids')
