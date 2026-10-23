"""Replace English item names written inside V1.0 dialogues with Korean.

V1.0 typed item names in English directly into dialogue text, e.g.
"『MUSHROOM』을 얻었습니다". This rewrites every bracketed English item name
with its Korean name in dialogue encoding, repacks the dialogue groups and
regenerates the pointer table and bank headers (see dialogue.py).

usage: dlg_rewrite.py ROM DLG_TBL_JSON OUT_ASM REPORT
  DLG_TBL_JSON: {"char": "hex code", ...} dialogue encoding incl. reused codes
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dialogue  # noqa: E402
import textfix  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BRACKETS = {0x3B: 0x3C, 0x3D: 0x3E}     # 「」 and 『』
# Dialogue glyphs and tab stops are both 10px. Banner lines such as
# "{09}「HONEYSYRUP」획득!" were centred by picking the tab for the English
# length, so a shorter Korean name needs more tabs to stay centred.
TAB_CELLS = {0x08: 2, 0x09: 3, 0x0A: 4}
LINE_BREAKS = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06}


def line_cells(toks):
    w = 0
    for t in toks:
        if len(t) == 1 and t[0] in TAB_CELLS:
            w += TAB_CELLS[t[0]]
        elif len(t) == 1 and t[0] < 0x20 or len(t) == 2 and t[0] in (0x0B, 0x0D):
            continue
        else:
            w += 1
    return w


def space_honorifics(data, enc, rev, rules, label, report):
    """'마리오님' -> '마리오 님' unless the line would no longer fit."""
    toks = tokens(data)
    char = lambda t: rev.get(t.hex().upper(), '')
    hangul = lambda t: len(char(t)) == 1 and '가' <= char(t) <= '힣'
    names = [(list(n), h) for h, lst in rules.items() if h in ('님', '씨') for n in lst]
    out, line, changed = [], [], False
    for t in toks + [None]:
        if t is not None and not (len(t) == 1 and t[0] in LINE_BREAKS):
            line.append(t)
            continue
        i = 0
        while i < len(line):
            for name, h in names:
                n = len(name)
                seg = line[i:i + n + 1]
                if (len(seg) == n + 1 and [char(x) for x in seg] == name + [h]
                        and (i == 0 or not hangul(line[i - 1]))
                        and line_cells(line) + 1 <= rules['max_cells']):
                    line[i + n:i + n] = [b' ']
                    report.append(f'{label} {"".join(name)}{h} -> {"".join(name)} {h}')
                    changed = True
                    i += n
                    break
            i += 1
        out += line
        line = []
        if t is not None:
            out.append(t)
    return b''.join(out) if changed else data


# {1B flags} is the patch's item-name code: the name is inserted at run time,
# so a banner around it can only be centred then (see KoDlgName).
NAME_BRACKETS, NAME_CENTRE, NAME_PARTICLE = 1, 2, 4


def item_name_codes(data):
    """「{1A}」 -> {1B}: brackets, 을/를 picked for the name, banner centring at line start."""
    toks = tokens(data)
    out, j = [], 0
    while j < len(toks):
        if toks[j:j + 3] == [b'\x3b', b'\x1a', b'\x3c']:
            flags = NAME_BRACKETS
            k = len(out)
            while k and (out[k - 1] == b' ' or len(out[k - 1]) == 1 and out[k - 1][0] in TAB_CELLS):
                k -= 1
            if k < len(out) and (k == 0 or len(out[k - 1]) == 1 and out[k - 1][0] in LINE_BREAKS):
                flags |= NAME_CENTRE
                del out[k:]
            j += 3
            if j < len(toks) and toks[j] in (b'\x8f', b'\x76'):          # 을 / 를
                flags |= NAME_PARTICLE
                j += 1
            elif toks[j:j + 4] == [b'(', b'\x8f', b')', b'\x76']:      # (을)를
                flags |= NAME_PARTICLE
                j += 4
            out.append(bytes([0x1B, flags]))
            continue
        out.append(toks[j])
        j += 1
    return b''.join(out)


BANNER_CELLS = 22      # same as !dn_line in main.asm


def centre_banners(data):
    """Lines that start with a tab and a bracket (item-get banners) -> centred."""
    toks = tokens(data)
    out, line = [], []
    for t in toks + [None]:
        if t is not None and not (len(t) == 1 and t[0] in LINE_BREAKS):
            line.append(t)
            continue
        indent = lambda t: t == b' ' or len(t) == 1 and t[0] in TAB_CELLS or len(t) == 2 and t[0] == 0x0B
        i = 0
        while i < len(line) and indent(line[i]):
            i += 1
        if i and line[0] != b' ' and i < len(line) and len(line[i]) == 1 and line[i][0] in BRACKETS:
            pad = (BANNER_CELLS - line_cells(line[i:])) // 2
            if pad >= min(TAB_CELLS.values()):
                line = tab_tokens(pad) + line[i:]
        out += line
        line = []
        if t is not None:
            out.append(t)
    return b''.join(out)


def drop_dead_tail(data):
    """Bytes after a dialogue's end code are never shown: leftovers of the text V1.0 overwrote."""
    toks = tokens(data)
    return b''.join(toks[:toks.index(b'\0') + 1]) if b'\0' in toks else data


