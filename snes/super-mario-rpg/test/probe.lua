-- Measurement probe for SMRPG (Mesen 2 --testrunner).
-- env: LIBDIR STATE SEQ OUT_DIR(=SHOT_DIR) EVERY TAIL
--      POKE="addr=val;..."   written every frame (CPU bus, S-CPU view)
--      ONCE="frame:addr=val;..."  written once, at that frame
--      EXEC="C156B4,C2420D"  log exec hits on S-CPU and SA-1
--      MAPCHECK=1            compare $00:3000/$00:6000 windows with SA-1 I-RAM / BW-RAM at the end
package.path = os.getenv("LIBDIR") .. "/?.lua;" .. package.path
local L = require("lib")
local log = {}
local function note(s) log[#log + 1] = s end
local function flush() L.write("probe.txt", table.concat(log, "\n") .. "\n") end
L.loadState(os.getenv("STATE"))

local steps = {}
for tok in string.gmatch(os.getenv("SEQ") or "wait:1", "[^,]+") do
  local b, f = tok:match("([%w+]+):(%d+)")
  steps[#steps + 1] = {b, tonumber(f)}
end
local pokes = {}
for a, v in string.gmatch(os.getenv("POKE") or "", "(%x+)=(%x+)") do pokes[#pokes + 1] = {tonumber(a, 16), tonumber(v, 16)} end

local once = {}
for f, a, v in string.gmatch(os.getenv("ONCE") or "", "(%d+):(%x+)=(%x+)") do once[#once + 1] = {tonumber(f), tonumber(a, 16), tonumber(v, 16)} end
local n = 0
local hits = {}
local cpus = {{"snes", emu.cpuType.snes, emu.memType.snesMemory}}
if emu.cpuType.sa1 and emu.memType.sa1Memory then cpus[#cpus + 1] = {"sa1", emu.cpuType.sa1, emu.memType.sa1Memory} end
for addr in string.gmatch(os.getenv("EXEC") or "", "(%x+)") do
  local a = tonumber(addr, 16)
  for _, c in ipairs(cpus) do
    local ok, err = pcall(function()
      emu.addMemoryCallback(function()
        local key = c[1] .. ":" .. addr
        hits[key] = (hits[key] or 0) + 1
        if hits[key] <= 5 then
          local m = emu.memType.snesMemory
          note(string.format("hit %s frame=%d FA06=%02X%02X E0=%02X 0B86=%02X%02X%02X", key, n,
            emu.read(0x7EFA07, m), emu.read(0x7EFA06, m), emu.read(0x7E00E0, m),
            emu.read(0x7E0B88, m), emu.read(0x7E0B87, m), emu.read(0x7E0B86, m)))
          L.shot(string.format("hit_%s_%s_%05d.png", c[1], addr, n))
        end
      end, emu.callbackType.exec, a, a, c[2], c[3])
    end)
    if not ok then note("exec hook failed " .. c[1] .. " " .. addr .. ": " .. tostring(err)) end
  end
end

local function mapcheck()
  local names = {}
  for k, _ in pairs(emu.memType) do names[#names + 1] = k end
  table.sort(names)
  note("memTypes: " .. table.concat(names, " "))
  local S = emu.memType.snesMemory
  local function same(memA, baseA, memB, baseB, len)
    local eq, nz = 0, 0
    for i = 0, len - 1 do
      local x = emu.read(baseA + i, memA)
      if x == emu.read(baseB + i, memB) then eq = eq + 1; if x ~= 0 then nz = nz + 1 end end
    end
    return eq, nz
  end
  local iram = emu.memType.sa1InternalRam
  if iram then
    local eq, nz = same(S, 0x3000, iram, 0, 0x800)
    note(string.format("S-CPU $00:3000-37FF vs sa1InternalRam 0-7FF: equal=%d/2048 (nonzero equal=%d)", eq, nz))
    note(string.format("$00:3030=%02X%02X  iram[30]=%02X%02X", emu.read(0x3031, S), emu.read(0x3030, S), emu.read(0x31, iram), emu.read(0x30, iram)))
  else note("no sa1InternalRam memType") end
  local bw = emu.memType.snesSaveRam
  if bw then
    local size = emu.getMemorySize and emu.getMemorySize(bw) or 0x8000
    note(string.format("snesSaveRam size=%d", size))
    for blk = 0, size // 0x2000 - 1 do
      local eq, nz = same(S, 0x6000, bw, blk * 0x2000, 0x2000)
      note(string.format("S-CPU $00:6000-7FFF vs BW-RAM block %d ($%04X): equal=%d/8192 (nonzero equal=%d)", blk, blk * 0x2000, eq, nz))
    end
    if emu.memType.sa1Memory then
      local eq, nz = same(S, 0x7000, emu.memType.sa1Memory, 0x400000 + 0x3000, 0x1000)
      note(string.format("S-CPU $00:7000-7FFF vs SA-1 $40:3000-3FFF: equal=%d/4096 (nonzero equal=%d)", eq, nz))
    end
  else note("no snesSaveRam memType") end
  local ok, st = pcall(emu.getState)
  if ok and type(st) == "table" then
    local keys = {}
    for k, v in pairs(st) do
      local lk = string.lower(k)
      if lk:find("sa1") or lk:find("bwram") or lk:find("bmap") then keys[#keys + 1] = k .. "=" .. tostring(v) end
    end
    table.sort(keys)
    note("state keys (sa1/bwram):\n  " .. table.concat(keys, "\n  "))
  else note("getState failed") end
end

local every = tonumber(os.getenv("EVERY") or "0")
local tail = tonumber(os.getenv("TAIL") or "60")
local i, left, done = 1, nil, nil
emu.addEventCallback(function()
  n = n + 1
  if n < 3 then return end
  for _, p in ipairs(pokes) do emu.write(p[1], p[2], emu.memType.snesMemory) end
  for _, p in ipairs(once) do if p[1] == n then emu.write(p[2], p[3], emu.memType.snesMemory) end end
  L.release()
  if i <= #steps then
    local s = steps[i]
    if left == nil then left = s[2] end
    if s[1] == "snap" then
      if left == s[2] then L.shot(string.format("s%05d.png", n)) end
    elseif s[1] ~= "wait" then local t = {}; for b in s[1]:gmatch("[^+]+") do t[b] = true end; L.press(t) end
    left = left - 1
    if left <= 0 then i = i + 1; left = nil end
  elseif not done then done = n end
  if every > 0 and n % every == 0 then L.shot(string.format("q%05d.png", n)) end
  if done and n == done + tail then
    L.shot("end.png")
    if os.getenv("MAPCHECK") == "1" then local ok, err = pcall(mapcheck); if not ok then note("mapcheck error: " .. tostring(err)) end end
    for k, v in pairs(hits) do note("hits " .. k .. " total=" .. v) end
    note("frames=" .. n)
    flush()
  end
  if done and n >= done + tail + 3 then emu.stop(0) end
end, emu.eventType.endFrame)
