import asyncio
import hashlib
import logging
import struct

from ragstack_core.embedders.base_embedder import EmbedderProtocol
from ragstack_core.exceptions import MissingDependencyError, StorageError
from ragstack_core.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)


class QdrantStore:

    def __init__(
        self,
        connection_string: str = ":memory:",
        collection_name: str = "ragstack",
    ) -> None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import (
                Distance,
                FieldCondition,
                Filter,
                MatchValue,
                PointStruct,
                VectorParams,
            )
        except ImportError:
            raise MissingDependencyError(
                "qdrant-client is not installed. Run: uv add 'ragstack[qdrant]'"
            )
        self._collection_name = collection_name
        self._qdrant_models = {
            "Distance": Distance,
            "VectorParams": VectorParams,
            "PointStruct": PointStruct,
            "Filter": Filter,
            "FieldCondition": FieldCondition,
            "MatchValue": MatchValue,
        }
        if connection_string == ":memory:":
            self._client = QdrantClient(":memory:")
        else:
            self._client = QdrantClient(url=connection_string)
        self._collection_ensured = False

    @staticmethod
    def _chunk_id_to_point_id(chunk_id: str) -> int:
        h = hashlib.sha256(chunk_id.encode()).digest()
        return struct.unpack("!Q", h[:8])[0]

    def _ensure_collection(self, dimensions: int) -> None:
        if self._collection_ensured:
            return
        Distance = self._qdrant_models["Distance"]
        VectorParams = self._qdrant_models["VectorParams"]
        existing = [c.name for c in self._client.get_collections().collections]
        if self._collection_name not in existing:
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=VectorParams(size=dimensions, distance=Distance.COSINE),
            )
        self._collection_ensured = True

    def upsert(self, chunks: list[DocumentChunk], embedder: EmbedderProtocol) -> None:
        if not chunks:
            return
        self._ensure_collection(embedder.dimensions)
        PointStruct = self._qdrant_models["PointStruct"]
        texts = [c.text for c in chunks]
        try:
            vectors = embedder.embed(texts)
            points = [
                PointStruct(
                    id=self._chunk_id_to_point_id(chunk.chunk_id),
                    vector=vector,
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index,
                        "text": chunk.text,
                        "metadata": chunk.metadata,
                    },
                )
                for chunk, vector in zip(chunks, vectors)
            ]
            self._client.upsert(collection_name=self._collection_name, points=points)
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def search(
        self, query: str, embedder: EmbedderProtocol, top_k: int = 5
    ) -> list[DocumentChunk]:
        return [chunk for chunk, _ in self.search_with_scores(query, embedder, top_k)]

    def search_with_scores(
        self, query: str, embedder: EmbedderProtocol, top_k: int = 5
    ) -> list[tuple[DocumentChunk, float]]:
        if top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        self._ensure_collection(embedder.dimensions)
        vector = embedder.embed([query])[0]
        try:
            response = self._client.query_points(
                collection_name=self._collection_name,
                query=vector,
                limit=top_k,
                with_payload=True,
            )
            return [
                (
                    DocumentChunk(
                        chunk_id=hit.payload["chunk_id"],
                        document_id=hit.payload["document_id"],
                        chunk_index=hit.payload["chunk_index"],
                        text=hit.payload["text"],
                        metadata=hit.payload.get("metadata", {}),
                    ),
                    float(hit.score),
                )
                for hit in response.points
            ]
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def delete(self, chunk_ids: list[str]) -> None:
        if not chunk_ids:
            return
        try:
            point_ids = [self._chunk_id_to_point_id(cid) for cid in chunk_ids]
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=point_ids,
            )
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def delete_by_document_id(self, document_id: str) -> None:
        Filter = self._qdrant_models["Filter"]
        FieldCondition = self._qdrant_models["FieldCondition"]
        MatchValue = self._qdrant_models["MatchValue"]
        try:
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
                ),
            )
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def close(self) -> None:
        self._client.close()

    async def upsert_async(
        self, chunks: list[DocumentChunk], embedder: EmbedderProtocol
    ) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.upsert, chunks, embedder)

    async def search_async(
        self, query: str, embedder: EmbedderProtocol, top_k: int = 5
    ) -> list[DocumentChunk]:
        return [chunk for chunk, _ in await self.search_with_scores_async(query, embedder, top_k)]

    async def search_with_scores_async(
        self, query: str, embedder: EmbedderProtocol, top_k: int = 5
    ) -> list[tuple[DocumentChunk, float]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, self.search_with_scores, query, embedder, top_k
        )

    async def delete_async(self, chunk_ids: list[str]) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.delete, chunk_ids)

    async def delete_by_document_id_async(self, document_id: str) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.delete_by_document_id, document_id)
