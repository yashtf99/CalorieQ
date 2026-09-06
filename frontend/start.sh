#!/usr/bin/env bash
# Starts the Vite dev server, mirroring output to logs/frontend.log with timestamps.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="$SCRIPT_DIR/logs/frontend.log"
mkdir -p "$SCRIPT_DIR/logs"
cd "$SCRIPT_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting CalorieQ frontend..." | /usr/bin/tee -a "$LOGFILE"

# Strip ANSI colour codes, stamp each non-blank line, mirror to console + log file.
npm run dev 2>&1 \
  | /usr/bin/sed -u 's/\x1b\[[0-9;]*[a-zA-Z]//g' \
  | while IFS= read -r line; do
      case "$line" in
        *[![:space:]]*) printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$line" ;;
      esac
    done \
  | /usr/bin/tee -a "$LOGFILE"
