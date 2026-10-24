-- Tap A until the script pointer reaches STOPAT, then let go and take a screenshot every
-- frame for SHOTS frames, to show whether the page waits for a key.
-- env: STOPAT (hex address), SHOTS, SEQ (menu presses, as boot.lua), SHOT_DIR, LIBDIR
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")
local stop = tonumber(os.getenv("STOPAT"), 16)
local shots = tonumber(os.getenv("SHOTS") or "120")
local presses = {}
for b, f, l in string.gmatch(os.getenv("SEQ") or "", "([%w+]+)@(%d+):(%d+)") do
  presses[#presses + 1] = {b, tonumber(f), tonumber(l)}
end
local n, stoppedAt, log = 0, nil, {}
emu.addEventCallback(function()
  n = n + 1
  L.release()
  local m = emu.memType.snesMemory
  local p = emu.read(0x7E0052, m) | emu.read(0x7E0053, m) << 8 | emu.read(0x7E0054, m) << 16
  if not stoppedAt and p >= stop and p < stop + 0x1000 then stoppedAt = n end
  if stoppedAt then
    local k = n - stoppedAt
    L.shot(string.format("w%04d.png", k))
    log[#log + 1] = string.format("%d %06X", k, p)
    if k >= shots then L.write("wait.txt", table.concat(log, "\n")); emu.stop(0) end
    return
  end
  for _, q in ipairs(presses) do
    if n >= q[2] and n < q[2] + q[3] then L.press({[q[1]] = true}); return end
  end
  if n > 1100 and n % 40 < 4 then L.press({a = true}) end
  if n > 20000 then emu.stop(1) end
end, emu.eventType.endFrame)
