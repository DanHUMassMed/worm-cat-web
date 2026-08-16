#!/usr/bin/env bash

if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

celery -A worm_cat_app.celery worker -Q wormcat_web --loglevel=info --concurrency=4
#celery -A worm_cat_app.celery inspect stats