def repair_ends(data, ids, encode):
    """V1.0 put an end code where these dialogues go on (checked against the JP text)."""
    if 0x498 in ids and data[:2] == b'\0\x05':          # was empty; JP: frog coin received
        data = b'\x0b\x06' + encode('개구리 코인 획득!') + b'\0' + data[data.index(b'\0', 1) + 1:]
    if 0x8B4 in ids and data[:1] == b'\0':               # was empty; JP: Peach 'shh'
        data = data[1:]
    if 0xE85 in ids:                                      # cut after the first line; JP has two
        toks = tokens(data)
        if b'\0' in toks and b'\x01' not in toks[:toks.index(b'\0')]:
            toks[toks.index(b'\0')] = b'\x01'
            data = b''.join(toks)
    return data


def tab_tokens(cells):
    """One tab code plus spaces: each extra tab code delays the text by ~30 frames."""
    code = max((c for c in TAB_CELLS if TAB_CELLS[c] <= cells), key=TAB_CELLS.get)
    return [bytes([code])] + [b' '] * (cells - TAB_CELLS[code])
# Where each bank's dialogue data must end (next used data).
BANK_LIMIT = {0x22: 0x22B400, 0x23: 0x23FF00, 0x24: 0x242800}
# Original end of the data in each bank (start of the zero run after it).
BANK_END = {0x22: 0x22ADC0, 0x23: 0x23E591, 0x24: 0x24272C}
# Spellings used in V1.0 dialogue that differ from the 10-char item table.
ALIASES = {
    'CASTLEKEY': 0x84, 'ZOOMSHOES': 0x4A, 'FLOWERTAB': 0x73, 'TEMPLEKEY': 0x7C,
    'ATACKSKARF': 0x51, 'CRICKET PIE': 0x82, 'CRICKET JAM': 0xA6, 'SHINY STONE': 0x8A,
    'SUPER SUIT': 0x45,
    'HAMMER': 0x05,     # 0x23 (Lucky Hammer) has the same name in V1.0
}


def tokens(data):
    """Split dialogue bytes into tokens (2-byte chars and codes with a parameter)."""
    out, j = [], 0
    while j < len(data):
        c = data[j]
        n = 2 if c in (0x1D, 0x1E, 0x1F, 0x0B, 0x0D, 0x1B, 0x1C) and j + 1 < len(data) else 1
        out.append(data[j:j + n])
        j += n
    return out


def decode(data, tbl_rev):
    s = ''
    for t in tokens(data):
        key = t.hex().upper()
        s += tbl_rev.get(key, '{%s}' % key)
    return s


