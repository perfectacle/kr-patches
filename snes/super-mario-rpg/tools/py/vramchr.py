# usage: vramchr.py vram byte_start ntiles bpp out.png [cols] [glyph8x16]
import sys
from PIL import Image
v=open(sys.argv[1],'rb').read();st=int(sys.argv[2],16);n=int(sys.argv[3],16);bpp=int(sys.argv[4]);out=sys.argv[5]
cols=int(sys.argv[6]) if len(sys.argv)>6 else 16
g16=len(sys.argv)>7
tb=8*bpp
def tile(t):
    base=st+t*tb;rows=[]
    for y in range(8):
        r=[]
        for x in range(8):
            b=7-x;val=0
            for p in range(bpp): val|=((v[base+(p//2)*16+y*2+(p&1)]>>b)&1)<<p
            r.append(val)
        rows.append(r)
    return rows
shade=lambda val:255-min(255,val*40) if val else 255
if g16:
    ng=n//2;img=Image.new('L',(cols*10,((ng+cols-1)//cols)*18),160);px=img.load()
    for g in range(ng):
        ox,oy=(g%cols)*10,(g//cols)*18
        for half in range(2):
            for y,r in enumerate(tile(g*2+half)):
                for x,val in enumerate(r): px[ox+x,oy+half*8+y]=shade(val)
else:
    img=Image.new('L',(cols*9,((n+cols-1)//cols)*9),160);px=img.load()
    for t in range(n):
        ox,oy=(t%cols)*9,(t//cols)*9
        for y,r in enumerate(tile(t)):
            for x,val in enumerate(r): px[ox+x,oy+y]=shade(val)
img.resize((img.width*3,img.height*3),Image.NEAREST).save(out)
