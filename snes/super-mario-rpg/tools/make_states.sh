#!/bin/zsh
# Derived save states for scenes that are hard to reach by playing.
# Each line: base state, pokes written once, output (test/states/derived/).
cd "$(dirname $0)/.."
mkdir -p test/states/derived
derive() {   # base out pokes
  LIBDIR=$PWD/test STATE=$PWD/test/states/$1.mss POKE="$3" OUT=$2.mss SHOT_DIR=$PWD/test/states/derived \
    tools/Mesen.app/Contents/MacOS/Mesen --testrunner build/test.sfc test/poke_state.lua >/dev/null 2>&1
  [[ -f test/states/derived/$2.mss ]] && echo "test/states/derived/$2.mss" || echo "FAILED $2"
}
# Field before a battle with Mario's and Mallow's EXP (record +$0A, u16) far past
# their next levels: the win runs through several level-ups (levels past 10,
# several specials). A state saved mid-battle does not work: the battle keeps
# its own copy of the party and writes it back at the end.
derive prebattle lvup_many "7FF80A=00;7FF80B=08;7FF85A=00;7FF85B=08"
# Field before a battle, Mallow knowing Thought Peek (specials bits: $15 = bit 5 of +$12).
derive prebattle thought_peek "7FF862=E0"
# Bandit's Way 3 (state 1) with the Croco cutscene marked unseen ($7077 bit 7):
# re-entering the room plays it again, Mallow following as in the story.
derive prebattle croco_bw3_unseen "7077=63"
# State 1 holding a Carbo Cookie (item $89, first item slot) with the first
# cookie already given to Moleville's bucket girl ($704D bit 2): the second
# cookie gets a Frog Coin. Used with build/scene_molev*.sfc.
derive prebattle molev_cookie "7FF882=89;704D=04"
# State 1 with Booster's secret path open ($7047 bit 5): Moleville's hint guy
# tells about the hole in Iga valley. Used with build/scene_molev_n4*.sfc.
derive prebattle molev_secret_open "7047=20"
# State 1 a few EXP short of the next level (Mario 47/48 for level 3, Mallow
# 83/84 for level 4), as after a few more fights in Bandit's Way: one win gives
# "레벨3이", Mario's Fire Orb ("파이어볼을") and Mallow's "레벨4가".
derive prebattle lvup_next "7FF80A=2F;7FF80B=00;7FF85A=53;7FF85B=00"
# State 1 after Mack is beaten (Mushroom Kingdom freed, $7082 bit 0) with the
# Star Piece from Mack ($7084 bit 4): the Toad in Toadstool's room senses her.
derive prebattle castle_after_mack "7082=01;7084=10"
