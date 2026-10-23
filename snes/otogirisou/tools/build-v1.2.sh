#!/bin/zsh
# Build v1.2 (v1.1 plus chapter select and ending list) on top of the v1.1 build.
# usage: tools/build-v1.2.sh   (needs build/otogirisou-kr-v1.1.sfc from tools/build.sh)
set -e
cd "$(dirname $0)/.."
JP="Otogirisou (Japan).sfc"
OUT=build/otogirisou-kr-v1.2.sfc
cp build/otogirisou-kr-v1.1.sfc $OUT
python3 tools/qol.py tables/script.txt build/kr.tbl tables/qol-chapters.tsv tables/qol-endings.tsv $OUT
python3 tools/flow.py tables/script.txt build/kr.tbl tables/qol-chapters.tsv tables/qol-endings.tsv $OUT
tools/asar --no-title-check asm/qol.asm $OUT
python3 tools/fixsum.py $OUT
python3 tools/ips.py make "$JP" $OUT "build/Otogirisou (K) v1.2.ips"
python3 -c "import zlib,hashlib,sys;d=open(sys.argv[1],'rb').read();print('CRC32 %08X MD5 %s'%(zlib.crc32(d),hashlib.md5(d).hexdigest().upper()))" $OUT
