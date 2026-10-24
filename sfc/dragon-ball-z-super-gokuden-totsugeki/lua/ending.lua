-- Load a savestate taken during the ending (ST), optionally write the player name (NAME = 5 hex codes,
-- comma separated) to $7E:0B01, run MAXF frames (default 11500) to the password page and save
-- the screen, $7E:0A00 (password) and $7E:0B01 (names).
-- LIBDIR: the toolkit's Lua directory (`krpatch sfc lua`)
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")
local n = 0
local name = {}
for h in string.gmatch(os.getenv("NAME") or "", "(%x+)") do name[#name + 1] = tonumber(h, 16) end
L.loadState(os.getenv("ST"))
local maxf = tonumber(os.getenv("MAXF") or "11500")
emu.addEventCallback(function()
  n = n + 1
  if n >= 2 and n <= 10 then
    for k, c in ipairs(name) do
      emu.write(0x7E0B01 + (k - 1) * 2, c & 0xFF, emu.memType.snesMemory)
      emu.write(0x7E0B02 + (k - 1) * 2, c >> 8, emu.memType.snesMemory)
    end
  end
  if n == maxf then
    L.shot("password.png")
    local t = {}
    for i = 0, 0xBF do t[#t + 1] = string.char(emu.read(0x7E0A00 + i, emu.memType.snesMemory)) end
    L.write("pw.bin", table.concat(t))
    local nm = {}
    for i = 0, 9 do nm[#nm + 1] = string.char(emu.read(0x7E0B01 + i, emu.memType.snesMemory)) end
    L.write("name.bin", table.concat(nm))
    emu.stop(0)
  end
end, emu.eventType.endFrame)
