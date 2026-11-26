
import uuid
from pathlib import Path

from fastapi import UploadFile


class LocalStorage:
    def __init__(self, storage_dir: str = "data/uploads"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, file: UploadFile) -> tuple[str, int]:
        document_id = str(uuid.uuid4())
        file_path = self.storage_dir / f"{document_id}.pdf"

        size = 0

        try:
            with file_path.open("wb") as destination:
                while chunk := await file.read(1024 * 1024):
                    size += len(chunk)

                    if size > 15 * 1024 * 1024:
                        raise ValueError("PDF exceeds the 15 MB limit.")

                    destination.write(chunk)

            return str(file_path), size

        except Exception:
            file_path.unlink(missing_ok=True)
            raise

    def delete(self, storage_path: str) -> None:
        Path(storage_path).unlink(missing_ok=True)
