#!/bin/zsh
# Build v1.3 (v1.2 plus the jamo name entry) on top of the v1.2 build.
# usage: tools/build-v1.3.sh   (needs build/otogirisou-kr-v1.1.sfc from tools/build.sh)
set -e
cd "$(dirname $0)/.."
PY=${PYTHON:-${PWD:h:h}/.venv/bin/python}
KRPATCH=${KRPATCH:-${PWD:h:h}/.venv/bin/krpatch}
JP="Otogirisou (Japan).sfc"
OUT=build/otogirisou-kr-v1.3.sfc
tools/build-v1.2.sh
cp build/otogirisou-kr-v1.2.sfc $OUT
$PY tools/namefont.py $OUT build/kr.tbl
tools/asar --no-title-check asm/nameentry.asm $OUT
$KRPATCH sfc checksum --fix --mapper lorom $OUT
$KRPATCH ips make "$JP" $OUT "build/Otogirisou (K) v1.3.ips"
$PY -c "import zlib,hashlib,sys;d=open(sys.argv[1],'rb').read();print('CRC32 %08X MD5 %s'%(zlib.crc32(d),hashlib.md5(d).hexdigest().upper()))" $OUT
