#!/usr/bin/env bash
set -euo pipefail
TARGET_FILE="mad_games_tycoon_2_planer.py"
isort ${TARGET_FILE}
black ${TARGET_FILE}
flake8 ${TARGET_FILE}
pylint --disable=C0103 ${TARGET_FILE}
mypy --strict ${TARGET_FILE}
python ${TARGET_FILE} --selftest
