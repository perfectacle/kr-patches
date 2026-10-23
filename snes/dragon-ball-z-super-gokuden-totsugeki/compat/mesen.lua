-- Mesen 2 replay of an lr.py script: SCRIPT=s_x.txt, SRM=save.srm (optional), SHOT_DIR=out
local dir = debug.getinfo(1, "S").source:match("^@(.*/)") or "./"
package.path = dir .. "../lua/?.lua;" .. package.path
local L = require("lib")
local BTN = {b="b", y="y", select="select", start="start", up="up", down="down", left="left", right="right", a="a", x="x", l="l", r="r"}
local presses, shots, endf = {}, {}, 0
for line in io.lines(os.getenv("SCRIPT")) do
  local p = {}
  for w in line:gmatch("%S+") do p[#p + 1] = w end
  if #p >= 2 then
    local f = tonumber(p[1])
    if p[2] == "shot" then shots[f] = true
    elseif p[2] == "end" then endf = f
    elseif p[2] == "tap" then
      for t = f, tonumber(p[5]) - 1, tonumber(p[4]) do presses[#presses + 1] = {t, t + 4, p[3]} end
    else presses[#presses + 1] = {f, f + tonumber(p[3]), p[2]} end
  end
end
local srm = os.getenv("SRM") and L.readFile(os.getenv("SRM"))
local m = emu.memType.snesMemory
local log = io.open(L.out .. "/wram.log", "w")
local prev, n = nil, 0
emu.addEventCallback(function()
  n = n + 1
  if srm and n <= 2 then for i = 1, #srm do emu.write(i - 1, srm:byte(i), emu.memType.snesSaveRam) end end
  L.release()
  local held = nil
  for _, p in ipairs(presses) do
    if n >= p[1] and n < p[2] then held = held or {}; for b in p[3]:gmatch("[^+]+") do held[BTN[b]] = true end end
  end
  if held then L.press(held) end
  local v = emu.read(0x7E004D, m) | (emu.read(0x7E004E, m) << 8)
  if v ~= prev then log:write(string.format("%d %04X\n", n, v)); prev = v end
  if shots[n] then L.shot(string.format("f%05d.png", n)) end
  if n >= endf then log:close(); L.shot("end.png"); emu.stop(0) end
end, emu.eventType.endFrame)
