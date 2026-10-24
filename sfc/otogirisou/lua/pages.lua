-- Screenshot every finished page: when the script pointer ($52-$54) has not moved for
-- STABLE frames, save p<addr>.png once per address and log "frame addr" to pages.txt.
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")
-- LIBDIR holds the toolkit scripts (`krpatch sfc lua`); this game's scripts are loaded from here.
local here = debug.getinfo(1, "S").source:match("^@(.*/)") or "./"
local stable = tonumber(os.getenv("STABLE") or "25")
local f, last, since = 0, -1, 0
local seen, log = {}, {}
emu.addEventCallback(function()
  f = f + 1
  local m = emu.memType.snesMemory
  local p = emu.read(0x7E0052, m) | emu.read(0x7E0053, m) << 8 | emu.read(0x7E0054, m) << 16
  if p == last then since = since + 1 else last, since = p, 0 end
  if since == stable and not seen[p] then
    seen[p] = true
    local name = string.format("p%06X.png", p)
    L.shot(name)
    log[#log + 1] = string.format("%d %06X", f, p)
    L.write("pages.txt", table.concat(log, "\n"))
  end
end, emu.eventType.endFrame)
dofile(here .. "lap.lua")
