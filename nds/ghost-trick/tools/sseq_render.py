"""SDAT 의 시퀀스(SSEQ) 하나를 DS 사운드 엔진 방식으로 합성한다(BGM 루프 파일용).

    sseq_render.py SDAT SEQ_INDEX OUT.wav [--rate 48000]

출력: 곡 처음부터 loopEnd + 꼬리 0.5초. 루프 회차는 앞 회차의 꼬리를 이어받는데, 도입부 꼬리가 사라진 뒤로는
1회차와 2회차가 표본 단위로 같다. 그 첫 지점을 loopStart, loopStart + 루프 길이를 loopEnd 로 두면 이음매가 정확하다.
이 값은 같은 이름의 .json 에 적는다.

지원 범위(이 게임 BGM 에 쓰인 것): 음표, 쉼표, 프로그램, 트랙 열기·점프·호출·복귀, 팬(C0), 트랙 음량(C1),
모노/폴리(C7, 폴리만), 모듈레이션 깊이(CA=0 만), 템포(E1). 악기: PCM(1), 드럼 세트(0x10), 키 분할(0x11).
엔벨로프·음량표는 NitroSDK 의 Cnv_Attack·Cnv_Fall·Cnv_Sust 와 같은 방식, 갱신 주기는 ARM7 64×2728 클록.
"""
import argparse
import json
import math
import struct
import wave

import numpy as np

ARM7_CLOCK = 33513982
FRAME_RATE = ARM7_CLOCK / (64 * 2728)   # 시퀀서·엔벨로프 갱신(약 191.96Hz)
AMP_MIN = -92544                         # -723 << 7
ATTACK_LUT = [0x00, 0x01, 0x05, 0x0E, 0x1A, 0x26, 0x33, 0x3F, 0x49, 0x54, 0x5C, 0x64, 0x6D, 0x74, 0x7B, 0x7F, 0x84,
              0x89, 0x8F]
IMA_INDEX = [-1, -1, -1, -1, 2, 4, 6, 8]
IMA_STEP = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88,
            97, 107, 118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658, 724,
            796, 876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026,
            4428, 4871, 5358, 5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500,
            20350, 22385, 24623, 27086, 29794, 32767]


def cnv_attack(a):
    return ATTACK_LUT[0x7F - a] if a >= 0x6D else 0xFF - a


def cnv_fall(f):
    if f == 0x7F:
        return 0xFFFF
    if f == 0x7E:
        return 0x3C00
    if f < 0x32:
        return f * 2 + 1
    return 0x1E00 // (0x7E - f)


def cnv_sust(v):
    """음량 0–127 → 감쇠값(0 이 최대, -723 이 무음 근처). 진폭은 v² 에 비례한다."""
    if v <= 0:
        return -32768
    return max(-723, round(400 * math.log10(v / 127)))


def gain(total):
    return 0.0 if total <= -723 else 10 ** (total / 400)


class Sdat:
    def __init__(self, data):
        self.d = data
        self.info = struct.unpack_from("<I", data, 0x18)[0]
        self.fat = struct.unpack_from("<I", data, 0x20)[0]

    def record(self, kind, i):
        r = self.info + struct.unpack_from("<I", self.d, self.info + 8 + 4 * kind)[0]
        return self.info + struct.unpack_from("<I", self.d, r + 4 + 4 * i)[0]

    def file(self, fid):
        st, sz = struct.unpack_from("<II", self.d, self.fat + 12 + fid * 16)
        return self.d[st:st + sz]


