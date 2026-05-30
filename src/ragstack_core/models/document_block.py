from pydantic import BaseModel, Field
from typing import Any


class DocumentBlock(BaseModel):
    document_id: str
    block_index: int
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)