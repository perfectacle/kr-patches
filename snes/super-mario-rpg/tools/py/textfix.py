"""Context-checked name replacements inside encoded Korean text.

Text is decoded to the same display form as dump_text.py so that "found" and
"context" strings written by reviewers can be located; replacements are then
applied to the token list and re-encoded.
"""
import dump_text
import dlg_rewrite

# particle that follows a word, keyed by (with final consonant, without)
PARTICLES = [('이', '가'), ('을', '를'), ('은', '는'), ('과', '와'), ('아', '야'), ('이야', '야'), ('으로', '로')]


def has_batchim(word):
    for ch in reversed(word):
        if '가' <= ch <= '힣':
            return (ord(ch) - 0xAC00) % 28 != 0
        if ch.isdigit():
            return ch in '013678'
    return False


def display(tokens, rev):
    """Display string plus [start, end) character span of every token."""
    s, spans = '', []
    for t in tokens:
        k = t.hex().upper()
        piece = dump_text.READABLE.get(k) or (rev[k] if len(rev.get(k, '')) == 1 else '{%s}' % k)
        spans.append((len(s), len(s) + len(piece)))
        s += piece
    return s, spans


def apply(data, fixes, enc, rev, log):
    """Apply fixes [{'found','replace','context'}] to encoded bytes; returns new bytes."""
    tokens = dlg_rewrite.tokens(data)
    text, spans = display(tokens, rev)
    todo = []
    by_found = {}
    for f in fixes:
        by_found.setdefault(f['found'], []).append(f)
    for found, group in by_found.items():
        hits = []
        k = text.find(found)
        while k >= 0:
            hits.append(k)
            k = text.find(found, k + len(found))
        if not hits:
            log.append(f'not found: {found!r}')
            continue
        if len(hits) <= len(group):
            chosen = hits
        else:
            chosen = []
            for f in group:
                ctx = f.get('context', '')
                c = text.find(ctx) if ctx else -1
                pick = next((h for h in hits if c >= 0 and c <= h < c + len(ctx)), None)
                if pick is None:
                    log.append(f'ambiguous, skipped: {found!r} context {ctx!r}')
                elif pick not in chosen:
                    chosen.append(pick)
        for h in chosen:
            todo.append((h, h + len(found), group[0]['replace'], found))
    for s, e, rep, found in sorted(todo, reverse=True):
        first = next(i for i, (a, b) in enumerate(spans) if a <= s < b)
        last = next(i for i, (a, b) in enumerate(spans) if a < e <= b)
        if spans[first][0] != s or spans[last][1] != e:
            log.append(f'not token aligned, skipped: {found!r}')
            continue
        new = [enc[ch] for ch in rep]
        # fix the particle right after the name
        nxt = last + 1
        if has_batchim(found.strip('<>')) != has_batchim(rep.strip('<>')) and nxt < len(tokens):
            after = text[spans[nxt][0]:spans[nxt][0] + 2]
            for withb, without in PARTICLES:
                old = withb if has_batchim(found.strip('<>')) else without
                newp = withb if has_batchim(rep.strip('<>')) else without
                if len(old) == 1 and after[:1] == old and (len(after) < 2 or not '가' <= after[1] <= '힣'):
                    tokens[nxt] = enc[newp]
                    log.append(f'particle {found}{old} -> {rep}{newp}')
                    break
        tokens[first:last + 1] = new
        spans[first:last + 1] = [(s, s)] * len(new)
        log.append(f'{found} -> {rep}')
    return b''.join(tokens)
