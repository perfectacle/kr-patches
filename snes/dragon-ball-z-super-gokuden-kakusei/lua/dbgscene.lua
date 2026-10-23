package.path = "/path/to/gokuden2-kr-v1.3-tools/lua/?.lua;" .. package.path
local L = require("lib")
local n=0
local sc=tonumber(os.getenv("TARGET"),16)
local maxf=tonumber(os.getenv("MAXF") or "3000")
local period=tonumber(os.getenv("PERIOD") or "70")
emu.addEventCallback(function()
  n=n+1
  L.release()
  if n==430 then emu.write16(0x7E029C,sc,emu.memType.snesMemory) end
  if (n>=250 and n<254) or (n>=450 and n<454) or (n>600 and n%period<3) then L.press({a=true}) end
  if os.getenv("QUIZ") and n>600 and n%period>=40 and n%period<43 then L.press({x=true}) end
  local ev=tonumber(os.getenv("EVERY") or "0")
  if (ev>0 and n%ev==0) or (ev==0 and n>600 and n%period==period-4) then L.shot(string.format("q%05d.png",n)) end
  if n==maxf-1 then L.shot("end.png") end
  if n>=maxf then emu.stop(0) end
end, emu.eventType.endFrame)
local idlog=io.open(os.getenv("SHOT_DIR").."/ids.txt","w")
local last=-1
local function watch(lo,hi,first,tag)
  emu.addMemoryCallback(function(a)
    local id=(a-lo)//2+first
    if id~=last then last=id
      local st=emu.getState()
      local pc=st["cpu.k"]*0x10000+st["cpu.pc"]
      idlog:write(string.format("%d %03x %s %06x\n",n,id,tag,pc)) idlog:flush() end
  end, emu.callbackType.read, lo, hi, emu.cpuType.snes, emu.memType.snesMemory)
end
watch(0x998000,0x9987BF,0x000,"d")
watch(0x9A8000,0x9A83AD,0x3E0,"d")
watch(0x9B8000,0x9B83EF,0x5B7,"d")
watch(0x9C8000,0x9C839B,0x7AF,"d")
watch(0x9D8000,0x9D838F,0x97D,"d")
watch(0x9E8000,0x9E83A1,0xB45,"d")
watch(0x9F8000,0x9F837B,0xD16,"d")
watch(0x98C1C8,0x98C349,0xED4,"d")
watch(0xB48000,0xB487FF,0x1000,"b")
