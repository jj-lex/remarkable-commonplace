#!/usr/bin/env bash
# Install the Index Cards mod on a reMarkable that already has xovi + qt-resource-rebuilder.
# Usage: ./scripts/install.sh [ssh-target]      (default: root@10.11.99.1)
#        NOTEBOOK_NAME="Index Cards 2026" ./scripts/install.sh
set -euo pipefail

HOST="${1:-root@10.11.99.1}"
NOTEBOOK="${NOTEBOOK_NAME:-Index Cards}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
XOCHITL=/home/root/.local/share/remarkable/xochitl
QRR=/home/root/xovi/exthome/qt-resource-rebuilder
DATA=/home/root/indexcards

say() { printf '\n==> %s\n' "$*"; }

say "Connecting to $HOST"
ssh -o ConnectTimeout=8 "$HOST" true || { echo "Can't connect. Is the tablet awake and plugged in?"; exit 1; }

say "Checking xovi"
ssh "$HOST" "test -f /home/root/xovi/xovi.so" || { echo "xovi is not installed. See docs/SETUP.md, step 3."; exit 1; }
ssh "$HOST" "test -f $QRR/hashtab" || { echo "No lookup table. Run /home/root/xovi/rebuild_hashtable first (docs/SETUP.md, step 3)."; exit 1; }

say "Finding the notebook \"$NOTEBOOK\""
ID="$(ssh "$HOST" "cd $XOCHITL && grep -l '\"visibleName\": \"$NOTEBOOK\"' *.metadata 2>/dev/null | while read f; do grep -q '\"parent\": \"trash\"' \"\$f\" || echo \"\${f%.metadata}\"; done | head -n 1")"
if [ -z "$ID" ]; then
  echo "No notebook named \"$NOTEBOOK\" found. Create it on the tablet, or set NOTEBOOK_NAME."
  exit 1
fi
echo "Found it."

say "Saving settings"
ssh "$HOST" "mkdir -p $DATA && printf '{\"notebookId\": \"%s\"}\n' '$ID' > $DATA/config.json && { test -f $DATA/index.json || echo '[]' > $DATA/index.json; }"

say "Copying the mod"
scp -q "$HERE/mod/indexCards.qmd" "$HOST:$QRR/indexCards.qmd"

say "Starting xovi (the screen restarts once)"
ssh "$HOST" "/home/root/xovi/start >/dev/null 2>&1; sleep 10; systemctl is-active xochitl" || true

say "Done. Open a book and look for the ❝ button in the toolbar."
