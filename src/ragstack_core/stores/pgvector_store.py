import asyncio
import json
import logging

from ragstack_core.embedders.base_embedder import EmbedderProtocol
from ragstack_core.exceptions import MissingDependencyError, StorageError
from ragstack_core.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)


class PgVectorStore:
    def __init__(
        self, connection_string: str, collection_name: str = "ragstack"
    ) -> None:
        try:
            import psycopg
            from pgvector.psycopg import register_vector
            from psycopg.rows import dict_row
            from psycopg_pool import ConnectionPool
        except ImportError:
            raise MissingDependencyError(
                "psycopg and pgvector are not installed. "
                "Run: uv add 'ragstack[pgvector]'"
            )
        self._collection_name = collection_name
        self._register_vector = register_vector
        self._psycopg = psycopg
        self._dict_row = dict_row
        self._pool = ConnectionPool(
            connection_string,
            min_size=1,
            max_size=10,
            kwargs={"row_factory": dict_row},
        )

    def _configure_conn(self, conn) -> None:
        self._register_vector(conn)

    def upsert(self, chunks: list[DocumentChunk], embedder: EmbedderProtocol) -> None:
        if not chunks:
            return
        texts = [c.text for c in chunks]
        vectors = embedder.embed(texts)
        try:
            with self._pool.connection() as conn:
                self._register_vector(conn)
                with conn.cursor() as cur:
                    chunk_rows = [
                        (
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.chunk_index,
                            chunk.text,
                            json.dumps(chunk.metadata),
                            self._collection_name,
                        )
                        for chunk in chunks
                    ]
                    cur.executemany(
                        """
                        INSERT INTO chunks (
                            chunk_id, document_id, chunk_index, text,
                            metadata, collection
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chunk_id) DO UPDATE
                            SET text = EXCLUDED.text,
                                metadata = EXCLUDED.metadata
                        """,
                        chunk_rows,
                        returning=False,
                    )
                    embedding_rows = [
                        (
                            chunk.chunk_id,
                            embedder.model_name,
                            embedder.dimensions,
                            vector,
                        )
                        for chunk, vector in zip(chunks, vectors)
                    ]
                    cur.executemany(
                        """
                        INSERT INTO embeddings (
                            chunk_id, model_name, dimensions, vector
                        )
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (chunk_id, model_name) DO UPDATE
                            SET vector = EXCLUDED.vector,
                                dimensions = EXCLUDED.dimensions
                        """,
                        embedding_rows,
                        returning=False,
                    )
                conn.commit()
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
            with self._pool.connection() as conn:
                self._register_vector(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT c.chunk_id, c.document_id, c.chunk_index, c.text,
                               c.metadata, 1 - (e.vector <=> %s::vector) AS score
                        FROM embeddings e
                        JOIN chunks c ON c.chunk_id = e.chunk_id
                        WHERE e.model_name = %s AND c.collection = %s
                        ORDER BY e.vector <=> %s::vector
                        LIMIT %s
                        """,
                        (
                            vector,
                            embedder.model_name,
                            self._collection_name,
                            vector,
                            top_k,
                        ),
                    )
                    rows = cur.fetchall()
            return [
                (
                    DocumentChunk(
                        chunk_id=row["chunk_id"],
                        document_id=row["document_id"],
                        chunk_index=row["chunk_index"],
                        text=row["text"],
                        metadata=row["metadata"] or {},
                    ),
                    float(row["score"]),
                )
                for row in rows
            ]
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def delete(self, chunk_ids: list[str]) -> None:
        if not chunk_ids:
            return
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM chunks WHERE chunk_id = ANY(%s) "
                        "AND collection = %s",
                        (chunk_ids, self._collection_name),
                    )
                conn.commit()
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def delete_by_document_id(self, document_id: str) -> None:
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM chunks WHERE document_id = %s AND collection = %s",
                        (document_id, self._collection_name),
                    )
                conn.commit()
        except Exception as exc:
            raise StorageError(str(exc)) from exc

    def close(self) -> None:
        self._pool.close()

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
