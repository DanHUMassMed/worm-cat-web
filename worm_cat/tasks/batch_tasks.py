"""Celery background tasks for asynchronous WormCat batch execution and progress tracking."""

import json
import logging
import os
from shutil import make_archive
from typing import Any, Dict

from celery.exceptions import SoftTimeLimitExceeded
from utils.email_utility import construct_message_with_html, email_results, send_message
from wormcat_batch.wormcat_batch import run_wormcat_batch

from .celery_app import celery, redis_server

logger = logging.getLogger(__name__)

BASE_DIR: str = os.getcwd()
DYNAMIC_DIR: str = os.getenv("DYNAMIC_DIR", "./static/dynamic")
DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "./static/download")
SMTP_SENDER_EMAIL: str = os.getenv("SMTP_SENDER_EMAIL", "wormcat@gmail.com")

TASK_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_TIME_LIMIT", "510"))
TASK_SOFT_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "500"))


def get_message(channel: str, timeout: int = 10) -> Dict[str, Any]:
    """Retrieve the next message from a Redis queue using non-polling blocking pop."""
    try:
        result = redis_server.brpop(channel, timeout=timeout)
        if result is None:
            return {"name": "TIMEOUT", "value": timeout}
        _, message_bytes = result
        if isinstance(message_bytes, bytes):
            data = message_bytes.decode("utf-8")
        else:
            data = str(message_bytes)
        return json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as e:
        logger.error("Error decoding Redis message from channel %s: %s", channel, e)
        return {"name": "ERROR", "value": "Error decoding message"}
    except Exception as e:
        logger.error("Redis error in get_message for channel %s: %s", channel, e)
        return {"name": "ERROR", "value": str(e)}


@celery.task(time_limit=TASK_TIME_LIMIT, soft_time_limit=TASK_SOFT_TIME_LIMIT)
def send_async_email(params: Dict[str, Any]) -> None:
    """Run WormCat batch analysis in the background, zip results, and optionally email output."""
    try:
        logger.info(
            "Starting async batch email processing for user=%s, annotation_file=%s",
            params.get("batch_user"),
            params.get("annotation_file"),
        )
        dir_nm = run_wormcat_batch(
            params["batch_user"],
            params["annotation_file"],
            params["xsl_file_nm"],
            redis_channel=params.get("redis_channel"),
            suffix=params.get("suffix"),
        )
        root_dir = f"{DYNAMIC_DIR}/{dir_nm}"
        base_name = f"{DOWNLOAD_DIR}/{dir_nm}"
        make_archive(base_name, "zip", root_dir=root_dir)
        zip_file = f"{base_name}.zip"

        if params.get("redis_channel"):
            redis_message = {"name": "DONE", "value": dir_nm}
            redis_server.lpush(params["redis_channel"], json.dumps(redis_message))

        email = params.get("email")
        if email is not None:
            email_results(email, zip_file)
            if os.path.exists(zip_file):
                os.remove(zip_file)
    except SoftTimeLimitExceeded:
        logger.warning("SoftTimeLimitExceeded during async email processing in base dir: %s", BASE_DIR)
        err_file_nm = f"{DYNAMIC_DIR}/async_email_timeout.txt"
        with open(err_file_nm, "a+") as err_file:
            err_file.write(f"{params.get('email')}, {params.get('xsl_file_nm')}, {params.get('redis_channel')}\n")
        receiver = params.get("email")
        if receiver is not None:
            sender = SMTP_SENDER_EMAIL
            message_text = "Sorry an error occurred during processing of your batch file.\nPlease try again later."
            subject = "Error running Wormcat"
            message = construct_message_with_html(subject, sender, receiver, message_text)
            send_message(sender, receiver, message)
    except Exception as e:
        logger.exception("Unexpected error in send_async_email: %s", e)
        if params.get("redis_channel"):
            redis_message = {"name": "ERROR", "value": str(e)}
            redis_server.lpush(params["redis_channel"], json.dumps(redis_message))
        raise


@celery.task(bind=True, time_limit=TASK_TIME_LIMIT)
def online_progress(self) -> Dict[str, Any]:
    """Track progress of a batch analysis task via Redis events and update Celery task state."""
    done = False
    download_url = "/bad"
    current = 0
    increment = 10
    while not done:
        message = get_message(self.request.id, timeout=10)
        if message["name"] == "DONE":
            download_url = f"{DOWNLOAD_DIR}/{message['value']}.zip"
            done = True
        elif message["name"] == "SHEETS":
            current += increment
            self.update_state(
                state="PROGRESS",
                meta={"current": current, "total": 100, "status": "Preparing Sheets"},
            )
            increment = int(80 / max(1, int(message.get("value", 1))))
        elif message["name"] == "MESSAGE":
            current += increment
            self.update_state(
                state="PROGRESS",
                meta={"current": current, "total": 100, "status": str(message.get("value", ""))},
            )
        elif message["name"] == "ERROR":
            done = True
            raise RuntimeError(message.get("value", "Batch processing failed"))
        elif message["name"] == "TIMEOUT":
            logger.debug("Waiting for batch updates on task %s (timeout interval reached)...", self.request.id)
    return {"current": 100, "total": 100, "status": "Batch completed!", "result": download_url}
