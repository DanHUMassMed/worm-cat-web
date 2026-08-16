import os
from typing import Any, Dict
from celery import Celery
from dotenv import load_dotenv

try:
    from worm_cat.utils.email_utility import construct_message_with_html, send_message_ssl, SMTP_SENDER_EMAIL
except ImportError:
    from utils.email_utility import construct_message_with_html, send_message_ssl, SMTP_SENDER_EMAIL

load_dotenv()

# Celery configuration
CELERY_BROKER_URL: str = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND: str = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Initialize Celery
celery = Celery('wormcat_tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
)


@celery.task
def send_async_email(email_data: Dict[str, Any]) -> None:
    sender = email_data.get('sender', SMTP_SENDER_EMAIL)
    message = construct_message_with_html(
        subject=email_data['subject'],
        sender=sender,
        receiver=email_data['to'],
        message_text=email_data.get('body'),
    )
    send_message_ssl(sender, email_data['to'], message)



