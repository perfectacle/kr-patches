-- Start a new game and log how the window code sizes the first dialogues and where lines wrap.
-- log.txt lines:
--   WINSET  $020E (columns) and $0210 (rows) after $81:AD51 picked the window for dialogue $4D
--   chk     at $B7:984A: A = right edge of this glyph, $0208 = its left edge, $020A = width
--   WRAP    at $B7:9851: the glyph did not fit and moved to the next line
-- env: MAXF (default 5400), SHOT_DIR. Use with tools/wintest1.py output.
-- LIBDIR: the toolkit's Lua directory (`krpatch snes lua`)
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")
local n = 0
local out = assert(io.open(L.out .. "/log.txt", "w"))
local function r16(a) return emu.read(a, emu.memType.snesMemory) | (emu.read(a + 1, emu.memType.snesMemory) << 8) end
emu.addMemoryCallback(function()
  local s = emu.getState()
  out:write(string.format("f=%d chk A=%d x0208=%d w020A=%d code=%04x row32=%d id=%04x\n", n, s["cpu.a"] & 0xffff,
    r16(0x7E0208), r16(0x7E020A), r16(0x7E0200), r16(0x7E0032), r16(0x7E004D)))
end, emu.callbackType.exec, 0xB7984A, 0xB7984A)
emu.addMemoryCallback(function()
  out:write(string.format("f=%d WRAP code=%04x x0208=%d\n", n, r16(0x7E0200), r16(0x7E0208)))
end, emu.callbackType.exec, 0xB79851, 0xB79851)
emu.addMemoryCallback(function()
  out:write(string.format("f=%d WINSET 020E=%d 0210=%d id=%04x\n", n, r16(0x7E020E), r16(0x7E0210), r16(0x7E004D)))
end, emu.callbackType.exec, 0x81ADDD, 0x81ADDD)
-- title -> new game -> name entry (Y finishes each name) -> first narration
local seq = {{300, "start"}, {700, "start"}, {1000, "start"}, {1600, "a"}, {1700, "a"}, {1800, "a"},
             {2000, "start"}, {2100, "start"}, {2200, "start"}, {2300, "start"}, {2400, "start"}}
local maxf = tonumber(os.getenv("MAXF") or "5400")
emu.addEventCallback(function()
  n = n + 1
  L.release()
  for _, e in ipairs(seq) do if n >= e[1] and n < e[1] + 4 then local t = {} t[e[2]] = true L.press(t) end end
  if n >= 2520 and n < 8000 and n % 40 < 3 then if n % 200 < 3 then L.press({y = true}) else L.press({a = true}) end end
  if n >= 5140 and n % 4 == 0 then L.shot(string.format("s%05d.png", n)) end
  if n >= maxf then out:close() emu.stop(0) end
end, emu.eventType.endFrame)
