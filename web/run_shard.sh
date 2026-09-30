#!/bin/sh
# Porcja K z 4 pełnego przeglądu PM9_full_N500 na zamrożonym kodzie modelu (98a762f - wersja, na której
# policzono pierwsze 1144 przebiegi). Uruchamia obliczenia jako niezależny proces + autozapis co 30 min.
# Użycie (z katalogu repo): sh web/run_shard.sh K   -> wypisuje PID; wyniki: results/full_N500_r15_shardK.csv
K="$1"
REPO=$(pwd)
FROZEN="${TMPDIR:-/tmp}/sipd_frozen_98a762f"
git fetch -q origin 98a762f 2>/dev/null || true
[ -f "$FROZEN/web/sipd.py" ] || git worktree add -q -f --detach "$FROZEN" 98a762f
cp "$REPO/web/stage1.py" "$FROZEN/web/stage1.py"        # stage1 nie wpływa na wyniki modelu
OUT="$REPO/results/full_N500_r15_shard$K.csv"
LOG="$REPO/results/.full_N500_shard$K.log"
cd "$FROZEN" && setsid nohup python3 web/stage1.py --experiments PM9_full_N500 --N 500 --workers 4 --interleave \
    --shard "$K/4" --also-done "$REPO/results/full_N500_r15.csv" --resume --out "$OUT" >> "$LOG" 2>&1 < /dev/null &
PID=$!
cd "$REPO" && setsid nohup sh web/autosave.sh "$PID" 1800 "results/full_N500_r15_shard$K.csv" > /dev/null 2>&1 < /dev/null &
echo "$PID"
