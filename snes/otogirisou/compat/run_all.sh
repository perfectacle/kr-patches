#!/bin/zsh
# usage: run_all.sh  -> out/<scenario>-<core>-<rom>/ and results.txt
# wram.log follows the script pointer $7E0052-54 (`krpatch snes run --watch`).
cd "$(dirname $0)"
KRPATCH=${KRPATCH:-${PWD:h:h:h}/.venv/bin/krpatch}
export LRVARS="supafaust_thread_affinity_ppu=0x0,supafaust_thread_affinity_emu=0x0"
: > results.txt
run() { # scenario core rom [save]
  local d=out/$1-$2-$3${4:+-$4} f=roms/$3.sfc
  [[ -f $f ]] || f=roms/$3.smc
  mkdir -p $d
  $KRPATCH snes run cores/$2_libretro.dylib $f $d s_$1.txt ${4:+roms/save_$4.srm} --watch 7E0052:3 > $d.log 2>&1
  echo "$1 $2 $3 ${4:--} exit=$? $(grep -E '^OK|LOAD FAILED|terminat|Segmentation' $d.log | tail -1) last=$(tail -1 $d/wram.log 2>/dev/null)" >> results.txt
}
for core in bsnes bsnes_hd_beta snes9x snes9x2010 mednafen_supafaust mesen-s; do
  for rom in jp v10 v11 v11h; do run new $core $rom; done
  run cont $core jp jp
  run cont $core v10 v10
  for sv in v11 v10 jp; do run cont $core v11 $sv; done
  run cont $core v11h v10
done
