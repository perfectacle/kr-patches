import sys,glob
from PIL import Image, ImageDraw
fs=sorted(glob.glob(sys.argv[1]));W=int(sys.argv[3]) if len(sys.argv)>3 else 10;s=0.5
w,h=int(256*s),int(224*s)
im=Image.new('RGB',(W*w,((len(fs)+W-1)//W)*(h+10)),'gray');d=ImageDraw.Draw(im)
for i,f in enumerate(fs):
    x,y=(i%W)*w,(i//W)*(h+10);im.paste(Image.open(f).convert('RGB').resize((w,h)),(x,y+10));d.text((x+2,y),f.split('/')[-1][:-4],fill='white')
im.save(sys.argv[2]);print(len(fs))
