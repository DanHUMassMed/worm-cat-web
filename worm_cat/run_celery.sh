#!/usr/bin/env bash

if [ -d "/home/ec2-user/Applications/python_envs" ]; then
    source /home/ec2-user/Applications/python_envs/bin/activate
fi

celery -A worm_cat_app.celery worker --loglevel=info --concurrency=4
#celery -A worm_cat_app.celery inspect stats
