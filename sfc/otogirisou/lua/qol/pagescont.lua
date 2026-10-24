-- pages.lua without the playthrough override: log page starts while boot.lua taps buttons.
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")
local stable = tonumber(os.getenv("STABLE") or "18")
local f, last, since = 0, -1, 0
local seen, log = {}, {}
emu.addEventCallback(function()
  f = f + 1
  local m = emu.memType.snesMemory
  local p = emu.read(0x7E0052, m) | emu.read(0x7E0053, m) << 8 | emu.read(0x7E0054, m) << 16
  if p == last then since = since + 1 else last, since = p, 0 end
  if since == stable and not seen[p] then
    seen[p] = true
    log[#log + 1] = string.format("%d %06X", f, p)
    L.write("pages.txt", table.concat(log, "\n"))
  end
end, emu.eventType.endFrame)
dofile(os.getenv("LIBDIR") .. "/boot.lua")
