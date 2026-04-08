#!/bin/zsh

set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
RUNTIME_DIR="$PROJECT_DIR/.run"
PID_FILE="$RUNTIME_DIR/time_master.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "Time Master is not currently tracked as running."
  exit 0
fi

APP_PID="$(<"$PID_FILE")"
if [[ -n "$APP_PID" ]] && kill -0 "$APP_PID" 2>/dev/null; then
  kill "$APP_PID"
  echo "Stopped Time Master (PID $APP_PID)."
else
  echo "Stored PID is no longer running."
fi

rm -f "$PID_FILE"
