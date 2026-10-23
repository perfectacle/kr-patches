"""Glyph workbench: show glyphs and build new ones by rectangle transplant.
  python3 gl.py show 략각걱
  python3 gl.py make 갹 '략' 'ini=각:0-6,0-5'   base glyph, then name=src:rows,cols (inclusive) copied over
"""
import sys, json; import os; ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,os.path.join(ROOT,'tools'))
from compose import Composer
from dump import load_table
rom=open(os.path.join(ROOT,'build/v1.0.sfc'),'rb').read()
G=Composer(rom,load_table(os.path.join(ROOT,'tables/kr-v1.0.tbl'))).g
STORE=os.path.join(ROOT,'tables/newglyphs.json')
try: NEW=json.load(open(STORE))
except Exception: NEW={}
def get(ch): return [list(map(int,r)) for r in (NEW.get(ch) or G[ch])]
def art(g): return [''.join('#' if p else '.' for p in r) for r in g]
def show(gl):
    arts=[(n,art(g)) for n,g in gl]
    print('  '.join(f'{n:<{len(a[0])}}' for n,a in arts))
    for y in range(max(len(a) for _,a in arts)):
        print('  '.join(a[y] if y<len(a) else ' '*len(a[0]) for _,a in arts))
if sys.argv[1]=='show':
    show([(c,get(c)) for c in sys.argv[2] if c in G or c in NEW])
elif sys.argv[1]=='make':
    ch,base=sys.argv[2],sys.argv[3]; g=get(base)
    for spec in sys.argv[4:]:
        src,rc=spec.split('=')[1].split(':'); rr,cc=rc.split(',')
        r0,r1=map(int,rr.split('-')); c0,c1=map(int,cc.split('-'))
        s=get(src)
        for y in range(r0,r1+1):
            for x in range(c0,c1+1): g[y][x]=s[y][x]
    show([(ch,g),(base,get(base))]+[(sp.split('=')[1].split(':')[0],get(sp.split('=')[1].split(':')[0])) for sp in sys.argv[4:]])
    if '--save' in sys.argv[2:] or True:
        NEW[ch]=[''.join(map(str,r)) for r in g]; json.dump(NEW,open(STORE,'w'),ensure_ascii=False,indent=0)
elif sys.argv[1]=='set':   # set ch from ASCII rows given as args
    ch=sys.argv[2]; rows=sys.argv[3:]
    NEW[ch]=[''.join('1' if c=='#' else '0' for c in r) for r in rows]; json.dump(NEW,open(STORE,'w'),ensure_ascii=False,indent=0)
    show([(ch,get(ch))])