def repack_table(rom, enc, rev, fixes, where, tab, count, bank, alt, log, transform, ptr_base=None):
    """Re-encode a pointer table of 0-terminated strings in one bank with fixes applied.
    Pointers are 16-bit addresses in `bank`, or offsets from `ptr_base` if given."""
    base = bank << 16
    if ptr_base is None:
        ptr_base = base
    ptrs = [ptr_base + int.from_bytes(rom[tab + i * 2:tab + i * 2 + 2], 'little') for i in range(count)]
    by_id = {}
    for f in fixes:
        if f['where'] == where:
            by_id.setdefault(int(f['id'], 16), []).append(f)
    lo = min(ptrs)
    end_of = {}
    for p in set(ptrs):
        e = p
        while rom[e] != 0:
            e += 1
        end_of[p] = e + 1
    hi = max(end_of.values())
    free_after = hi
    while rom[free_after] == 0 and free_after < hi + 0x1000:
        free_after += 1
    blob, new_off, first_id = bytearray(), {}, {}
    for i, p in enumerate(ptrs):
        first_id.setdefault(p, i)
    for p in sorted(set(ptrs)):
        data = bytes(rom[p:end_of[p]])
        i = first_id[p]
        if i in by_id:
            l = []
            data = textfix.apply(data[:-1], by_id[i], enc, rev, l) + b'\0'
            log += [f'{where} {i:02X} {x}' for x in l]
        data = transform(data[:-1], f'{where} {i:02X}') + b'\0'
        new_off[p] = len(blob)
        blob += data
    start = lo if lo + len(blob) <= free_after else alt[0]
    if start == alt[0] and len(blob) > alt[1]:
        sys.exit(f'{where}: {len(blob)} bytes do not fit')
    table = b''.join(((start + new_off[p] - ptr_base) & 0xFFFF).to_bytes(2, 'little') for p in ptrs)
    name = f'text_{where}'
    (ROOT / f'build/{name}.bin').write_bytes(bytes(blob))
    (ROOT / f'build/{name}_ptr.bin').write_bytes(table)
    out = [f'org ${0xC00000 | start:06X}', f'    incbin "{name}.bin"', f'assert pc() <= ${0xC00000 | (free_after if start == lo else alt[0] + alt[1]):06X}',
           f'org ${0xC00000 | tab:06X}', f'    incbin "{name}_ptr.bin"']
    if start != lo:
        # old text area is no longer referenced
        out[0:0] = []
    log.append(f'{where}: {hi - lo} -> {len(blob)} bytes at {start:06X}')
    return out


def patch_in_place(rom, enc, rev, fixes, where, tab, count, ptr_base, spare, transform, log):
    """Rewrite changed strings at their own address. The area also holds data the
    pointers do not cover, so nothing moves; a string that grows uses the zero
    bytes after it (up to the next string), else goes to `spare` (unused bytes
    after the table's text) and its pointers are updated."""
    out = []
    by_id = {}
    for f in fixes:
        if f['where'] == where:
            by_id.setdefault(int(f['id'], 16), []).append(f)
    offs = [int.from_bytes(rom[tab + i * 2:tab + i * 2 + 2], 'little') for i in range(count)]
    table = list(offs)
    free = spare[0]
    for off in sorted(set(offs)):
        p = ptr_base + off
        e = p
        while rom[e]:
            e += 1
        old = bytes(rom[p:e])
        new = old
        ids = [i for i, o in enumerate(offs) if o == off]
        for i in ids:
            if i in by_id:
                l = []
                new = textfix.apply(new, by_id[i], enc, rev, l)
                log += [f'{where} {i:02X} {x}' for x in l]
        new = transform(new, f'{where} {ids[0]:02X}')
        if new == old:
            continue
        data = new + b'\0'
        room = e + 1
        starts = {ptr_base + o for o in offs}
        while room < len(rom) and rom[room] == 0 and room not in starts:
            room += 1
        if len(data) <= room - p:
            dest = p
        else:
            dest = free
            free += len(data)
            if free > spare[1]:
                sys.exit(f'{where}: spare area full')
            for i in ids:
                table[i] = dest - ptr_base
        out += [f'org ${0xC00000 | dest:06X}', '    db ' + ','.join(f'${b:02X}' for b in data)]
        log.append(f'{where} {ids[0]:02X}: {len(old)} -> {len(new)} bytes at {dest:06X}')
    if table != offs:
        out += [f'org ${0xC00000 | tab:06X}', '    dw ' + ','.join(f'${o:04X}' for o in table)]
    return out


