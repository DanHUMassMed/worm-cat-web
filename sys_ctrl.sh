#!/usr/bin/env bash
# ==============================================================================
# System Controller (sys_ctrl.sh) for WormCat Web
# Manages Redis, Celery Worker, and Web Application services
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$PROJECT_ROOT/worm_cat"
PID_DIR="$PROJECT_ROOT/.run"
LOG_DIR="$PROJECT_ROOT/logs"
VENV_DIR="$PROJECT_ROOT/.venv"

WEB_PID="$PID_DIR/web.pid"
CELERY_PID="$PID_DIR/celery.pid"
REDIS_PID="$PID_DIR/redis.pid"

WEB_LOG="$LOG_DIR/web.log"
CELERY_LOG="$LOG_DIR/celery.log"
REDIS_LOG="$LOG_DIR/redis.log"

PORT="${PORT:-9000}"
HOST="${HOST:-127.0.0.1}"

# Ensure runtime directories exist
mkdir -p "$PID_DIR" "$LOG_DIR"

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ensure_env() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
    else
        echo -e "${RED}[ERROR] Virtual environment not found at $VENV_DIR${NC}"
        echo "Run 'make install' first to set up the environment."
        exit 1
    fi
}

is_pid_running() {
    local pid="$1"
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

is_port_in_use() {
    local port="$1"
    if command -v lsof >/dev/null 2>&1; then
        lsof -i ":$port" -sTCP:LISTEN >/dev/null 2>&1
    elif command -v nc >/dev/null 2>&1; then
        nc -z 127.0.0.1 "$port" 2>/dev/null
    else
        return 1
    fi
}

start_redis() {
    echo -n "Checking Redis... "
    if is_port_in_use 6379; then
        echo -e "${GREEN}Running (port 6379 in use)${NC}"
        return 0
    fi

    echo -e "${YELLOW}Starting local Redis server...${NC}"
    if command -v redis-server >/dev/null 2>&1; then
        redis-server --daemonize yes --logfile "$REDIS_LOG" --pidfile "$REDIS_PID"
        echo -e "${GREEN}Redis started successfully.${NC}"
    elif [ -x "$PROJECT_ROOT/redis/redis-stable/src/redis-server" ]; then
        "$PROJECT_ROOT/redis/redis-stable/src/redis-server" --daemonize yes --logfile "$REDIS_LOG" --pidfile "$REDIS_PID"
        echo -e "${GREEN}Redis (local build) started successfully.${NC}"
    else
        echo -e "${RED}[WARNING] redis-server binary not found in PATH or redis-stable. Please install or start Redis.${NC}"
    fi
}

stop_redis() {
    echo -n "Stopping Redis... "
    local stopped=0
    if [ -f "$REDIS_PID" ]; then
        local pid
        pid=$(cat "$REDIS_PID")
        if is_pid_running "$pid"; then
            kill -TERM "$pid" 2>/dev/null || true
            for _ in {1..5}; do
                if ! is_pid_running "$pid"; then
                    stopped=1
                    break
                fi
                sleep 1
            done
            if [ $stopped -eq 0 ]; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$REDIS_PID"
        echo -e "${GREEN}Stopped.${NC}"
    elif is_port_in_use 6379; then
        pkill -TERM redis-server 2>/dev/null || true
        echo -e "${GREEN}Stopped (via pkill).${NC}"
    else
        echo -e "${YELLOW}Redis is not running.${NC}"
    fi
}

start_celery() {
    echo -n "Starting Celery worker... "
    if [ -f "$CELERY_PID" ]; then
        local pid
        pid=$(cat "$CELERY_PID")
        if is_pid_running "$pid"; then
            echo -e "${YELLOW}Already running (PID: $pid).${NC}"
            return 0
        fi
    fi

    ensure_env
    cd "$APP_DIR"
    nohup celery -A worm_cat_app.celery worker -Q wormcat_web --loglevel=info --concurrency=4 >> "$CELERY_LOG" 2>&1 &
    local new_pid=$!
    echo "$new_pid" > "$CELERY_PID"
    sleep 1

    if is_pid_running "$new_pid"; then
        echo -e "${GREEN}Started (PID: $new_pid).${NC}"
    else
        echo -e "${RED}Failed to start. Check $CELERY_LOG${NC}"
    fi
}

stop_celery() {
    echo -n "Stopping Celery worker... "
    local stopped=0
    if [ -f "$CELERY_PID" ]; then
        local pid
        pid=$(cat "$CELERY_PID")
        if is_pid_running "$pid"; then
            kill -TERM "$pid" 2>/dev/null || true
            for _ in {1..5}; do
                if ! is_pid_running "$pid"; then
                    stopped=1
                    break
                fi
                sleep 1
            done
            if [ $stopped -eq 0 ]; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$CELERY_PID"
    fi

    # Fallback cleanup for worker child processes
    pkill -TERM -f "celery -A worm_cat_app.celery worker" 2>/dev/null || true
    echo -e "${GREEN}Stopped.${NC}"
}

start_web() {
    local mode="${1:-dev}"
    echo -n "Starting Web server ($mode mode on $HOST:$PORT)... "

    if [ -f "$WEB_PID" ]; then
        local pid
        pid=$(cat "$WEB_PID")
        if is_pid_running "$pid"; then
            echo -e "${YELLOW}Already running (PID: $pid).${NC}"
            return 0
        fi
    fi

    ensure_env
    cd "$APP_DIR"

    local workers=3
    local loglevel="info"
    local bind_host="${HOST:-127.0.0.1}"

    if [ "$mode" == "dev" ]; then
        workers=2
        loglevel="debug"
    fi

    nohup gunicorn worm_cat_app:app \
        --workers "$workers" \
        --worker-class gevent \
        --timeout 120 \
        --log-level "$loglevel" \
        --bind "$bind_host:$PORT" \
        --pid "$WEB_PID" >> "$WEB_LOG" 2>&1 &

    sleep 1

    if [ -f "$WEB_PID" ] && is_pid_running "$(cat "$WEB_PID")"; then
        local new_pid
        new_pid=$(cat "$WEB_PID")
        echo -e "${GREEN}Started (PID: $new_pid).${NC}"
        echo -e "  --> App available at: ${BLUE}http://$bind_host:$PORT${NC}"
    else
        echo -e "${RED}Failed to start. Check $WEB_LOG${NC}"
    fi
}

stop_web() {
    echo -n "Stopping Web server... "
    local stopped=0
    if [ -f "$WEB_PID" ]; then
        local pid
        pid=$(cat "$WEB_PID")
        if is_pid_running "$pid"; then
            kill -TERM "$pid" 2>/dev/null || true
            for _ in {1..5}; do
                if ! is_pid_running "$pid"; then
                    stopped=1
                    break
                fi
                sleep 1
            done
            if [ $stopped -eq 0 ]; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$WEB_PID"
    fi

    # Also clean legacy gunicorn.pid if present in APP_DIR
    if [ -f "$APP_DIR/gunicorn.pid" ]; then
        local old_pid
        old_pid=$(cat "$APP_DIR/gunicorn.pid")
        kill -TERM "$old_pid" 2>/dev/null || true
        rm -f "$APP_DIR/gunicorn.pid"
    fi

    pkill -TERM -f "gunicorn worm_cat_app:app" 2>/dev/null || true
    echo -e "${GREEN}Stopped.${NC}"
}

start_all() {
    local mode="${1:-dev}"
    echo -e "${BLUE}=== Starting WormCat Services ($mode mode) ===${NC}"
    start_redis
    start_celery
    start_web "$mode"
    echo -e "${BLUE}===============================================${NC}"
}

stop_all() {
    echo -e "${BLUE}=== Stopping WormCat Services ===${NC}"
    stop_web
    stop_celery
    echo -e "${YELLOW}(Note: Redis was left running as it is independent/shared)${NC}"
    echo -e "${BLUE}=================================${NC}"
}

show_status() {
    echo -e "${BLUE}=== WormCat Services Status ===${NC}"

    # Redis
    echo -n "Redis Server:   "
    if is_port_in_use 6379; then
        echo -e "${GREEN}[RUNNING]${NC} (Port 6379 active)"
    else
        echo -e "${RED}[STOPPED]${NC}"
    fi

    # Celery
    echo -n "Celery Worker:  "
    if [ -f "$CELERY_PID" ] && is_pid_running "$(cat "$CELERY_PID")"; then
        echo -e "${GREEN}[RUNNING]${NC} (PID: $(cat "$CELERY_PID"))"
    elif pgrep -f "celery -A worm_cat_app.celery" >/dev/null 2>&1; then
        echo -e "${GREEN}[RUNNING]${NC} (PID: $(pgrep -f "celery -A worm_cat_app.celery" | head -n 1))"
    else
        echo -e "${RED}[STOPPED]${NC}"
    fi

    # Web
    echo -n "Web App Server: "
    if [ -f "$WEB_PID" ] && is_pid_running "$(cat "$WEB_PID")"; then
        echo -e "${GREEN}[RUNNING]${NC} (PID: $(cat "$WEB_PID"), URL: http://$HOST:$PORT)"
    elif [ -f "$APP_DIR/gunicorn.pid" ] && is_pid_running "$(cat "$APP_DIR/gunicorn.pid")"; then
        echo -e "${GREEN}[RUNNING]${NC} (PID: $(cat "$APP_DIR/gunicorn.pid"), URL: http://$HOST:$PORT)"
    elif pgrep -f "gunicorn worm_cat_app:app" >/dev/null 2>&1; then
        echo -e "${GREEN}[RUNNING]${NC} (PID: $(pgrep -f "gunicorn worm_cat_app:app" | head -n 1), URL: http://$HOST:$PORT)"
    else
        echo -e "${RED}[STOPPED]${NC}"
    fi
    echo -e "${BLUE}===============================${NC}"
}

show_logs() {
    local target="${1:-all}"
    case "$target" in
        web)
            tail -f "$WEB_LOG"
            ;;
        celery)
            tail -f "$CELERY_LOG"
            ;;
        redis)
            tail -f "$REDIS_LOG"
            ;;
        all|*)
            tail -f "$WEB_LOG" "$CELERY_LOG" "$REDIS_LOG" 2>/dev/null || true
            ;;
    esac
}

case "$1" in
    start)
        case "$2" in
            web)
                start_web "${3:-dev}"
                ;;
            celery)
                start_celery
                ;;
            redis)
                start_redis
                ;;
            *)
                start_all "${2:-dev}"
                ;;
        esac
        ;;
    stop)
        case "$2" in
            web)
                stop_web
                ;;
            celery)
                stop_celery
                ;;
            redis)
                stop_redis
                ;;
            *)
                stop_all
                ;;
        esac
        ;;
    stop-redis|stop_redis)
        stop_redis
        ;;
    restart)
        stop_all
        sleep 1
        start_all "${2:-dev}"
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    *)
        echo "Usage: $0 {start [dev|prod|web|celery|redis]|stop [web|celery|redis]|stop-redis|restart [dev|prod]|status|logs [web|celery|redis]}"
        exit 1
        ;;
esac
