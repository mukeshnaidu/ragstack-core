from pydantic import BaseModel
from ragstack_core.models.document_chunk import DocumentChunk


class SearchResult(BaseModel):
    chunk: DocumentChunk
    score: float | None = None
