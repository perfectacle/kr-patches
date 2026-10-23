# usage: tiles.py rom start length bpp(1|2) out.png [cols]
import sys
from PIL import Image
rom=open(sys.argv[1],'rb').read();st=int(sys.argv[2],16);ln=int(sys.argv[3],16);bpp=int(sys.argv[4]);out=sys.argv[5]
cols=int(sys.argv[6]) if len(sys.argv)>6 else 32
tb=8*bpp;n=ln//tb;rows=(n+cols-1)//cols
img=Image.new('L',(cols*9,rows*9),40);px=img.load()
pal=[255,170,85,0] if bpp==2 else [255,0]
for t in range(n):
    d=rom[st+t*tb:st+(t+1)*tb];ox=(t%cols)*9;oy=(t//cols)*9
    for y in range(8):
        for x in range(8):
            b=7-x
            if bpp==1: v=(d[y]>>b)&1
            else: v=((d[y*2]>>b)&1)|(((d[y*2+1]>>b)&1)<<1)
            px[ox+x,oy+y]=pal[v] if v else 255
img=img.resize((img.width*2,img.height*2),Image.NEAREST);img.save(out)
print(out,n,'tiles')
