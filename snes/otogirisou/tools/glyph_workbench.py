"""Glyph workbench: show glyphs and build new ones by rectangle transplant.
  python3 tools/glyph_workbench.py show 략각걱
  python3 tools/glyph_workbench.py make 갹 '략' 'ini=각:0-6,0-5'   base glyph, then name=src:rows,cols (inclusive) copied over
  python3 tools/glyph_workbench.py set 갹 '.##.' '#..#'
Glyphs come from tables/newglyphs.json, then from the v1.0 font in build/v1.0.sfc
(made by tools/build.sh); `make` and `set` write to tables/newglyphs.json.
"""
import sys, os
from kr_patch.glyph import store as S
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,os.path.join(ROOT,'tools'))
from compose import Composer
from dump import load_table
rom=open(os.path.join(ROOT,'build/v1.0.sfc'),'rb').read()
G=Composer(rom,load_table(os.path.join(ROOT,'tables/kr-v1.0.tbl'))).g
STORE=os.path.join(ROOT,'tables/newglyphs.json')
NEW=S.load(STORE)
def get(ch): return [list(r) for r in (NEW.get(ch) or G[ch])]
def show(gl): print('\n'.join(S.side_by_side(gl)))
if sys.argv[1]=='show':
    show([(c,get(c)) for c in sys.argv[2] if c in G or c in NEW])
elif sys.argv[1]=='make':
    ch,base=sys.argv[2],sys.argv[3]; g=get(base)
    for spec in sys.argv[4:]:
        src,rows,cols=S.parse_spec(spec)
        g=S.transplant(g,get(src),rows,cols)
    show([(ch,g),(base,get(base))]+[(S.parse_spec(sp)[0],get(S.parse_spec(sp)[0])) for sp in sys.argv[4:]])
    NEW[ch]=g; S.save(STORE,NEW)
elif sys.argv[1]=='set':
    ch=sys.argv[2]; NEW[ch]=S.parse(sys.argv[3:]); S.save(STORE,NEW)
    show([(ch,get(ch))])
