#!/usr/bin/env bash

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIDFILE="$APP_DIR/gunicorn.pid"
WAIT_SECONDS=5

stop_by_pid() {
    local pid="$1"
    echo "Sending SIGTERM to master process (PID: $pid)..."
    kill -TERM "$pid" 2>/dev/null || return 1

    # Wait up to WAIT_SECONDS for the process to exit cleanly
    for ((i=1; i<=WAIT_SECONDS; i++)); do
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "Process $pid stopped gracefully."
            rm -f "$PIDFILE"
            return 0
        fi
        sleep 1
    done

    echo "Process $pid did not stop after $WAIT_SECONDS seconds. Forcing shutdown (SIGKILL)..."
    kill -9 "$pid" 2>/dev/null
    rm -f "$PIDFILE"
}

stop_by_pattern() {
    echo "Sending SIGTERM to processes matching 'worm_cat_app:app'..."
    pkill -TERM -f "worm_cat_app:app"

    # Wait up to WAIT_SECONDS for processes to exit
    for ((i=1; i<=WAIT_SECONDS; i++)); do
        if ! pgrep -f "worm_cat_app:app" > /dev/null; then
            echo "All processes stopped successfully."
            return 0
        fi
        sleep 1
    done

    echo "Processes still running after $WAIT_SECONDS seconds. Forcing shutdown (SIGKILL)..."
    pkill -9 -f "worm_cat_app:app"
}

# Strategy 1: Try stopping via PID file
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        stop_by_pid "$PID"
        exit 0
    else
        echo "Stale PID file found. Removing..."
        rm -f "$PIDFILE"
    fi
fi

# Strategy 2: Fallback to process search
if pgrep -f "worm_cat_app:app" > /dev/null; then
    stop_by_pattern
else
    echo "No running processes found for 'worm_cat_app:app'."
fi