def decode_swav(w):
    kind, loop, rate, _, loop_start, loop_len = struct.unpack_from("<BBHHHI", w, 0)
    body = w[12:12 + (loop_start + loop_len) * 4]
    if kind == 0:
        pcm = np.frombuffer(body, np.int8).astype(np.float32) / 128
        ls = loop_start * 4
    elif kind == 1:
        pcm = np.frombuffer(body[:len(body) // 2 * 2], "<i2").astype(np.float32) / 32768
        ls = loop_start * 2
    else:
        pred, idx = struct.unpack_from("<hH", body, 0)
        out = []
        for b in body[4:]:
            for nib in (b & 15, b >> 4):
                step = IMA_STEP[idx]
                diff = step >> 3
                if nib & 1:
                    diff += step >> 2
                if nib & 2:
                    diff += step >> 1
                if nib & 4:
                    diff += step
                pred = max(-32768, min(32767, pred - diff if nib & 8 else pred + diff))
                idx = max(0, min(88, idx + IMA_INDEX[nib & 7]))
                out.append(pred)
        pcm = np.array(out, np.float32) / 32768
        ls = (loop_start * 4 - 4) * 2   # 머리말 한 워드를 뺀 니블 수
    return {"pcm": pcm, "rate": rate, "loop": bool(loop), "loop_start": ls}


class Bank:
    def __init__(self, sdat, bank_index):
        e = sdat.record(2, bank_index)
        fid = struct.unpack_from("<H", sdat.d, e)[0]
        self.arcs = list(struct.unpack_from("<4H", sdat.d, e + 4))
        self.b = sdat.file(fid)
        self.sdat = sdat
        self.waves = {}

    def wave(self, arc, swav):
        key = (arc, swav)
        if key not in self.waves:
            a = self.sdat.file(struct.unpack_from("<H", self.sdat.d, self.sdat.record(3, self.arcs[arc]))[0])
            off = struct.unpack_from("<I", a, 0x3C + 4 * swav)[0]
            self.waves[key] = decode_swav(a[off:])
        return self.waves[key]

    def note_def(self, prog, key):
        """(swav, swar, 기준 음, A, D, S, R, 팬) 또는 None."""
        t, off = self.b[0x3C + prog * 4], struct.unpack_from("<H", self.b, 0x3C + prog * 4 + 1)[0]
        if t == 1:
            return struct.unpack_from("<HHBBBBBB", self.b, off)
        if t == 0x10:
            lo, hi = self.b[off], self.b[off + 1]
            if not lo <= key <= hi:
                return None
            return struct.unpack_from("<HHBBBBBB", self.b, off + 2 + (key - lo) * 12 + 2)
        if t == 0x11:
            tops = self.b[off:off + 8]
            for i, top in enumerate(tops):
                if top and key <= top:
                    return struct.unpack_from("<HHBBBBBB", self.b, off + 8 + i * 12 + 2)
            return None
        return None


class Voice:
    def __init__(self, wav, base, a, d, s, r, pan, key, vel, track, dur):
        self.w, self.key, self.base = wav, key, base
        self.attack, self.decay, self.sust, self.rel = cnv_attack(a), cnv_fall(d), cnv_sust(s) << 7, cnv_fall(r)
        self.inst_pan, self.vel, self.track, self.left = pan, vel, track, dur
        self.amp, self.state, self.pos = AMP_MIN, "attack", 0.0

    def update(self):
        if self.left is not None:
            if self.left <= 0 and self.state != "release":
                self.state = "release"
        if self.state == "attack":
            self.amp = (self.attack * self.amp) >> 8
            if self.amp == 0:
                self.state = "decay"
        elif self.state == "decay":
            self.amp -= self.decay
            if self.amp <= self.sust:
                self.amp, self.state = self.sust, "sustain"
        elif self.state == "release":
            self.amp -= self.rel
        return self.amp > AMP_MIN


class Track:
    def __init__(self, seq, pos):
        self.s, self.pc, self.wait, self.calls = seq, pos, 0, []
        self.prog, self.vol, self.pan = 0, 127, 64
        self.done = False


class Player:
    def __init__(self, sdat, seq_index):
        e = sdat.record(0, seq_index)
        fid, _, bank, self.seq_vol = struct.unpack_from("<HHHB", sdat.d, e)
        s = sdat.file(fid)
        self.base = struct.unpack_from("<I", s, 0x18)[0]
        self.s = s
        self.bank = Bank(sdat, bank)
        self.tracks = [Track(s, self.base)]
        self.voices = []
        self.tempo, self.acc = 120, 0
        self.ticks = 0

    def varlen(self, t):
        v = 0
        while True:
            b = self.s[t.pc]
            t.pc += 1
            v = (v << 7) | (b & 0x7F)
            if not b & 0x80:
                return v

    def u24(self, p):
        return self.s[p] | self.s[p + 1] << 8 | self.s[p + 2] << 16

    def step_track(self, t):
        s = self.s
        while t.wait == 0 and not t.done:
            c = s[t.pc]
            t.pc += 1
            if c < 0x80:
                vel = s[t.pc]
                t.pc += 1
                dur = self.varlen(t)
                nd = self.bank.note_def(t.prog, c)
                if nd:
                    swav, swar, base, a, d, su, r, pan = nd
                    self.voices.append(Voice(self.bank.wave(swar, swav), base, a, d, su, r, pan, c, vel, t, dur or None))
            elif c == 0x80:
                t.wait = self.varlen(t)
            elif c == 0x81:
                t.prog = self.varlen(t)
            elif c == 0x93:
                n, off = s[t.pc], self.u24(t.pc + 1)
                t.pc += 4
                self.tracks.append(Track(s, self.base + off))
            elif c == 0x94:
                t.pc = self.base + self.u24(t.pc)
            elif c == 0x95:
                t.calls.append(t.pc + 3)
                t.pc = self.base + self.u24(t.pc)
            elif c == 0xFD:
                t.pc = t.calls.pop()
            elif c == 0xFE:
                t.pc += 2
            elif c == 0xC0:
                t.pan = s[t.pc]
                t.pc += 1
            elif c == 0xC1:
                t.vol = s[t.pc]
                t.pc += 1
            elif c in (0xC7, 0xCA):
                if s[t.pc]:
                    raise SystemExit(f"unsupported {c:#x} {s[t.pc]}")
                t.pc += 1
            elif 0xC0 <= c <= 0xD7:
                raise SystemExit(f"unsupported command {c:#x}")
            elif c == 0xE1:
                self.tempo = struct.unpack_from("<H", s, t.pc)[0]
                t.pc += 2
            elif c == 0xFF:
                t.done = True
            else:
                raise SystemExit(f"unsupported command {c:#x}")

    def frame(self):
        """시퀀서·엔벨로프 한 번 갱신."""
        self.acc += self.tempo
        while self.acc >= 240:
            self.acc -= 240
            for t in list(self.tracks):
                self.step_track(t)
            for t in self.tracks:
                if t.wait:
                    t.wait -= 1
            for v in self.voices:
                if v.left is not None:
                    v.left -= 1
            self.ticks += 1
        self.voices = [v for v in self.voices if v.update()]


def events(pl, ticks):
    """[(시작 틱, 길이 틱 또는 None, 악기 정의, 음, 세기, 트랙 음량, 트랙 팬)] — 시퀀서를 틱 단위로 돌린다."""
    out = []

    class Capture(list):
        def append(self, v):
            out.append((pl.ticks, v.left, v, v.track.vol, v.track.pan))
    pl.voices = Capture()
    for _ in range(ticks):
        for t in list(pl.tracks):
            pl.step_track(t)
        for t in pl.tracks:
            if t.wait:
                t.wait -= 1
        pl.ticks += 1
    return out


def render_voice(v, vol, pan, seq_vol, frames_len, rate, release_at, length):
    """음 하나를 시작 시점 기준으로 그린다. 엔벨로프는 시작부터 frames_len 표본마다 갱신(하드웨어처럼 그 사이는 고정)."""
    w = v.w
    pcm, L = w["pcm"], len(w["pcm"])
    step = w["rate"] * 2 ** ((v.key - v.base) / 12) / rate
    base_gain = cnv_sust(v.vel) + cnv_sust(vol) + cnv_sust(seq_vol)
    p = max(0, min(127, v.inst_pan + pan - 64))
    gl, gr = (128 - p) / 128, p / 128
    gains = []
    edge = 0.0
    while True:
        if release_at is not None and edge >= release_at and v.state != "release":
            v.state = "release"
        alive = v.update()
        gains.append(gain((v.amp >> 7) + base_gain) if alive else 0.0)
        edge += frames_len
        if not alive or edge >= length:
            break
    n = min(length, int(math.ceil(edge)))
    idx = step * np.arange(n)
    if w["loop"] and L > w["loop_start"]:
        ls = w["loop_start"]
        idx = np.where(idx >= L, ls + np.mod(idx - ls, L - ls), idx)
        i0 = idx.astype(np.int64)
        i1 = np.where(i0 + 1 >= L, ls, i0 + 1)
        valid = np.ones(n, bool)
    else:
        valid = idx < L - 1
        i0 = np.minimum(idx.astype(np.int64), L - 1)
        i1 = np.minimum(i0 + 1, L - 1)
    frac = (idx - np.floor(idx)).astype(np.float32)
    smp = (pcm[i0] * (1 - frac) + pcm[i1] * frac) * valid
    g = np.repeat(np.array(gains, np.float32), np.diff(np.floor(np.arange(len(gains) + 1) * frames_len).astype(np.int64)))[:n]
    g = np.pad(g, (0, n - len(g)))
    return np.stack([smp * g * gl, smp * g * gr], 1)


def render(sdat_bytes, seq_index, rate, intro_ticks, loop_ticks):
    """도입부 + 루프 3회 분량을 그리고 (표본 배열, 루프 1·2·3회차 시작 표본)을 돌려준다.
    틱 간격은 루프 한 바퀴가 정수 표본이 되도록 백만분의 1 이하로 맞춘다. 그래서 회차마다 표본 단위로 같다."""
    pl = Player(Sdat(sdat_bytes), seq_index)
    total = intro_ticks + 3 * loop_ticks
    evs = events(pl, total)
    spt = 240 / (pl.tempo * FRAME_RATE) * rate          # 템포가 고정인 곡만 다룬다
    loop_len = round(loop_ticks * spt)
    spt = loop_len / loop_ticks
    at = lambda t: round(t * spt)
    frames_len = rate / FRAME_RATE
    out = np.zeros((at(total) + int(2 * rate), 2), np.float32)
    for t0, dur, v, vol, pan in evs:
        s0 = at(t0)
        release = None if dur is None else at(t0 + dur) - s0
        seg = render_voice(v, vol, pan, pl.seq_vol, frames_len, rate, release, len(out) - s0)
        out[s0:s0 + len(seg)] += seg
    return out, at(intro_ticks), at(intro_ticks + loop_ticks), at(intro_ticks + 2 * loop_ticks), at(total)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sdat")
    ap.add_argument("seq", type=int)
    ap.add_argument("out")
    ap.add_argument("--rate", type=int, default=48000)
    ap.add_argument("--intro", type=int, required=True, help="도입부 틱")
    ap.add_argument("--loop", type=int, required=True, help="루프 틱")
    a = ap.parse_args()
    y, l1, l2, l3, _ = render(open(a.sdat, "rb").read(), a.seq, a.rate, a.intro, a.loop)
    # 루프 1회차는 도입부 꼬리가 사라진 뒤부터 2회차와 표본 단위로 같다. 그 뒤를 루프 시작으로 잡아 파일을 줄인다.
    loop_len = l2 - l1
    differ = np.nonzero(np.abs(y[l1:l2] - y[l2:l3]).max(1))[0]
    l2 = l1 + (int(differ[-1]) + 1 if len(differ) else 0)
    l3 = l2 + loop_len
    peak = float(np.abs(y).max())
    y = y / peak * 10 ** (-1 / 20)
    end = l3 + int(0.5 * a.rate)
    pcm = (np.clip(y[:end], -1, 1) * 32767).astype("<i2")
    with wave.open(a.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(a.rate)
        w.writeframes(pcm.tobytes())
    meta = {"loopStart": round(l2 / a.rate, 6), "loopEnd": round(l3 / a.rate, 6), "duration": round(end / a.rate, 6),
            "loopStartSample": l2, "loopEndSample": l3, "sampleRate": a.rate}
    json.dump(meta, open(a.out.rsplit(".", 1)[0] + ".json", "w"), indent=1)
    print(meta)


if __name__ == "__main__":
    main()
