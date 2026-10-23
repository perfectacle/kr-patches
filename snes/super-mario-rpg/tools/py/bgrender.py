# Render one SNES BG layer from a VRAM dump.
# usage: bgrender.py vram cgram tilemap_word chr_word bpp out.png [palbase]
import sys
from PIL import Image
v=open(sys.argv[1],'rb').read();cg=open(sys.argv[2],'rb').read()
tm=int(sys.argv[3])*2;ch=int(sys.argv[4])*2;bpp=int(sys.argv[5]);out=sys.argv[6]
palbase=int(sys.argv[7]) if len(sys.argv)>7 else 0
def col(i):
    c=cg[i*2]|cg[i*2+1]<<8;return ((c&31)<<3,((c>>5)&31)<<3,((c>>10)&31)<<3)
img=Image.new('RGB',(256,256),(255,0,255));px=img.load()
tb=8*bpp
for ty in range(32):
    for tx in range(32):
        e=v[tm+(ty*32+tx)*2]|v[tm+(ty*32+tx)*2+1]<<8
        t=e&0x3FF;pal=(e>>10)&7;hf=e>>14&1;vf=e>>15&1
        base=(ch+t*tb)&0xFFFF
        for y in range(8):
            yy=7-y if vf else y
            for x in range(8):
                xx=7-x if hf else x;b=7-xx;val=0
                for p in range(bpp):
                    o=base+(p//2)*16+yy*2+(p&1)
                    val|=((v[o&0xFFFF]>>b)&1)<<p
                if val: px[tx*8+x,ty*8+y]=col(palbase+pal*(1<<bpp)+val)
img.resize((768,768),Image.NEAREST).save(out)
