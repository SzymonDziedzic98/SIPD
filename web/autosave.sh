#!/bin/sh
# Zapis częściowych wyników długiego przeglądu: co INTERVAL sekund commit + push plików, dopóki działa proces.
# Użycie: sh web/autosave.sh <wzorzec procesu> <interwał s> <plik> [plik...]
PATTERN="$1"; INTERVAL="$2"; shift 2
save() {
    git add -f "$@" 2>/dev/null
    if ! git diff --cached --quiet -- "$@"; then
        n=$(($(wc -l < "$1") - 1))
        git commit -q -m "Pełny przegląd N = 500: częściowe wyniki ($n przebiegów)" -- "$@" && \
            git push -q origin "$(git rev-parse --abbrev-ref HEAD)" || true
    fi
}
while pgrep -f "$PATTERN" > /dev/null; do
    sleep "$INTERVAL"
    save "$@"
done
save "$@"
