import hashlib
from typing import Any

from pydantic import BaseModel, Field, model_validator


class DocumentChunk(BaseModel):
    document_id: str
    chunk_id: str | None = None
    chunk_index: int
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _compute_chunk_id(self) -> "DocumentChunk":
        if not self.chunk_id:
            text_hash = hashlib.sha256(self.text.encode()).hexdigest()[:12]
            block_index = self.metadata.get("block_index", 0)
            raw = f"{self.document_id}:{block_index}:{self.chunk_index}:{text_hash}"
            self.chunk_id = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return self
