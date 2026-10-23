-- At frame PF dump PPU shadow $0A00-$0A24, $0A0E/$0A0F and VRAM/BG settings; ppu.txt.
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")
local f = 0
local at = tonumber(os.getenv("PF"))
emu.addEventCallback(function()
  f = f + 1
  if f == at then
    local m = emu.memType.snesMemory
    local t = {}
    for a = 0x0A00, 0x0A24 do t[#t + 1] = string.format("%04X=%02X", a, emu.read(a, m)) end
    local s = emu.getState()
    local keys = {}
    for k, v in pairs(s) do if string.find(k, "ppu.") and (string.find(k, "bg") or string.find(k, "mainScreen") or string.find(k, "subScreen") or string.find(k, "mode")) then keys[#keys + 1] = k .. "=" .. tostring(v) end end
    table.sort(keys)
    L.write("ppu.txt", table.concat(t, " ") .. "\n" .. table.concat(keys, "\n"))
  end
end, emu.eventType.endFrame)
dofile(os.getenv("LIBDIR") .. "/boot.lua")
