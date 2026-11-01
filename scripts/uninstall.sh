#!/usr/bin/env bash
# Remove the Quote Cards mod. Keeps your cards and /home/root/quotecards/.
# Usage: ./scripts/uninstall.sh [ssh-target]      (default: root@10.11.99.1)
set -euo pipefail

HOST="${1:-root@10.11.99.1}"
QRR=/home/root/xovi/exthome/qt-resource-rebuilder

ssh -o ConnectTimeout=8 "$HOST" "rm -f $QRR/quoteCards.qmd && /home/root/xovi/start >/dev/null 2>&1; sleep 10; systemctl is-active xochitl"
echo "Mod removed. Your Quote Cards notebook and card logs are untouched."
