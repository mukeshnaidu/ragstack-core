import asyncio
import json
import logging

from ragstack_core.embedders.base_embedder import EmbedderProtocol
from ragstack_core.exceptions import MissingDependencyError, StorageError
from ragstack_core.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)


def _safe_metadata(metadata: dict) -> dict:
    """Chroma metadata values must be str, int, float, or bool."""
    safe: dict = {}
    for k, v in metadata.items():
        if isinstance(v, (str, int, float, bool)):
            safe[k] = v
        elif isinstance(v, (dict, list)):
            safe[k] = json.dumps(v)
        else:
            safe[k] = str(v)
    return safe


class ChromaStore:
    def __init__(
        self,
        connection_string: str = ":memory:",
        collection_name: str = "ragstack",
    ) -> None:
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
        except ImportError:
            raise MissingDependencyError(
                "chromadb is not installed. Run: uv add 'ragstack[chroma]'"
            )
        self._collection_name = collection_name
        if connection_string == ":memory:":
            self._client = chromadb.EphemeralClient(
                settings=ChromaSettings(allow_reset=True)
            )
        else:
            self._client = chromadb.PersistentClient(path=connection_string)
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, chunks: list[DocumentChunk], embedder: EmbedderProtocol) -> None:
        if not chunks:
            return
        texts = [c.text for c in chunks]
        try:
            vectors = embedder.embed(texts)
            self._collection.upsert(
                ids=[c.chunk_id for c in chunks],
                embeddings=vectors,
                documents=texts,
                metadatas=[
                    {
                        "_ragstack_chunk_id": c.chunk_id,
                        "_ragstack_document_id": c.document_id,
                        "_ragstack_chunk_index": c.chunk_index,
                        **_safe_metadata(
                            {
                                k: v
                                for k, v in c.metadata.items()
                                if k
                                not in {
                                    "_ragstack_chunk_id",
                                    "_ragstack_document_id",
                                    "_ragstack_chunk_index",
                                }
                            }
                        ),
                    }
                    for c in chunks
                ],
            )
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
        vector = embedder.embed([query])[0]
        try:
            result = self._collection.query(
                query_embeddings=[vector],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
            if not result["documents"] or not result["documents"][0]:
                return []
            chunks_and_scores: list[tuple[DocumentChunk, float]] = []
            for doc, meta, distance in zip(
                result["documents"][0],
                result["metadatas"][0],
                result["distances"][0],
            ):
                chunk = DocumentChunk(
                    chunk_id=meta["_ragstack_chunk_id"],
                    document_id=meta["_ragstack_document_id"],
                    chunk_index=int(meta["_ragstack_chunk_index"]),
                    text=doc,
                    metadata={
                        k: v
                        for k, v in meta.items()
                        if k
                        not in {
                            "_ragstack_chunk_id",
                            "_ragstack_document_id",
                            "_ragstack_chunk_index",
                        }
                    },
                )
                score = 1.0 - distance
                chunks_and_scores.append((chunk, score))
            return chunks_and_scores
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def delete(self, chunk_ids: list[str]) -> None:
        if not chunk_ids:
            return
        try:
            self._collection.delete(ids=chunk_ids)
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def delete_by_document_id(self, document_id: str) -> None:
        try:
            self._collection.delete(where={"_ragstack_document_id": document_id})
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def close(self) -> None:
        pass

    async def upsert_async(
        self, chunks: list[DocumentChunk], embedder: EmbedderProtocol
    ) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.upsert, chunks, embedder)

    async def search_async(
        self, query: str, embedder: EmbedderProtocol, top_k: int = 5
    ) -> list[DocumentChunk]:
        return [
            chunk
            for chunk, _ in await self.search_with_scores_async(query, embedder, top_k)
        ]

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
