#!/bin/zsh
# For each chapter: a save whose slot 1 has only that chapter read this playthrough; open
# the flowchart with Select, the chapter list with Y, and take the first entry. usage: menujump.sh rom template.srm outdir
ROM=$1; TPL=$2; OUT=$3
SV=~/Library/Application\ Support/Mesen2/Saves
M=${MESEN:-Mesen}               # Mesen 2 executable
cd "$(dirname $0)/../.."
LUA=$(${KRPATCH:-${PWD:h:h}/.venv/bin/krpatch} sfc lua)
for id in ${=IDS:-$(seq 1 30)}; do
  d=$OUT/ch$id; mkdir -p $d
  python3 -c "
d=bytearray(open('$TPL','rb').read()); d[0x1800:0x1880]=bytes(0x80); d[0x1800:0x1802]=b'LQ'
d[0x1810:0x1814]=(1<<($id-1)).to_bytes(4,'little'); open('$SV/mj$id.srm','wb').write(d)"
  cp $ROM $d/mj$id.sfc
  LIBDIR=$LUA MAXF=5000 EVERY=100 PERIOD=40 TAPUNTIL=2800 SEQ="select@3000:4,y@3200:4,a@3900:6,a@4500:4,a@4700:4" SHOT_DIR=$d $M --testrunner $d/mj$id.sfc $LUA/boot.lua >/dev/null 2>&1
done
