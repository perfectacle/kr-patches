# usage: glyphs.py rom start count bytes_per_glyph rows out.png  (2bpp planar rows, 8px wide)
import sys
from PIL import Image
rom=open(sys.argv[1],'rb').read();st=int(sys.argv[2],16);n=int(sys.argv[3]);bpg=int(sys.argv[4],16);rows=int(sys.argv[5]);out=sys.argv[6]
cols=16;W=10;H=rows+2
img=Image.new('L',(cols*W,((n+cols-1)//cols)*H),128);px=img.load()
for g in range(n):
    d=rom[st+g*bpg:st+(g+1)*bpg];ox=(g%cols)*W;oy=(g//cols)*H
    for y in range(rows):
        lo,hi=d[y*2],d[y*2+1]
        for x in range(8):
            v=((lo>>(7-x))&1)|(((hi>>(7-x))&1)<<1)
            px[ox+x,oy+y]=[255,0,100,180][v]
img.resize((img.width*3,img.height*3),Image.NEAREST).save(out)
