#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$SCRIPT_DIR/logs"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting CalorieQ backend..." >> "$SCRIPT_DIR/logs/backend.log"
cd "$SCRIPT_DIR"
# FileHandler in log_config.json writes to logs/backend.log directly from the worker
.venv/Scripts/uvicorn app.main:app --reload --log-config log_config.json 2>&1 | tee -a logs/backend.log
