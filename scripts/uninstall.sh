#!/usr/bin/env bash
# Remove the Commonplace mod. Keeps your cards and /home/root/commonplace/.
# Usage: ./scripts/uninstall.sh [ssh-target]      (default: root@10.11.99.1)
set -euo pipefail

HOST="${1:-root@10.11.99.1}"
QRR=/home/root/xovi/exthome/qt-resource-rebuilder

ssh -o ConnectTimeout=8 "$HOST" "rm -f $QRR/commonplace.qmd && /home/root/xovi/start >/dev/null 2>&1; sleep 10; systemctl is-active xochitl"
echo "Mod removed. Your Commonplace notebook and card logs are untouched."
