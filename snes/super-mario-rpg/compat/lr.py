"""Minimal headless libretro frontend for compatibility runs.

usage: lr.py core.dylib rom.sfc outdir script.txt [save.srm]

script.txt lines: `frame button[+button] len` presses, `frame shot` screenshots, `frame dump`,
`frame end`. Writes PNGs and wram.log (frame, script pointer $7E0052-54 on change) to outdir.
"""
import ctypes as C
import os
import sys

from PIL import Image

core = C.CDLL(sys.argv[1])
rom_path, out = sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)

BTN = {"b": 0, "y": 1, "select": 2, "start": 3, "up": 4, "down": 5, "left": 6, "right": 7,
       "a": 8, "x": 9, "l": 10, "r": 11}
presses, shots, dumps, end = [], set(), set(), 0
for line in open(sys.argv[4]):
    p = line.split()
    if not p:
        continue
    f = int(p[0])
    if p[1] == "shot":
        shots.add(f)
    elif p[1] == "dump":          # WRAM and SRAM to wram_<frame>.bin / sram_<frame>.bin
        dumps.add(f)
    elif p[1] == "end":
        end = f
    elif p[1] == "tap":           # `frame tap button period until`: 4-frame presses every period frames
        for t in range(f, int(p[4]), int(p[3])):
            presses.append((t, t + 4, {BTN[p[2]]}))
    else:
        presses.append((f, f + int(p[2]), {BTN[b] for b in p[1].split("+")}))

frame = [0]
pixfmt = [0]
last = [None]

ENV_CB = C.CFUNCTYPE(C.c_bool, C.c_uint, C.c_void_p)
VID_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_uint, C.c_uint, C.c_size_t)
AUD_CB = C.CFUNCTYPE(None, C.c_int16, C.c_int16)
AUDB_CB = C.CFUNCTYPE(C.c_size_t, C.c_void_p, C.c_size_t)
POLL_CB = C.CFUNCTYPE(None)
IN_CB = C.CFUNCTYPE(C.c_int16, C.c_uint, C.c_uint, C.c_uint, C.c_uint)
LOG_CB = C.CFUNCTYPE(None, C.c_int, C.c_char_p)

sysdir = C.c_char_p(out.encode())
# LRVARS="key=value,key=value" overrides core options
VARS = {k: C.c_char_p(v.encode()) for k, v in (kv.split('=', 1) for kv in os.getenv('LRVARS', '').split(',') if kv)}


class LogIface(C.Structure):
    _fields_ = [("log", C.c_void_p)]


def _log(level, fmt):
    if os.getenv('LRLOG'):
        sys.stderr.write(fmt.decode(errors='replace'))


log_fn = LOG_CB(_log)
log_iface = LogIface(C.cast(log_fn, C.c_void_p))


@ENV_CB
def env(cmd, data):
    if os.getenv('LRLOG'):
        sys.stderr.write(f'ENV {cmd}\n'); sys.stderr.flush()
    cmd &= 0xFFFF
    if cmd in (9, 31):            # GET_SYSTEM_DIRECTORY, GET_SAVE_DIRECTORY
        C.cast(data, C.POINTER(C.c_char_p))[0] = sysdir
        return True
    if cmd == 10:                 # SET_PIXEL_FORMAT
        pixfmt[0] = C.cast(data, C.POINTER(C.c_int))[0]
        return True
    if cmd == 27:                 # GET_LOG_INTERFACE
        C.cast(data, C.POINTER(LogIface))[0] = log_iface
        return True
    if cmd == 15:                 # GET_VARIABLE
        key = C.cast(data, C.POINTER(C.c_char_p))[0].decode()
        if key in VARS:
            C.cast(data, C.POINTER(C.c_char_p))[1] = VARS[key]
            return True
        return False
    if cmd == 3:                  # GET_CAN_DUPE
        C.cast(data, C.POINTER(C.c_bool))[0] = True
        return True
    return False


@VID_CB
def video(data, w, h, pitch):
    if data:
        last[0] = (C.string_at(data, pitch * h), w, h, pitch)


@AUD_CB
def audio(l, r):
    pass


@AUDB_CB
def audio_batch(data, n):
    return n


@POLL_CB
def poll():
    pass


@IN_CB
def inp(port, device, index, id_):
    if port != 0 or device != 1:
        return 0
    return int(any(a <= frame[0] < b and id_ in s for a, b, s in presses))


def save_png(path):
    data, w, h, pitch = last[0]
    if pixfmt[0] == 2:            # RGB565
        im = Image.frombuffer("RGB", (w, h), data, "raw", "BGR;16", pitch, 1)
    elif pixfmt[0] == 1:          # XRGB8888
        im = Image.frombuffer("RGBX", (w, h), data, "raw", "BGRX", pitch, 1).convert("RGB")
    else:                         # 0RGB1555
        im = Image.frombuffer("RGB", (w, h), data, "raw", "BGR;15", pitch, 1)
    im.save(path)


class GameInfo(C.Structure):
    _fields_ = [("path", C.c_char_p), ("data", C.c_void_p), ("size", C.c_size_t), ("meta", C.c_char_p)]


if len(sys.argv) > 5:
    # cores without a SAVE_RAM pointer (bsnes) read <save dir>/<rom name>.srm instead
    base = os.path.splitext(os.path.basename(rom_path))[0]
    open(os.path.join(out, base + ".srm"), "wb").write(open(sys.argv[5], "rb").read())
core.retro_set_environment(env)
core.retro_set_video_refresh(video)
core.retro_set_audio_sample(audio)
core.retro_set_audio_sample_batch(audio_batch)
core.retro_set_input_poll(poll)
core.retro_set_input_state(inp)
core.retro_init()
rom = open(rom_path, "rb").read()
buf = C.create_string_buffer(rom, len(rom))
gi = GameInfo(os.path.abspath(rom_path).encode(), C.cast(buf, C.c_void_p), len(rom), None)
if not core.retro_load_game(C.byref(gi)):
    print("LOAD FAILED")
    sys.exit(3)

core.retro_get_memory_data.restype = C.c_void_p
core.retro_get_memory_size.restype = C.c_size_t
srm = open(sys.argv[5], "rb").read() if len(sys.argv) > 5 else None


def inject():
    p, n = core.retro_get_memory_data(0), core.retro_get_memory_size(0)
    if p:
        C.memmove(p, srm, min(n, len(srm)))
    if os.getenv('LRLOG'):
        sys.stderr.write(f"SRAM ptr={p} size={n}\n")


if srm:
    inject()
wram = core.retro_get_memory_data(2)

log = open(os.path.join(out, "wram.log"), "w")
prev = None
while frame[0] < end:
    core.retro_run()
    frame[0] += 1
    if srm and frame[0] == 1:     # some cores clear SRAM during their first frame
        inject()
    if wram:
        sc = C.string_at(wram + 0x52, 3)
        v = sc[0] | sc[1] << 8 | sc[2] << 16
        if v != prev:
            log.write(f"{frame[0]} {v:06X}\n")
            prev = v
    if frame[0] in dumps:
        for i, name in ((2, "wram"), (0, "sram")):
            ptr, n = core.retro_get_memory_data(i), core.retro_get_memory_size(i)
            if ptr:
                open(os.path.join(out, f"{name}_{frame[0]}.bin"), "wb").write(C.string_at(ptr, n))
    if frame[0] in shots and last[0]:
        save_png(os.path.join(out, f"f{frame[0]:05d}.png"))
log.close()
if last[0]:
    save_png(os.path.join(out, "end.png"))
print("OK", frame[0])
