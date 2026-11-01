#!/usr/bin/env bash
# Install the Commonplace mod on a reMarkable that already has xovi + qt-resource-rebuilder.
# Usage: ./scripts/install.sh [ssh-target]      (default: root@10.11.99.1)
#        NOTEBOOK_NAME="My Quotes" ./scripts/install.sh      (default: "Commonplace <this year>", then "Commonplace")
set -euo pipefail

HOST="${1:-root@10.11.99.1}"
NOTEBOOK="${NOTEBOOK_NAME:-}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
XOCHITL=/home/root/.local/share/remarkable/xochitl
QRR=/home/root/xovi/exthome/qt-resource-rebuilder
DATA=/home/root/commonplace

say() { printf '\n==> %s\n' "$*"; }

say "Connecting to $HOST"
ssh -o ConnectTimeout=8 "$HOST" true || { echo "Can't connect. Is the tablet awake and plugged in?"; exit 1; }

say "Checking xovi"
ssh "$HOST" "test -f /home/root/xovi/xovi.so" || { echo "xovi is not installed. See docs/SETUP.md, step 3."; exit 1; }
ssh "$HOST" "test -f $QRR/hashtab" || { echo "No lookup table. Run /home/root/xovi/rebuild_hashtable first (docs/SETUP.md, step 3)."; exit 1; }

find_notebook() {
  ssh "$HOST" "cd $XOCHITL && grep -l '\"visibleName\": \"$1\"' *.metadata 2>/dev/null | while read f; do grep -q '\"parent\": \"trash\"' \"\$f\" || echo \"\${f%.metadata}\"; done | head -n 1"
}
if [ -n "$NOTEBOOK" ]; then CANDIDATES=("$NOTEBOOK"); else CANDIDATES=("Commonplace $(date +%Y)" "Commonplace"); fi
ID=""
for name in "${CANDIDATES[@]}"; do
  say "Looking for the notebook \"$name\""
  ID="$(find_notebook "$name")"
  [ -n "$ID" ] && break
done
if [ -z "$ID" ]; then
  echo "No notebook found. On the tablet, create a folder named Commonplace with a notebook named \"Commonplace $(date +%Y)\" inside it (or set NOTEBOOK_NAME)."
  exit 1
fi
echo "Found it."

say "Saving settings"
ssh "$HOST" "mkdir -p $DATA && printf '{\"notebookId\": \"%s\"}\n' '$ID' > $DATA/config.json && { test -f $DATA/index.json || echo '[]' > $DATA/index.json; }"

say "Copying the mod"
scp -q "$HERE/mod/commonplace.qmd" "$HOST:$QRR/commonplace.qmd"

say "Starting xovi (the screen restarts once)"
ssh "$HOST" "/home/root/xovi/start >/dev/null 2>&1; sleep 10; systemctl is-active xochitl" || true

say "Done. Open a book and look for the ❝ button in the toolbar."
