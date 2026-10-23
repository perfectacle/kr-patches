#!/bin/zsh
# build/harness.sfc    = build/test.sfc + test/harness/harness.asm (test-only hooks)
# build/harness_v1.sfc = the V1.0 ROM + the same hooks, for before/after shots
cd "$(dirname $0)/.."
python3 -I -c "
import sys
r=open('build/test.sfc','rb').read()
if any(r[0x22FE00:0x22FF00]): sys.exit('harness area \$E2FE00 is used by the patch now; move it')
" || exit 1
cp build/test.sfc build/harness.sfc
tools/asar --fix-checksum=on test/harness/harness.asm build/harness.sfc
cp rom/smrpg_kr_v1.sfc build/harness_v1.sfc
tools/asar --fix-checksum=on test/harness/harness.asm build/harness_v1.sfc
# build/noresui.sfc = this patch without the battle result window layout change
cp rom/smrpg_kr_v1.sfc build/noresui.sfc
tools/asar --fix-checksum=on -Dres_ui=0 src/main.asm build/noresui.sfc
