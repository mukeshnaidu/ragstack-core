from datetime import datetime, timezone
from pydantic import BaseModel, Field


class EmbeddingRecord(BaseModel):
    chunk_id: str
    model_name: str
    dimensions: int
    vector: list[float]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
