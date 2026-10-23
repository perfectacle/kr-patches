-- Play SEQ from STATE; the first room change goes to room ROOM instead
-- ($00:3030 is the current room id; the game's write is replaced while the
-- door transition writes it). Saves OUT (relative to SHOT_DIR) at the end and
-- screenshots every EVERY frames. POKE_AT="frame:addr=val;addr=val" writes
-- once at that frame (CPU bus addresses).
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")
L.loadState(os.getenv("STATE"))
local M = emu.memType.snesMemory
local room = tonumber(os.getenv("ROOM") or "", 16)
local every = tonumber(os.getenv("EVERY") or "0")
local steps = {}
for tok in string.gmatch(os.getenv("SEQ"), "[^,]+") do local bt, f = tok:match("([%w+]+):(%d+)"); steps[#steps + 1] = {bt, tonumber(f)} end
local n, i, left, lastHit = 0, 1, nil, nil
if room then
  emu.addMemoryCallback(function(addr, val)
    if lastHit and n > lastHit + 30 then return val end   -- only the first transition
    lastHit = n
    if addr == 0x3030 then return room & 0xFF else return (room >> 8) & 0xFF end
  end, emu.callbackType.write, 0x3030, 0x3031, emu.cpuType.snes, M)
end
local pokeAt, pokes = nil, {}
if os.getenv("POKE_AT") then
  local f, rest = os.getenv("POKE_AT"):match("(%d+):(.*)")
  pokeAt = tonumber(f)
  for a, v in string.gmatch(rest, "(%x+)=(%x+)") do pokes[#pokes + 1] = {tonumber(a, 16), tonumber(v, 16)} end
end
local done = false
emu.addEventCallback(function()
  n = n + 1
  if every > 0 and n % every == 0 then L.shot(string.format("w%05d.png", n)) end
  if n == pokeAt then for _, p in ipairs(pokes) do emu.write(p[1], p[2], M) end end
  if n < 3 then return end
  L.release()
  if i <= #steps then
    local s = steps[i]; if left == nil then left = s[2] end
    if s[1] ~= "wait" then local t = {}; for x in s[1]:gmatch("[^+]+") do t[x] = true end; L.press(t) end
    left = left - 1; if left <= 0 then i = i + 1; left = nil end
  elseif not done then
    done = true
    L.shot("end.png")
    if os.getenv("OUT") then L.saveState(os.getenv("OUT")) end
  else
    emu.stop(0)
  end
end, emu.eventType.endFrame)
