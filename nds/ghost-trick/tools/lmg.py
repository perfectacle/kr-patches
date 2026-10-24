"""1LMG 스크립트(stNN/*_Expand.xml.lz 를 푼 것)의 대사 읽기·다시 넣기.

구조: 0x34 바이트 헤더, 코드 구역(헤더 +0x08 크기), 이름 문자열 구역, 레이블 표.
코드 구역은 u16 열이다. 대사는 `FF2D 장면 번호 … FFFE` 블록이고, 앞뒤로 이어 붙은
대사 묶음(run)을 이룬다. 묶음 밖(바이트코드, `FFFD` 이벤트 블록)은 건드리지 않는다.

다시 넣기는 묶음 단위다. 묶음 안 대사를 순서대로 이어 쓰고 남는 칸은 0 으로 채운다.
묶음 크기는 그대로라 파일 크기와 묶음 밖 위치가 바뀌지 않는다. 대사가 옮겨 가면
그 시작을 가리키는 포인터(아래 PTR_TAGS 태그 뒤 u32, 파일 오프셋)를 고친다.
PTR_TAGS 는 v1.1 이 일본판에서 고친 포인터 위치에서 모은 것이다.
"""
import struct

HEADER = 0x34
MSG, END = 0xFF2D, 0xFFFE
PTR_TAGS = {0x37, 0x51, 0x4C, 0x40, 0x5D, 0xDB, 0x5C, 0x45, 0x3C, 0x00, 0x01, 0x02, 0xFFFD, 0xFFF4, 0x228}


def code_words(d):
    n = struct.unpack_from("<I", d, 8)[0] // 2
    return list(struct.unpack_from(f"<{n}H", d, HEADER))


def _is_msg(w, i):
    return w[i] == MSG and i + 2 < len(w) and w[i + 1] < 0x100 and w[i + 2] < 0x400


def _msg_end(w, i):
    j = i
    while j < len(w) and w[j] != END:
        j += 1
    if j == len(w):
        raise ValueError(f"message at word {i} has no FFFE")
    return j + 1


def runs(d):
    """[(start word, end word, [(msg start, msg end), ...])] — 일본판처럼 빈칸 없는 파일용."""
    w = code_words(d)
    out = []
    i = 0
    while i < len(w):
        if _is_msg(w, i):
            msgs = []
            j = i
            while j < len(w) and _is_msg(w, j):
                e = _msg_end(w, j)
                msgs.append((j, e))
                j = e
            out.append((i, j, msgs))
            i = j
        else:
            i += 1
    return out


def messages_in(w, start, count):
    """묶음 시작부터 대사 `count` 개를 차례로 읽는다(뒤의 남는 칸은 무시)."""
    return [tuple(w[s:e]) for s, e in locate(w, start, count)]


