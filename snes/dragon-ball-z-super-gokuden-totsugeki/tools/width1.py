"""Pixel width of dialogue codes (VWF table at $B7:97D6)."""


def char_width(w):
    c = w & 0x7FFF
    if c in (0xBE4, 0xBE5, 0xBE6, 0xBE7):
        return {0xBE4: 2, 0xBE5: 4, 0xBE6: 6, 0xBE7: 7}[c]
    if w & 0x8000:
        return 8 if c < 0x500 else 12
    if c >= 0x500:
        return 13
    if c in (0x2C7, 0x2A2):
        return 5
    if c == 0x2C6:
        return 4
    return 9


def line_widths(ws):
    out, cur = [], 0
    for w in ws:
        if w == 0x000A:
            out.append(cur)
            cur = 0
        else:
            cur += char_width(w)
    out.append(cur)
    return out
