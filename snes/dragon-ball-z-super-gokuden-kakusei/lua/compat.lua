-- Mesen 2 side of compat/run_all.sh: plays the same script.txt as compat/lr.py.
-- env SCRIPT (script.txt), SHOT_DIR. Writes f<frame>.png, end.png, wram.log.
package.path = (os.getenv("LUA_DIR") or "/path/to/gokuden2-kr-v1.3-tools/lua") .. "/?.lua;" .. package.path
local L = require("lib")
local presses, shots, pokes, last = {}, {}, {}, 0
for line in io.lines(os.getenv("SCRIPT")) do
  local f, a, b, c = line:match("^(%d+)%s+(%S+)%s*(%S*)%s*(%S*)")
  if f then
    f = tonumber(f)
    if a == "shot" then shots[f] = true
    elseif a == "end" then last = f
    elseif a == "poke" then pokes[f] = {tonumber(b, 16), tonumber(c, 16)}
    else
      local btn = {}
      for k in a:gmatch("[^+]+") do btn[k] = true end
      presses[#presses + 1] = {f, f + tonumber(b), btn}
    end
  end
end
local n, prev = 0, nil
local log = io.open(L.out .. "/wram.log", "w")
emu.addEventCallback(function()
  n = n + 1
  L.release()
  for _, p in ipairs(presses) do
    if n >= p[1] and n < p[2] then L.press(p[3]) end
  end
  if pokes[n] then emu.write16(0x7E0000 + pokes[n][1], pokes[n][2], emu.memType.snesMemory) end
  local v = emu.read16(0x7E029C, emu.memType.snesMemory)
  if v ~= prev then log:write(string.format("%d %03x\n", n, v)) log:flush() prev = v end
  if shots[n] then L.shot(string.format("f%05d.png", n)) end
  if n >= last then L.shot("end.png") log:close() emu.stop(0) end
end, emu.eventType.endFrame)
