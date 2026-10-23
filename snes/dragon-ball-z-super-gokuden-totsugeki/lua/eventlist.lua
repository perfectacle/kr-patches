-- usage: TARGET=c0 SHOT_DIR=out Mesen --testrunner debug.smc eventlist.lua
-- Debug scenario TARGET: A mash until a dialogue waits for input, then START -> story status
-- -> clear table -> B (event list) -> scroll to the bottom -> B B -> A mash; logs dialogue ids
-- and the WRAM words the hidden 205th event row reads ($0686 for v1.0).
local dir = debug.getinfo(1, "S").source:match("^@(.*/)") or "./"
package.path = dir .. "?.lua;" .. package.path
local L = require("lib")
local m = emu.memType.snesMemory
local n, t0, waiting = 0, nil, 0
local sc = tonumber(os.getenv("TARGET"), 16)
local seq = {{100,"down"},{130,"down"},{160,"down"},{190,"down"},{220,"a"},{300,"down"},{330,"down"},{360,"a"},{480,"a"},{540,"down"},{570,"down"},{600,"down"},{630,"a"}}
local rel = {{0,"start"},{400,"down"},{550,"down"},{700,"a"},{1000,"b"},{5700,"b"},{6300,"b"}}
local out = io.open(os.getenv("SHOT_DIR") .. "/log.txt", "w")
local function press(b) local t = {} t[b] = true L.press(t) end
emu.addEventCallback(function()
  n = n + 1
  L.release()
  for _, s in ipairs(seq) do if n >= s[1] and n < s[1] + 4 then press(s[2]) end end
  if n >= 440 and n < 480 then emu.write(0x7E0263, sc, m) emu.write(0x7E0063, sc, m) end
  if not t0 then
    if n > 900 and waiting > 0 and n % 60 == 30 then
      t0 = n
      local w = {} for i = 0, 15 do w[#w + 1] = string.format("%04x", emu.read16(0x7E0686 + 2 * i, m)) end
      out:write("open " .. n .. " " .. table.concat(w, " ") .. "\n")
    elseif n > 760 and n % 60 < 3 then press("a") end
  else
    local d = n - t0
    for _, s in ipairs(rel) do if d >= s[1] and d < s[1] + 4 then press(s[2]) end end
    if d >= 1300 and d < 5500 and n % 8 < 3 then press("down") end
    if d >= 6800 and n % 60 < 3 then press("a") end
    if d >= 4800 and d % 100 == 0 then L.shot(string.format("q%05d.png", d)) end
  end
  waiting = 0
  if n >= tonumber(os.getenv("MAXF") or "16000") then out:close() emu.stop(0) end
end, emu.eventType.endFrame)
for _, a in ipairs({0x81BE6F, 0x01BE6F}) do
  emu.addMemoryCallback(function() waiting = waiting + 1 end, emu.callbackType.exec, a, a, emu.cpuType.snes, m)
end
local last = -1
emu.addMemoryCallback(function(a)
  local id = ((a & 0x7FFFFF) - 0x0EC9BA) // 2
  if id ~= last then last = id out:write(string.format("%d %03x\n", n, id)) end
end, emu.callbackType.read, 0x0EC9BA, 0x0EC9BA + 0x1800 * 2, emu.cpuType.snes, m)
emu.addMemoryCallback(function(a)
  local id = ((a & 0x7FFFFF) - 0x0EC9BA) // 2
  if id ~= last then last = id out:write(string.format("%d %03x\n", n, id)) end
end, emu.callbackType.read, 0x8EC9BA, 0x8EC9BA + 0x1800 * 2, emu.cpuType.snes, m)
