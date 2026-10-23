-- Start debug ADVENTURE scenario TARGET (hex) from the hidden debug menu, then press A every
-- PERIOD frames (one frame each). Logs every dialogue id shown to SHOT_DIR/ids.txt
-- ("frame id"). SHOTS=1 also saves a screenshot every 3 frames for tools/pages1.py.
-- env: TARGET, MAXF (default 8000), PERIOD (default 90), SHOTS, SHOT_DIR
-- The ROM must have the debug menu enabled (file 0x61: 80 04 -> EA EA).
-- LIBDIR: the toolkit's Lua directory (`krpatch snes lua`)
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")
local m = emu.memType.snesMemory
local n = 0
local tgt = tonumber(os.getenv("TARGET") or "0", 16)
local maxf = tonumber(os.getenv("MAXF") or "8000")
local period = tonumber(os.getenv("PERIOD") or "90")
local shots = os.getenv("SHOTS")
-- ADVENTURE -> SCENARIO SELECT, confirm with A (B would cancel), then SCENARIO START
local seq = {{100,"down"},{130,"down"},{160,"down"},{190,"down"},{220,"a"},{300,"down"},{330,"down"},
             {360,"a"},{480,"a"},{540,"down"},{570,"down"},{600,"down"},{630,"a"}}
emu.addEventCallback(function()
  n = n + 1
  L.release()
  for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 4 then local t = {} t[s[2]] = true L.press(t) end end
  if n >= 440 and n < 480 then emu.write(0x7E0263, tgt, m) emu.write(0x7E0063, tgt, m) end
  -- a single-frame press; holding A also skips the page that just finished printing
  if n > 760 and n % period == 0 then L.press({a = true}) end
  if shots and n > 700 and n % 3 == 0 then L.shot(string.format("q%05d.png", n)) end
  if n == maxf - 1 then L.shot("end.png") end
  if n >= maxf then emu.stop(0) end
end, emu.eventType.endFrame)
-- every line reads its window info at $8E:C9BA + id*2 (through either bank mirror)
local idlog = io.open(os.getenv("SHOT_DIR") .. "/ids.txt", "w")
local last = -1
local function seen(a)
  local id = ((a & 0x7FFFFF) - 0x0EC9BA) // 2
  if id ~= last then last = id idlog:write(string.format("%d %03x\n", n, id)) idlog:flush() end
end
for _, base in ipairs({0x8EC9BA, 0x0EC9BA}) do
  emu.addMemoryCallback(seen, emu.callbackType.read, base, base + 0x1800 * 2, emu.cpuType.snes, m)
end
