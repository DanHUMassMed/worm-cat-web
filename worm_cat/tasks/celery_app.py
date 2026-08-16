"""Celery application instance and Redis broker initialization."""

import os
from celery import Celery
from dotenv import load_dotenv
import redis

load_dotenv()

REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB: int = int(os.getenv("REDIS_DB", "1"))

redis_server = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

CELERY_BROKER_URL: str = os.getenv(
    "CELERY_BROKER_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
)
CELERY_RESULT_BACKEND: str = os.getenv(
    "CELERY_RESULT_BACKEND", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
)

celery = Celery("wormcat_tasks", broker=CELERY_BROKER_URL)
celery.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_default_queue="wormcat_web",
    broker_transport_options={"global_keyprefix": "wormcat_web:"},
    result_backend_transport_options={"global_keyprefix": "wormcat_web:"},
)
