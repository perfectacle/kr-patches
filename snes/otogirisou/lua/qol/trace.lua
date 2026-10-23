-- Count executions of PCs listed in TRACE (hex, comma separated) and log $CC at each hit; trace.txt at the end.
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")
local f, hits, log = 0, {}, {}
for a in string.gmatch(os.getenv("TRACE"), "[^,]+") do
  local addr = tonumber(a, 16)
  emu.addMemoryCallback(function()
    hits[a] = (hits[a] or 0) + 1
    if #log < 400 then
      local m = emu.memType.snesMemory
      local st = emu.getState(); log[#log + 1] = string.format("%d %s CC=%04X 1A95=%04X D=%04X 52=%02X%04X d52=%02X%04X", f, a, emu.read16(0x0000CC, m), emu.read16(0x001A95, m), st["cpu.d"], emu.read(0x54, m), emu.read16(0x52, m), emu.read(st["cpu.d"] + 0x54, m), emu.read16(st["cpu.d"] + 0x52, m))
    end
  end, emu.callbackType.exec, addr, addr)
end
local maxf = tonumber(os.getenv("MAXF") or "1500")
emu.addEventCallback(function()
  f = f + 1
  if f == maxf - 1 then
    local t = {}
    for k, v in pairs(hits) do t[#t + 1] = k .. " " .. v end
    L.write("trace.txt", table.concat(t, "\n") .. "\n---\n" .. table.concat(log, "\n"))
  end
end, emu.eventType.endFrame)
dofile(os.getenv("LIBDIR") .. "/boot.lua")
