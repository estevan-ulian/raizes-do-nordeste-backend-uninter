import re
import uuid
from pathlib import Path

from fastapi import UploadFile

from src.config import config

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
READ_CHUNK_SIZE_BYTES = 1024 * 1024


class LocalStorage:
    def __init__(self, base_dir: str, public_base_url: str) -> None:
        self.base_dir = Path(base_dir)
        self.public_base_url = public_base_url.rstrip("/")

    async def save_product_image(self, image: UploadFile) -> str:
        header = await image.read(12)
        content_type = self._detect_image_content_type(header)
        if content_type is None:
            raise ValueError("invalid_image_type")

        extension = ALLOWED_IMAGE_CONTENT_TYPES[content_type]
        safe_stem = self._safe_stem(image.filename or "product")
        file_name = f"{safe_stem}-{uuid.uuid4().hex}{extension}"
        relative_path = Path("products") / file_name
        destination = self.base_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)

        size = len(header)
        try:
            with destination.open("wb") as file:
                file.write(header)
                while chunk := await image.read(READ_CHUNK_SIZE_BYTES):
                    size += len(chunk)
                    if size > MAX_IMAGE_SIZE_BYTES:
                        raise ValueError("image_too_large")
                    file.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise

        return f"{self.public_base_url}/{relative_path.as_posix()}"

    def delete_by_public_url(self, public_url: str | None) -> None:
        if not public_url or not public_url.startswith(f"{self.public_base_url}/"):
            return

        relative_path = Path(public_url.removeprefix(f"{self.public_base_url}/"))
        destination = (self.base_dir / relative_path).resolve()
        base_dir = self.base_dir.resolve()
        if base_dir in destination.parents:
            destination.unlink(missing_ok=True)

    @staticmethod
    def _detect_image_content_type(header: bytes) -> str | None:
        if header.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            return "image/webp"
        return None

    @staticmethod
    def _safe_stem(file_name: str) -> str:
        stem = Path(file_name).stem.lower()
        stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
        return stem or "product"


storage = LocalStorage(
    base_dir=str(config.UPLOAD_PATH),
    public_base_url=config.EFFECTIVE_UPLOAD_PUBLIC_URL,
)
