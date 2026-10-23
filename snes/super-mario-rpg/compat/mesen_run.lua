-- Run an lr.py scenario (s_*.txt) on Mesen 2 from power-on, for the same input on every emulator.
-- Mesen 2 --testrunner; env: LIBDIR SCRIPT SHOT_DIR [SRM]
-- SRM is copied into the save RAM on the first frame, as lr.py does for libretro cores.
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")

local presses, shots, last = {}, {}, 0
for line in io.lines(os.getenv("SCRIPT")) do
  local p = {}
  for w in line:gmatch("%S+") do p[#p + 1] = w end
  if #p >= 2 then
    local f = tonumber(p[1])
    if p[2] == "shot" then shots[f] = true
    elseif p[2] == "end" then last = f
    elseif p[2] == "tap" then
      for t = f, tonumber(p[5]) - 1, tonumber(p[4]) do presses[#presses + 1] = {t, t + 4, p[3]} end
    elseif p[2] ~= "dump" then presses[#presses + 1] = {f, f + tonumber(p[3]), p[2]} end
  end
end

local srm = os.getenv("SRM")
local n = 0
emu.addEventCallback(function()
  n = n + 1
  if n == 1 and srm then
    local d = L.readFile(srm)
    for i = 1, #d do emu.write(i - 1, d:byte(i), emu.memType.snesSaveRam) end
  end
  local held
  for _, p in ipairs(presses) do
    if p[1] <= n and n < p[2] then
      held = held or {}
      for b in p[3]:gmatch("[^+]+") do held[b] = true end
    end
  end
  if held then L.press(held) else L.release() end
  if shots[n] then L.shot(string.format("f%05d.png", n)) end
  if n >= last then L.shot("end.png"); emu.stop(0) end
end, emu.eventType.endFrame)
