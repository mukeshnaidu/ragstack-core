from enum import Enum
from typing import Protocol, runtime_checkable

from ragstack_core.embedders.base_embedder import EmbedderProtocol
from ragstack_core.models.document_chunk import DocumentChunk


class VectorStoreProvider(str, Enum):
    PGVECTOR = "pgvector"
    QDRANT = "qdrant"
    CHROMA = "chroma"


@runtime_checkable
class VectorStoreProtocol(Protocol):
    def upsert(
        self, chunks: list[DocumentChunk], embedder: EmbedderProtocol
    ) -> None: ...

    async def upsert_async(
        self, chunks: list[DocumentChunk], embedder: EmbedderProtocol
    ) -> None: ...

    def search(
        self, query: str, embedder: EmbedderProtocol, top_k: int = 5
    ) -> list[DocumentChunk]: ...

    def search_with_scores(
        self, query: str, embedder: EmbedderProtocol, top_k: int = 5
    ) -> list[tuple[DocumentChunk, float]]: ...

    async def search_async(
        self, query: str, embedder: EmbedderProtocol, top_k: int = 5
    ) -> list[DocumentChunk]: ...

    async def search_with_scores_async(
        self, query: str, embedder: EmbedderProtocol, top_k: int = 5
    ) -> list[tuple[DocumentChunk, float]]: ...

    def delete(self, chunk_ids: list[str]) -> None: ...

    def delete_by_document_id(self, document_id: str) -> None: ...

    async def delete_async(self, chunk_ids: list[str]) -> None: ...

    async def delete_by_document_id_async(self, document_id: str) -> None: ...

    def close(self) -> None: ...
