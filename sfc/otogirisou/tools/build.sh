#!/bin/zsh
# Build v1.1 from the Japanese ROM and the v1.0 IPS.
# usage: tools/build.sh   (outputs build/otogirisou-kr-v1.1.sfc and IPS files)
set -e
cd "$(dirname $0)/.."
PY=${PYTHON:-${PWD:h:h}/.venv/bin/python}
KRPATCH=${KRPATCH:-${PWD:h:h}/.venv/bin/krpatch}
mkdir -p build
JP="Otogirisou (Japan).sfc"
OUT=build/otogirisou-kr-v1.1.sfc
# Japanese script for comparison, dumped from your own ROM (same line numbers as tables/script.txt)
[ -f tables/script-jp.txt ] || $PY tools/dump.py jp "$JP" tables/jp.tbl tables/script-jp.txt
$KRPATCH ips apply "$JP" "Otogirisou(K).ips" build/v1.0.sfc
cp build/v1.0.sfc $OUT
$PY tools/fixes.py $OUT
$PY tools/mkfont.py $OUT tables/kr-v1.0.tbl tables/script.txt build/kr.tbl
$PY tools/assemble.py $OUT build/kr.tbl tables/script.txt $OUT
tools/asar --no-title-check asm/wordwrap.asm $OUT
$PY tools/savemap.py tables/script-v1.0.txt tables/script.txt "$JP" $OUT
tools/asar --no-title-check asm/savecompat.asm $OUT
$KRPATCH sfc checksum --fix --mapper lorom $OUT
$KRPATCH ips make "$JP" $OUT "build/Otogirisou (K) v1.1.ips"
$PY -c "import zlib,hashlib,sys;d=open(sys.argv[1],'rb').read();print('CRC32 %08X MD5 %s'%(zlib.crc32(d),hashlib.md5(d).hexdigest().upper()))" $OUT
# reports (do not fail the build): key-wait mismatches with JP and pages over 9 lines
$PY tools/waits.py tables/script.txt tables/script-jp.txt build/kr.tbl tables/jp.tbl > build/waits.tsv
$PY tools/layout.py $OUT build/kr.tbl tables/script.txt --word > build/overflow.tsv
