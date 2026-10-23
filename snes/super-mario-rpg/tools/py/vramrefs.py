# Report which VRAM byte ranges each BG tilemap references (mode 1: BG1/BG2 4bpp, BG3 2bpp).
# usage: vramrefs.py vram [bg1map bg1chr bg2map bg2chr bg3map bg3chr] (word addresses, defaults = menu layout)
import sys
v=open(sys.argv[1],'rb').read()
cfg=[int(x) for x in sys.argv[2:8]] if len(sys.argv)>7 else [0,4096,2048,12288,3072,20480]
for i,bpp in enumerate((4,4,2)):
    m,c=cfg[i*2]*2,cfg[i*2+1]*2;ts=set()
    for k in range(1024):
        e=v[m+k*2]|v[m+k*2+1]<<8;ts.add(e&0x3FF)
    hit=[t for t in ts if 0x6000<=c+t*8*bpp<0x8000]
    print('BG%d tiles->0x6000-0x7FFF: %d %s'%(i+1,len(hit),('%04X-%04X'%(c+min(hit)*8*bpp,c+max(hit)*8*bpp+8*bpp-1)) if hit else ''))
