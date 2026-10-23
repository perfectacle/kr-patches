-- At the first key wait after frame JF, move the script to JADDR (hex) the way the menu's
-- jump does (all four script position copies), then keep tapping A via boot.lua env.
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local f, done = 0, false
local at = tonumber(os.getenv("JF"))
local addr = tonumber(os.getenv("JADDR"), 16)
emu.addEventCallback(function()
  f = f + 1
  local m = emu.memType.snesMemory
  if not done and f >= at and emu.read16(0x1A95, m) ~= 0 then
    done = true
    local lo, bank = addr & 0xFFFF, addr >> 16
    for _, a in ipairs({0x52, 0x195B, 0x1972, 0x1989, 0x19A0}) do emu.write16(a, lo, m) end
    for _, a in ipairs({0x54, 0x195D, 0x1974, 0x198B, 0x19A2}) do emu.write(a, bank, m) end
    for _, a in ipairs({0x55, 0x195E, 0x1975, 0x198C, 0x19A3, 0x5D, 0x1960, 0x1977, 0x198E, 0x19A5}) do emu.write16(a, 0, m) end
    emu.write16(0x1A95, 0, m)
  end
end, emu.eventType.endFrame)
dofile(os.getenv("LIBDIR") .. "/boot.lua")
