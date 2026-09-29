#!/bin/sh
# Zapis częściowych wyników długiego przeglądu: co INTERVAL sekund commit + push plików, dopóki żyje proces PID.
# Użycie: sh web/autosave.sh <PID> <interwał s> <plik> [plik...]
PID="$1"; INTERVAL="$2"; shift 2
save() {
    [ -s "$1" ] || return 0
    git add -f "$@" 2>/dev/null
    if ! git diff --cached --quiet -- "$@"; then
        n=$(($(wc -l < "$1") - 1))
        msg=$(mktemp)
        printf 'Pełny przegląd N = 500: częściowe wyniki (%s przebiegów)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_019k73S7cZJWPrBZf5HaTdxg\n' "$n" > "$msg"
        git commit -q -F "$msg" -- "$@" && { git pull -q --no-rebase --no-edit origin "$(git rev-parse --abbrev-ref HEAD)"; git push -q origin "$(git rev-parse --abbrev-ref HEAD)"; } || true
        rm -f "$msg"
    fi
}
elapsed=0
while kill -0 "$PID" 2>/dev/null; do
    sleep 60
    elapsed=$((elapsed + 60))
    if [ "$elapsed" -ge "$INTERVAL" ]; then save "$@"; elapsed=0; fi
done
save "$@"
