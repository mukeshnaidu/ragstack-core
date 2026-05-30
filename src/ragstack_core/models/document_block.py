from typing import Any

from pydantic import BaseModel, Field


class DocumentBlock(BaseModel):
    document_id: str
    block_index: int
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
