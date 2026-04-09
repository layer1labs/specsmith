#!/usr/bin/env bash
# specsmith — Command Execution Shim (POSIX)
# Wraps external commands with PID tracking, timeout enforcement, and abort support.
# Usage: ./scripts/exec.sh <timeout_seconds> <command...>
#
# PID files: .specsmith/pids/<pid>.json (for specsmith ps / specsmith abort)
# Logs:      .specsmith/logs/exec_<timestamp>.stdout/.stderr
# Prefer:    specsmith exec "<command>" --timeout <N>  (Python-based, full tracking)
set -uo pipefail

TIMEOUT_SECONDS="${1:?Usage: exec.sh <timeout_seconds> <command...>}"
shift
COMMAND="$*"

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_DIR="$PROJECT_ROOT/.specsmith/pids"
LOG_DIR="$PROJECT_ROOT/.specsmith/logs"
mkdir -p "$PID_DIR" "$LOG_DIR"

TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
STDOUT_LOG="$LOG_DIR/exec_${TIMESTAMP}.stdout"
STDERR_LOG="$LOG_DIR/exec_${TIMESTAMP}.stderr"

echo "[exec] Command : $COMMAND"
echo "[exec] Timeout : ${TIMEOUT_SECONDS}s"

# Launch in background, track PID
bash -c "$COMMAND" > "$STDOUT_LOG" 2> "$STDERR_LOG" &
CMD_PID=$!

# Write PID file for specsmith ps/abort
cat > "$PID_DIR/${CMD_PID}.json" <<EOF
{"pid": ${CMD_PID}, "command": "$COMMAND", "started": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "timeout": ${TIMEOUT_SECONDS}}
EOF

# Cleanup function — remove PID file on exit
cleanup() {
    rm -f "$PID_DIR/${CMD_PID}.json"
}
trap cleanup EXIT

# Watchdog: kill after timeout
( sleep "$TIMEOUT_SECONDS" && kill -TERM "$CMD_PID" 2>/dev/null && sleep 5 && kill -9 "$CMD_PID" 2>/dev/null ) &
WATCHDOG=$!

START_TIME=$(date +%s)
wait "$CMD_PID" 2>/dev/null
EXIT_CODE=$?
DURATION=$(( $(date +%s) - START_TIME ))

# Kill watchdog if command finished before timeout
kill "$WATCHDOG" 2>/dev/null
wait "$WATCHDOG" 2>/dev/null

if [ "$EXIT_CODE" -eq 143 ] || [ "$EXIT_CODE" -eq 137 ]; then
    echo "[exec] TIMEOUT after ${TIMEOUT_SECONDS}s (PID $CMD_PID killed)"
    exit 124
fi
echo "[exec] $([ $EXIT_CODE -eq 0 ] && echo OK || echo FAILED) (${DURATION}s) — exit code $EXIT_CODE"
exit "$EXIT_CODE"
