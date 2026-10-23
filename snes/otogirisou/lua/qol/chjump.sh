#!/bin/zsh
# Jump to every chapter start from the scene the template save resumes in, the way the
# chapter menu does, and take screenshots.  usage: chjump.sh rom template.srm outdir
ROM=$1; TPL=$2; OUT=$3
SV=~/Library/Application\ Support/Mesen2/Saves
M=${MESEN:-Mesen}               # Mesen 2 executable
cd "$(dirname $0)/../.."
python3 - <<'PY' > $OUT/starts.txt
import sys; sys.path.insert(0,'tools')
from savemap import walk
L=open('tables/script.txt',encoding='utf-8').read().split('\n'); p=walk(L,True)
for l in open('tables/qol-chapters.tsv',encoding='utf-8'):
    if l.startswith('#') or not l.strip(): continue
    c=l.split('\t'); print(c[0], '%06X' % p[int(c[3])-1][0])
PY
while read id addr; do
  d=$OUT/ch$id; mkdir -p $d
  cp "$TPL" "$SV/cj$id.srm"
  cp $ROM $d/cj$id.sfc
  LIBDIR=$PWD/lua JF=2950 JADDR=$addr MAXF=4200 EVERY=100 PERIOD=40 TAPUNTIL=2800 SEQ="a@3400:4,a@3600:4,a@3800:4" SHOT_DIR=$d $M --testrunner $d/cj$id.sfc lua/qol/jumpto.lua >/dev/null 2>&1
done < $OUT/starts.txt
