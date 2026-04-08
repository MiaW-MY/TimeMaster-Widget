#!/bin/zsh

set -euo pipefail
unsetopt BG_NICE

PROJECT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
RUNTIME_DIR="$PROJECT_DIR/.run"
PID_FILE="$RUNTIME_DIR/time_master.pid"
LOG_FILE="$RUNTIME_DIR/time_master.log"

mkdir -p "$RUNTIME_DIR"

PYTHON_BIN="$PROJECT_DIR/.venv/bin/python3"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="$(command -v python3)"
fi

if [[ -f "$PID_FILE" ]]; then
  EXISTING_PID="$(<"$PID_FILE")"
  if [[ -n "$EXISTING_PID" ]] && kill -0 "$EXISTING_PID" 2>/dev/null; then
    echo "Time Master is already running (PID $EXISTING_PID)."
    echo "You can close this Terminal window."
    exit 0
  fi
  rm -f "$PID_FILE"
fi

cd "$PROJECT_DIR"
nohup "$PYTHON_BIN" "$PROJECT_DIR/time_master.py" >"$LOG_FILE" 2>&1 </dev/null &
APP_PID=$!
disown "$APP_PID" 2>/dev/null || true

sleep 1
if ! kill -0 "$APP_PID" 2>/dev/null; then
  rm -f "$PID_FILE"
  echo "Time Master exited immediately."
  echo "Check the log file: $LOG_FILE"
  exit 1
fi

echo "$APP_PID" > "$PID_FILE"

echo "Time Master started in background (PID $APP_PID)."
echo "Log file: $LOG_FILE"
echo "You can now close this Terminal window."
