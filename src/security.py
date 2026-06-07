import logging
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
import redis.asyncio as aioredis
from itsdangerous import URLSafeSerializer

from src.config import config
from src.utils import get_utc_now

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 3600  # 1 hour


def create_access_token(
    user_data: dict,
    expiry: timedelta = timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS),
    refresh: bool = False,
) -> str:
    """Create a JWT access token with the given user data and expiry time."""
    payload = {}
    payload["user"] = user_data
    payload["exp"] = get_utc_now() + expiry
    payload["jti"] = str(uuid.uuid4())
    payload["refresh"] = refresh

    token = jwt.encode(payload=payload, key=config.SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_token(token: str) -> dict | None:
    """Decode a JWT token and return its payload. Returns None if the token is invalid."""
    try:
        token_data = jwt.decode(jwt=token, key=config.SECRET_KEY, algorithms=[ALGORITHM])
        return token_data
    except jwt.PyJWTError as error:
        logging.exception(error)
        return None


def generate_password_hash(password: str) -> str:
    """Hash a plaintext password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


token_salt = "email-configuration"
token_serializer = URLSafeSerializer(secret_key=config.SECRET_KEY, salt=token_salt)


def create_url_safe_token(data: dict):
    token = token_serializer.dumps(obj=data, salt=token_salt)
    return token


def decode_url_safe_token(token: str) -> dict | None:
    try:
        token_data = token_serializer.loads(s=token, salt=token_salt)
        exp = token_data.get("exp")
        if exp and datetime.now(timezone.utc).timestamp() > exp:
            return None
        return token_data
    except Exception as error:
        logging.exception(error)
        return None


TOKEN_BLOCK_LIST = aioredis.from_url(
    url=config.REDIS_URL,
)
JTI_EXPIRY_SECONDS = 60 * 60 * 24 * 7  # 7 days
JTI_PREFIX = "auth_token:"


async def add_jti_to_blocklist(jti: str) -> None:
    """Store a JTI in the blocklist with a 7-day TTL."""
    await TOKEN_BLOCK_LIST.set(name=f"{JTI_PREFIX}{jti}", value="", ex=JTI_EXPIRY_SECONDS)


async def token_in_blocklist(jti: str) -> bool:
    """Check if a JTI is in the blocklist (already used)."""
    jti = await TOKEN_BLOCK_LIST.get(name=f"{JTI_PREFIX}{jti}")
    return jti is not None


RESET_TOKEN_PREFIX = "reset_password:"
RESET_TOKEN_EXPIRY_SECONDS = 60 * 60 * 2  # 2 hours


async def add_reset_token_to_blocklist(token_id: str) -> None:
    """Store a reset token in the blocklist with a 2-hour TTL."""
    await TOKEN_BLOCK_LIST.set(
        name=f"{RESET_TOKEN_PREFIX}{token_id}", value="", ex=RESET_TOKEN_EXPIRY_SECONDS
    )


async def reset_token_in_blocklist(token_id: str) -> bool:
    """Verify if a reset token is in the blocklist (already used)."""
    result = await TOKEN_BLOCK_LIST.get(name=f"{RESET_TOKEN_PREFIX}{token_id}")
    return result is not None
