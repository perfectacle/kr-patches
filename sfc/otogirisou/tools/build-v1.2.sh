#!/bin/zsh
# Build v1.2 (v1.1 plus chapter select and ending list) on top of the v1.1 build.
# usage: tools/build-v1.2.sh   (needs build/otogirisou-kr-v1.1.sfc from tools/build.sh)
set -e
cd "$(dirname $0)/.."
PY=${PYTHON:-${PWD:h:h}/.venv/bin/python}
KRPATCH=${KRPATCH:-${PWD:h:h}/.venv/bin/krpatch}
JP="Otogirisou (Japan).sfc"
OUT=build/otogirisou-kr-v1.2.sfc
cp build/otogirisou-kr-v1.1.sfc $OUT
$PY tools/qol.py tables/script.txt build/kr.tbl tables/qol-chapters.tsv tables/qol-endings.tsv $OUT
$PY tools/flow.py tables/script.txt build/kr.tbl tables/qol-chapters.tsv tables/qol-endings.tsv $OUT
tools/asar --no-title-check asm/qol.asm $OUT
$KRPATCH sfc checksum --fix --mapper lorom $OUT
$KRPATCH ips make "$JP" $OUT "build/Otogirisou (K) v1.2.ips"
$PY -c "import zlib,hashlib,sys;d=open(sys.argv[1],'rb').read();print('CRC32 %08X MD5 %s'%(zlib.crc32(d),hashlib.md5(d).hexdigest().upper()))" $OUT
