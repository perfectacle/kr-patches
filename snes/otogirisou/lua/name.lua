-- Replace the player name once the story runs, so captures show a real name instead of the
-- letters the periodic A taps typed. env: NAME="494,1180" (glyph codes), plus pages.lua env
local codes = {}
for c in string.gmatch(os.getenv("NAME") or "494,1180", "%d+") do codes[#codes + 1] = tonumber(c) end
codes[#codes + 1] = 0xFFFF
emu.addEventCallback(function()
  local m = emu.memType.snesMemory
  local bank = emu.read(0x7E0054, m)
  if bank < 0x20 or bank > 0x35 then return end
  for i, c in ipairs(codes) do
    for _, base in ipairs({0x7E1BC9, 0x7E005F}) do
      emu.write(base + (i - 1) * 2, c & 0xFF, m)
      emu.write(base + (i - 1) * 2 + 1, c >> 8, m)
    end
  end
end, emu.eventType.endFrame)
dofile(os.getenv("LIBDIR") .. "/pages.lua")
