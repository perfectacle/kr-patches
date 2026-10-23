#!/bin/zsh
# usage: run_all.sh [core ...] -> out/<scenario>-<core>-<rom>/ and results.txt (appends)
# roms/: <rom>.sfc, or <rom>.smc for names ending in h (512-byte copier header); save.srm (made by v1.0)
# cores/: <core>_libretro.dylib. env ROMS picks the ROMs (default "jp v10 v11 v11h").
cd "$(dirname $0)"
export LRVARS="supafaust_thread_affinity_ppu=0x0,supafaust_thread_affinity_emu=0x0"
cores=($@)
(( $# )) || cores=(bsnes bsnes_hd_beta snes9x snes9x2010 mednafen_supafaust mesen-s)
for core in $cores; do
  for rom in ${=ROMS:-jp v10 v11 v11h}; do
    f=roms/$rom.sfc; [[ $rom == *h ]] && f=roms/$rom.smc
    for sc in new cont; do
      d=out/$sc-$core-$rom; rm -rf $d; mkdir -p $d
      if [[ $sc == cont ]]; then python3 lr.py cores/${core}_libretro.dylib $f $d s_$sc.txt roms/save.srm > $d.log 2>&1
      else python3 lr.py cores/${core}_libretro.dylib $f $d s_$sc.txt > $d.log 2>&1; fi
      echo "$sc $core $rom exit=$? $(grep -E '^OK|LOAD FAILED|terminat|Segmentation' $d.log | tail -1) last=$(tail -1 $d/wram.log 2>/dev/null)" >> results.txt
    done
  done
done