def pointer_map(wj, wk, starts, spans):
    """일본판 대사 시작(단어 위치) -> 한국어판 시작. 일본판에서 그 대사를 가리키는 포인터 자리의
    한국어판 값을 읽는다(묶음 밖 자리는 두 판이 같은 위치다)."""
    targets = {HEADER + 2 * s: s for s in starts}
    out = {}
    for i in pointer_sites(wj, set(targets), spans):
        v = wk[i] | wk[i + 1] << 16
        if v >= HEADER and (v - HEADER) % 2 == 0:
            out.setdefault(targets[wj[i] | wj[i + 1] << 16], (v - HEADER) // 2)
    return out


def locate(w, start, count, ids=None, end=None, hint=None, orig=None):
    """묶음 [start, end) 안 대사 `count` 개의 (시작, 끝) 단어 위치.

    v1.1 은 대부분 일본판 순서로 이어 썼지만 그렇지 않은 곳(번역 안 된 대사를 제자리에 둠,
    번호를 바꿈, 남는 칸에 옛 대사 사본)도 있다. 그래서 대사마다 다음 순서로 찾는다:
    포인터로 찾은 위치(`hint`) → 앞 대사 뒤 블록(번호가 같거나, 이미 찾은 대사의 번호거나,
    어느 대사의 번호도 아닐 때) → 같은 (창, 번호) → 같은 번호 → 앞 대사 뒤 첫 FF2D.
    한 번 쓴 블록은 다시 쓰지 않는다. 대사의 끝은 찾은 블록 가운데 다음 시작 직전까지다(v1.1 에는
    FFFE 가 중간에 있거나 FFFE 뒤에 낱값이 붙은 대사가 있다). 마지막 대사는 첫 FFFE 까지."""
    end = end or len(w)
    ids = ids or [None] * count
    hint = hint or [None] * count
    found = [i for i in range(start, end - 2) if _is_msg(w, i)]
    used = {h for h in hint if h is not None and h in found}
    starts = []
    prev = start - 1
    located = {}
    for m, h in zip(ids, hint):
        if h is not None and h in found:
            hit = h
        else:
            hit = None
            # the next block, when its number is this one's or belongs to a message already found
            # (v1.1 sometimes labelled a translation with a wrong, already used number)
            seq = next((i for i in found if i not in used and i > prev), None)
            if m is not None and seq is not None:
                sid = (w[seq + 1], w[seq + 2])
                # a leftover copy of the Japanese message with that number (`orig`: number -> first words)
                copy = orig is not None and sid in located and tuple(w[seq + 3:seq + 13]) == orig.get(sid)
                if not copy and (w[seq + 2] == m[1] or sid in located or sid not in ids):
                    hit = seq
            if hit is None and m is not None:
                hit = next((i for i in found if i not in used and (w[i + 1], w[i + 2]) == m), None)
                if hit is None:
                    hit = next((i for i in found if i not in used and w[i + 2] == m[1]
                                and (w[i + 1], w[i + 2]) not in ids), None)
            if hit is None:
                hit = next((i for i in found if i not in used and i > prev), None)
            if hit is None:
                raise ValueError(f"message {m} not found in words {start}-{end}")
            used.add(hit)
        starts.append(hit)
        prev = hit
        if m is not None:
            located[m] = hit
            located.setdefault((w[hit + 1], w[hit + 2]), hit)
    order = sorted(set(starts))
    nxt = {s: (order[k + 1] if k + 1 < len(order) else _msg_end(w, s)) for k, s in enumerate(order)}
    return [(s, nxt[s]) for s in starts]


def pointer_sites(w, targets, skip=()):
    """값이 `targets`(파일 오프셋) 중 하나인 포인터의 단어 위치. `skip` 범위(묶음) 안은 제외."""
    sites = []
    for i in range(1, len(w) - 1):
        if w[i - 1] not in PTR_TAGS:
            continue
        if any(a <= i < b for a, b in skip):
            continue
        v = w[i] | w[i + 1] << 16
        if v in targets:
            sites.append(i)
    return sites


def repack(d, layout, new_msgs):
    """`layout`: runs() 결과(이 파일 기준 묶음 위치와 지금 대사 위치), `new_msgs`: 묶음마다 대사 u16 튜플 목록.
    묶음 크기를 넘으면 ValueError."""
    w = code_words(d)
    old_to_new = {}
    spans = [(a, b) for a, b, _ in layout]
    for (a, b, msgs), new in zip(layout, new_msgs):
        if len(new) != len(msgs):
            raise ValueError(f"run at word {a}: {len(msgs)} messages, got {len(new)}")
        total = sum(len(m) for m in new)
        if total > b - a:
            raise ValueError(f"run at word {a}: {total} words do not fit in {b - a}")
        p = a
        for (s, _), m in zip(msgs, new):
            old_to_new[HEADER + 2 * s] = HEADER + 2 * p
            w[p:p + len(m)] = m
            p += len(m)
        w[p:b] = [0] * (b - p)
    moved = {o: n for o, n in old_to_new.items() if o != n}
    for i in pointer_sites(code_words(d), set(moved), spans):
        v = moved[w[i] | w[i + 1] << 16]
        w[i], w[i + 1] = v & 0xFFFF, v >> 16
    out = bytearray(d)
    struct.pack_into(f"<{len(w)}H", out, HEADER, *w)
    # label table: u32 count, then (name offset, file offset) pairs
    lab = HEADER + sum(struct.unpack_from("<II", d, 8))
    for k in range(struct.unpack_from("<I", d, lab)[0]):
        at = lab + 4 + k * 8 + 4
        v = struct.unpack_from("<I", d, at)[0]
        if v in moved:
            struct.pack_into("<I", out, at, moved[v])
    return bytes(out)
