-- Force the playthrough counter in every save slot when the scenario selector runs,
-- and log which scenario index ($02:A5EF, A register) was chosen.
-- env: LAP, plus boot.lua env
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")
local lap = tonumber(os.getenv("LAP") or "1")
emu.addMemoryCallback(function()
  for slot = 0, 2 do emu.write(0x24 + slot * 0x5E3, lap, emu.memType.snesSaveRam) end
end, emu.callbackType.exec, 0x02A569, 0x02A569)
emu.addMemoryCallback(function()
  local st = emu.getState()
  L.write("index.txt", tostring(st["cpu.a"] & 0xFF))
end, emu.callbackType.exec, 0x02A5EF, 0x02A5EF)
dofile(os.getenv("LIBDIR") .. "/boot.lua")
