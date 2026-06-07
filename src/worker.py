from asgiref.sync import async_to_sync
from celery import Celery

from src.config import config
from src.mail import create_message, mail

celery_app = Celery(
    "raizes-worker",
    broker=config.REDIS_URL,
    backend=config.REDIS_URL,
    broker_connection_retry_on_startup=True,
)


@celery_app.task
def send_mail(recipients: list[str], subject: str, body: str):
    """Celery task to send an email."""
    message = create_message(recipients=recipients, subject=subject, body=body)
    async_to_sync(mail.send_message)(message)
