import re
import uuid
from pathlib import Path

from fastapi import UploadFile

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}
MAX_FILE_SIZE = 10 * 1024 * 1024
STORAGE_ROOT = Path(__file__).resolve().parents[2] / "data" / "review_attachments"


def _safe_filename(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    return cleaned[:200] or "attachment"


class ReviewAttachmentService:
    def __init__(self, storage_root: Path | None = None) -> None:
        self._root = storage_root or STORAGE_ROOT
        self._root.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, message_id: str, upload: UploadFile) -> tuple[str, str, int, str]:
        content_type = upload.content_type or "application/octet-stream"
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValueError(f"File type '{content_type}' is not allowed.")

        data = await upload.read()
        if len(data) > MAX_FILE_SIZE:
            raise ValueError(f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)}MB.")
        if not data:
            raise ValueError("Uploaded file is empty.")

        file_name = _safe_filename(upload.filename or "attachment")
        message_dir = self._root / message_id
        message_dir.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid.uuid4().hex}_{file_name}"
        path = message_dir / stored_name
        path.write_bytes(data)
        return file_name, content_type, len(data), str(path)

    def resolve_path(self, storage_path: str) -> Path:
        path = Path(storage_path).resolve()
        root = self._root.resolve()
        if not str(path).startswith(str(root)):
            raise ValueError("Invalid attachment path")
        if not path.is_file():
            raise FileNotFoundError("Attachment file not found")
        return path