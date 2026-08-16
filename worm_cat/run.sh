#!/usr/bin/env bash
echo $1
if [ "$1" == "" ]; then
   PORT=9000
else
   PORT=$1
fi

NUM_WORKERS=3
TIMEOUT=120
PIDFILE="gunicorn.pid"

if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

exec gunicorn worm_cat_app:app \
--workers $NUM_WORKERS \
--worker-class gevent \
--timeout $TIMEOUT \
--log-level=debug \
--bind=127.0.0.1:$PORT \
--pid=$PIDFILE
