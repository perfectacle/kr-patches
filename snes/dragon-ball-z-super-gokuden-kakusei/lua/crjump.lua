package.path = "/path/to/gokuden2-kr-v1.3-tools/lua/?.lua;" .. package.path
local L = require("lib")
local n=0 local done=false
emu.addEventCallback(function()
  n=n+1
  L.release()
  if n==430 then emu.write16(0x7E029C,0x050,emu.memType.snesMemory) end
  if (n>=250 and n<254) or (n>=450 and n<454) then L.press({a=true}) end
  if n>800 and n%120==0 then L.shot(string.format("c%05d.png",n)) end
  if n>=9000 then emu.stop(0) end
end, emu.eventType.endFrame)
emu.addMemoryCallback(function()
  if n>700 and not done then done=true
    local s=emu.getState(); s["cpu.pc"]=0x8669; s["cpu.k"]=0x83; emu.setState(s) end
end, emu.callbackType.exec, 0x80822D, 0x80822D, emu.cpuType.snes, emu.memType.snesMemory)
