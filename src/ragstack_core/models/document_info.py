import hashlib
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    CSV = "csv"
    XLSX = "xlsx"
    MD = "md"


class DocumentInfo(BaseModel):
    document_id: str = ""
    file_name: str
    file_size_bytes: int
    source_path: str
    file_type: FileType
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def _compute_document_id(self) -> "DocumentInfo":
        if not self.document_id:
            raw = f"{self.source_path}:{self.file_size_bytes}"
            self.document_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self

    @classmethod
    def from_path(cls, file_path: str | Path) -> "DocumentInfo":
        path = Path(file_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = path.suffix.lower().replace(".", "")

        try:
            file_type = FileType(suffix)
        except ValueError:
            raise ValueError(f"Unsupported file type: {suffix}")

        stat = path.stat()
        file_size = stat.st_size
        raw = f"{path}:{file_size}"
        doc_id = hashlib.sha256(raw.encode()).hexdigest()[:16]

        return cls(
            document_id=doc_id,
            source_path=str(path),
            file_name=path.name,
            file_type=file_type,
            file_size_bytes=file_size,
        )
