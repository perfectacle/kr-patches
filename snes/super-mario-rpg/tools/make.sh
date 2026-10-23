#!/bin/zsh
# Build build/test.sfc = V1.0 Korean ROM + this patch.
# PYTHON defaults to the repository's .venv (see the top-level README).
set -e
cd "$(dirname $0)/.."
PY=${PYTHON:-${PWD:h:h}/.venv/bin/python}
$PY -I tools/build.py
$PY -I tools/py/dlg_rewrite.py rom/smrpg_kr_v1.sfc build/dlg_tbl.json build/dialogue.asm build/dialogue_report.txt
cp rom/smrpg_kr_v1.sfc build/test.sfc
tools/asar --fix-checksum=on src/main.asm build/test.sfc
$PY -I tools/py/check_menu_names.py
