from pathlib import Path

from fastapi_mail import (
    ConnectionConfig,
    FastMail,
    MessageSchema,
    MessageType,
    NameEmail,
)
from pydantic import SecretStr

from src.config import config

BASE_DIR = Path(__file__).resolve().parent

connectionConfig = ConnectionConfig(
    MAIL_USERNAME=config.MAIL_USERNAME,
    MAIL_PASSWORD=SecretStr(config.MAIL_PASSWORD),
    MAIL_FROM=config.MAIL_FROM,
    MAIL_PORT=config.MAIL_PORT,
    MAIL_SERVER=config.MAIL_SERVER,
    MAIL_FROM_NAME=config.MAIL_FROM_NAME,
    MAIL_STARTTLS=config.MAIL_STARTTLS,
    MAIL_SSL_TLS=config.MAIL_SSL_TLS,
    USE_CREDENTIALS=config.USE_CREDENTIALS,
    VALIDATE_CERTS=config.VALIDATE_CERTS,
    TEMPLATE_FOLDER=BASE_DIR / "templates",
)

mail = FastMail(config=connectionConfig)


def create_message(recipients: list[str], subject: str, body: str) -> MessageSchema:
    """Create an email message schema."""
    message = MessageSchema(
        recipients=[
            NameEmail(
                name=recipient.split("@")[0],
                email=recipient,
            )
            for recipient in recipients
        ],
        subject=subject,
        body=body,
        subtype=MessageType.html,
    )
    return message
