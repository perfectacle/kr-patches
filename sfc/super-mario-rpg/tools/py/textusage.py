"""Which 2-byte dialogue-font codes does the V1.0 text actually use?

Covers every text area known to use the dialogue encoding. Reusing a code that
any of them uses breaks that text (e.g. the menu tutorial's 「봅」).
"""
import dialogue
import dlg_rewrite

MENU_TEXT_PTRS, MENU_TEXT_BASE, MENU_TEXT_COUNT = 0x3EEF00, 0x3EF000, 118
# Regions scanned as 0-terminated strings: enemy attack names, battle messages,
# level-up/timed-hit help, item descriptions, Psychopath thoughts.
TEXT_REGIONS = [(0x3A1740, 0x3A198F), (0x3A2600, 0x3A4100), (0x39961E, 0x39A581), (0x3959F4, 0x396554)]


def used_codes(rom):
    used = set()

    def scan(data):
        for t in dlg_rewrite.tokens(data):
            if len(t) == 2 and t[0] in (0x1D, 0x1E, 0x1F):
                used.add(t[0] << 8 | t[1])

    def zstr(a):
        e = a
        while rom[e]:
            e += 1
        return rom[a:e]

    addrs = dialogue.all_addresses(rom)
    starts = sorted(set(addrs))
    for k, a in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) and starts[k + 1] >> 16 == a >> 16 else a + 2000
        scan(rom[a:end])
    for i in range(256):
        scan(zstr(0x390000 | int.from_bytes(rom[0x396554 + i * 2:0x396556 + i * 2], 'little')))
    for i in range(MENU_TEXT_COUNT):
        scan(zstr(MENU_TEXT_BASE + int.from_bytes(rom[MENU_TEXT_PTRS + i * 2:MENU_TEXT_PTRS + i * 2 + 2], 'little')))
    for a, b in TEXT_REGIONS:
        for s in rom[a:b].split(b'\0'):
            scan(s)
    return used
