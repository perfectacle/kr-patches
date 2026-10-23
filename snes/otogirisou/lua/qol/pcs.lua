-- From frame PCFROM to PCTO log PC at each NMI-free point (end of frame) and some RAM; pcs.txt at the end.
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")
local f, log = 0, {}
local a, b = tonumber(os.getenv("PCFROM")), tonumber(os.getenv("PCTO"))
emu.addEventCallback(function()
  f = f + 1
  if f >= a and f <= b then
    local s = emu.getState()
    local m = emu.memType.snesMemory
    log[#log + 1] = string.format("%d pc=%02X%04X 0A25=%04X CC=%04X 1A95=%04X 1BAA=%04X 2140=%02X%02X", f, s["cpu.k"], s["cpu.pc"],
      emu.read16(0x0A25, m), emu.read16(0xCC, m), emu.read16(0x1A95, m), emu.read16(0x1BAA, m), emu.read(0x10A0, m), emu.read(0x10A1, m)) .. string.format(" hold=%04X B8=%02X 52=%06X", emu.read16(0x7E1FF0, m), emu.read(0xB8, m), emu.read16(0x52, m) | (emu.read(0x54, m) << 16))
  end
  if f == b then L.write("pcs.txt", table.concat(log, "\n")) end
end, emu.eventType.endFrame)
dofile(os.getenv("LIBDIR") .. "/boot.lua")
