from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class AppConfig(BaseSettings):
    """Application configuration loaded from environment variables."""

    FRONTEND_URL: str | None = None
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "super-secret-key-change-in-production"
    FIRST_ADMIN_EMAIL: str = "admin@example.com"
    FIRST_ADMIN_PASSWORD: str = "admin"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str = "email@exemplo.com"
    MAIL_PORT: int = 1025
    MAIL_SERVER: str = "localhost"
    MAIL_FROM_NAME: str = "Raízes do Nordeste"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = False
    VALIDATE_CERTS: bool = True

    API_ROOT_PATH: str = "/api"
    UPLOAD_DIR: str = "static/uploads"
    UPLOAD_PUBLIC_URL: str = "/uploads"

    @property
    def UPLOAD_PATH(self) -> Path:
        upload_path = Path(self.UPLOAD_DIR)
        if not upload_path.is_absolute():
            upload_path = BASE_DIR / upload_path
        return upload_path

    @property
    def EFFECTIVE_UPLOAD_PUBLIC_URL(self) -> str:
        public_url = self.UPLOAD_PUBLIC_URL.rstrip("/") or "/uploads"
        root_path = self.API_ROOT_PATH.rstrip("/")
        if root_path and public_url.startswith("/") and not public_url.startswith(f"{root_path}/"):
            return f"{root_path}{public_url}"
        return public_url

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


config = AppConfig()
