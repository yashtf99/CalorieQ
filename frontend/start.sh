#!/usr/bin/env bash
# Starts the Vite dev server with timestamped logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="$SCRIPT_DIR/logs/frontend.log"
mkdir -p "$SCRIPT_DIR/logs"
cd "$SCRIPT_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting CalorieQ frontend..." | tee -a "$LOGFILE"

# Strip ANSI color codes and add timestamps to each line
npm run dev 2>&1 | sed -u 's/\x1b\[[0-9;]*[a-zA-Z]//g' | while IFS= read -r line; do
  if [[ -n "$line" ]]; then
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$line"
  fi
done | tee -a "$LOGFILE"
