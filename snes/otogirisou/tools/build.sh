#!/bin/zsh
# Build v1.1 from the Japanese ROM and the v1.0 IPS.
# usage: tools/build.sh   (outputs build/otogirisou-kr-v1.1.sfc and IPS files)
set -e
cd "$(dirname $0)/.."
mkdir -p build
JP="Otogirisou (Japan).sfc"
OUT=build/otogirisou-kr-v1.1.sfc
# Japanese script for comparison, dumped from your own ROM (same line numbers as tables/script.txt)
[ -f tables/script-jp.txt ] || python3 tools/dump.py jp "$JP" tables/jp.tbl tables/script-jp.txt
python3 tools/ips.py apply "$JP" "Otogirisou(K).ips" build/v1.0.sfc
cp build/v1.0.sfc $OUT
python3 tools/fixes.py $OUT
python3 tools/mkfont.py $OUT tables/kr-v1.0.tbl tables/script.txt build/kr.tbl
python3 tools/assemble.py $OUT build/kr.tbl tables/script.txt $OUT
tools/asar --no-title-check asm/wordwrap.asm $OUT
python3 tools/savemap.py tables/script-v1.0.txt tables/script.txt "$JP" $OUT
tools/asar --no-title-check asm/savecompat.asm $OUT
python3 tools/fixsum.py $OUT
python3 tools/ips.py make "$JP" $OUT "build/Otogirisou (K) v1.1.ips"
python3 -c "import zlib,hashlib,sys;d=open(sys.argv[1],'rb').read();print('CRC32 %08X MD5 %s'%(zlib.crc32(d),hashlib.md5(d).hexdigest().upper()))" $OUT
# reports (do not fail the build): key-wait mismatches with JP and pages over 9 lines
python3 tools/waits.py tables/script.txt tables/script-jp.txt build/kr.tbl tables/jp.tbl > build/waits.tsv
python3 tools/layout.py $OUT build/kr.tbl tables/script.txt --word > build/overflow.tsv