def main():
    rom = bytearray(Path(sys.argv[1]).read_bytes())
    enc = {ch: bytes.fromhex(h) for ch, h in json.loads(Path(sys.argv[2]).read_text()).items()}
    tbl_rev = {v.hex().upper(): k for k, v in enc.items()}
    items_en = json.loads((ROOT / 'data/items_en.json').read_text())
    items_ko = {int(x['id_hex'], 16): x['ko'].replace(' ', '') for x in json.loads((ROOT / 'data/items_ko.json').read_text())}
    for h, ko in json.loads((ROOT / 'data/name_overrides.json').read_text())['item'].items():
        items_ko[int(h, 16)] = ko
    names = {x['en_patch']: x['id'] for x in items_en if x['en_patch'] and '{' not in x['en_patch']}
    names.update(ALIASES)

    extra = json.loads((ROOT / 'data/dialogue_names.json').read_text())
    bare = sorted(extra['bare'].items(), key=lambda kv: -len(kv[0]))
    encode = lambda text: b''.join(enc[c] for c in text)

    def korean(id_):
        ko = items_ko.get(id_)
        return b''.join(enc[c] for c in ko) if ko else None

    report = []

    def replace_english(data, label):
        """English item names (bracketed or listed bare words) -> Korean."""
        toks = tokens(data)
        res, j = [], 0
        tab_at, shrink = None, 0      # tab of a banner line, cells saved on it

        def close_line():
            nonlocal tab_at, shrink
            if tab_at is not None and shrink > 0:
                cells = TAB_CELLS[res[tab_at][0]] + (shrink + 1) // 2
                res[tab_at] = b''.join(tab_tokens(cells))
                report.append(f'{label} recentred: +{(shrink + 1) // 2} tab')
            tab_at, shrink = None, 0

        while j < len(toks):
            if len(toks[j]) == 1 and toks[j][0] in LINE_BREAKS:
                close_line()
                res.append(toks[j])
                j += 1
                continue
            line_start = not res or (len(res[-1]) == 1 and res[-1][0] in LINE_BREAKS)
            if line_start and len(toks[j]) == 1 and toks[j][0] in TAB_CELLS and j + 1 < len(toks) and len(toks[j + 1]) == 1 and toks[j + 1][0] in BRACKETS:
                tab_at = len(res)
            opener = toks[j][0] if len(toks[j]) == 1 and toks[j][0] in BRACKETS else None
            if opener:
                closer = bytes([BRACKETS[opener]])
                close = next((m for m in range(j + 1, min(j + 16, len(toks))) if toks[m] == closer), None)
                if close:
                    word = b''.join(toks[j + 1:close])
                    txt = word.decode('latin-1') if all(0x20 <= b < 0x60 for b in word) else None
                    ko_text = extra['bracketed'].get(txt) or (items_ko.get(names[txt]) if txt in names else None)
                    if ko_text:
                        res.append(bytes([opener]) + encode(ko_text) + closer)
                        report.append(f'{label} {txt} -> {ko_text}')
                        if tab_at is not None:
                            shrink += len(txt) - len(ko_text)
                        j = close + 1
                        continue
            hit = None
            if len(toks[j]) == 1 and 0x41 <= toks[j][0] <= 0x5A and not (j and len(toks[j - 1]) == 1 and 0x41 <= toks[j - 1][0] <= 0x5A):
                for en_word, ko_text in bare:
                    w = en_word.encode()
                    seg = toks[j:j + len(w)]
                    after = toks[j + len(w)] if j + len(w) < len(toks) else b''
                    if all(len(t) == 1 for t in seg) and b''.join(seg) == w and not (len(after) == 1 and 0x41 <= after[0] <= 0x5A):
                        hit = (en_word, ko_text, len(w))
                        break
            if hit:
                res.append(encode(hit[1]))
                report.append(f'{label} {hit[0]} -> {hit[1]} (bare)')
                j += hit[2]
                continue
            res.append(toks[j])
            j += 1
        close_line()
        return b''.join(res)

    fixes = json.loads((ROOT / 'data/dialogue_fixes.json').read_text())
    fix_log = []
    honorifics = json.loads((ROOT / 'data/honorifics.json').read_text())
    table_text = lambda data, label: space_honorifics(replace_english(data, label), enc, tbl_rev, honorifics, label, report)

    addrs = dialogue.all_addresses(rom)
    dlg_fixes = {}
    for f in fixes:
        if f['where'] == 'dialogue':
            dlg_fixes.setdefault(addrs[int(f['id'], 16)], []).append(f)
    groups = {}
    for i, a in enumerate(addrs):
        groups.setdefault(i >> 9, set()).add(a)

    new_addr = {}
    bank_out = {}
    for g in sorted(groups):
        bank, base = dialogue.group_base(rom, g)
        starts = sorted(groups[g])
        # group ends at the next group's base in this bank, or the bank's data end
        later = [dialogue.group_base(rom, h) for h in groups if h > g]
        later = [(b << 16) | x for b, x in later if b == bank]
        gend = min(later) if later else BANK_END[bank]
        out = bytearray()
        for k, a in enumerate(starts):
            end = starts[k + 1] if k + 1 < len(starts) else gend
            ids = {i for i, x in enumerate(addrs) if x == a}
            data = repair_ends(bytes(rom[a:end]), ids, encode)
            data = space_honorifics(replace_english(data, f'{a:06X}'), enc, tbl_rev, honorifics, f'{a:06X}', report)
            # Fixes see the Korean names: several correct the particle after one.
            if a in dlg_fixes:
                log = []
                data = textfix.apply(data, dlg_fixes.pop(a), enc, tbl_rev, log)
                fix_log += [f'{a:06X} {x}' for x in log]
            # Pointers of a group can equal the next group's start (empty tail),
            # so the same address may belong to two groups.
            new_addr[(g, a)] = (bank, len(out))
            out += drop_dead_tail(centre_banners(item_name_codes(data)))
        bank_out.setdefault(bank, []).append((g, base, out))

    # Repack: groups stay in their banks and order; each bank starts with its header.
    ptr = bytearray(rom[dialogue.PTR_TABLE:dialogue.PTR_TABLE + dialogue.COUNT * 2])
    asm = ['; generated by tools/py/dlg_rewrite.py']
    for bank, glist in sorted(bank_out.items()):
        hdr_size = int.from_bytes(rom[(bank << 16):(bank << 16) + 2], 'little')
        header = bytearray(rom[(bank << 16):(bank << 16) + hdr_size])
        pos = glist[0][1]
        blob = bytearray()
        for idx, (g, base, data) in enumerate(glist):
            if idx:
                header[2 * idx:2 * idx + 2] = pos.to_bytes(2, 'little')
            else:
                assert pos == base
            for i in range(g * 512, min((g + 1) * 512, dialogue.COUNT)):
                b, off = new_addr[(g, addrs[i])]
                ptr[i * 2:i * 2 + 2] = off.to_bytes(2, 'little')
            blob += data
            pos += len(data)
        end = (bank << 16) + glist[0][1] + len(blob)
        if end > BANK_LIMIT[bank]:
            sys.exit(f'bank {bank:02X} overflows: ends at {end:06X}, limit {BANK_LIMIT[bank]:06X}')
        old_end = BANK_END[bank]
        pad = max(0, old_end - end)
        (ROOT / f'build/dlg_bank{bank:02X}.bin').write_bytes(bytes(header) + bytes(rom[(bank << 16) + hdr_size:(bank << 16) + glist[0][1]]) + blob + bytes(pad))
        asm += [f'org ${0xC0 | bank:02X}0000', f'    incbin "dlg_bank{bank:02X}.bin"']
        report.append(f'bank {bank:02X}: end {old_end:06X} -> {end:06X} ({end - old_end:+d} bytes)')
    asm += repack_table(rom, enc, tbl_rev, fixes, 'battle_dialogue', 0x396554, 256, 0x39, (0x39AF2A, 4310), fix_log, table_text)
    asm += repack_table(rom, enc, tbl_rev, fixes, 'item_description', 0x3A2F20, 0xB1, 0x3A, (0x3A50FC, 3844), fix_log, replace_english)
    asm += patch_in_place(rom, enc, tbl_rev, fixes, 'menu_text', 0x3EEF00, 118, 0x3EF000, (0x3EF61C, 0x3EF700), table_text, fix_log)
    asm += patch_in_place(rom, enc, tbl_rev, fixes, 'battle_message', 0x3A26F1, 46, 0x3A0000, (0, 0), lambda data, label: data, fix_log)
    # No known spare bytes in bank 39: Psychopath fixes must not grow.
    asm += patch_in_place(rom, enc, tbl_rev, fixes, 'psychopath', 0x399411, 256, 0x390000, (0, 0), lambda data, label: data, fix_log)
    (ROOT / 'build/text_fixes_log.txt').write_text('\n'.join(fix_log) + '\n', encoding='utf-8')
    report.append(f"text fixes: {sum(1 for x in fix_log if ' -> ' in x and 'particle' not in x)} applied, "
                  f"{sum(1 for x in fix_log if 'skipped' in x or 'not found' in x)} skipped")
    (ROOT / 'build/dlg_ptr.bin').write_bytes(ptr)
    asm += [f'org ${0xC00000 | dialogue.PTR_TABLE:06X}', '    incbin "dlg_ptr.bin"']
    Path(sys.argv[3]).write_text('\n'.join(asm) + '\n')
    Path(sys.argv[4]).write_text('\n'.join(report) + '\n', encoding='utf-8')
    print(f'{sum(1 for r in report if "->" in r and "bank" not in r)} names replaced')


if __name__ == '__main__':
    main()
