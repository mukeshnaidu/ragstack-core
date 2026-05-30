from datetime import datetime
from ragstack_core.models.embedding_record import EmbeddingRecord
from ragstack_core.models.search_result import SearchResult
from ragstack_core.models.document_chunk import DocumentChunk


def test_embedding_record_fields():
    record = EmbeddingRecord(
        chunk_id="abc-123",
        model_name="text-embedding-3-small",
        dimensions=1536,
        vector=[0.1, 0.2, 0.3],
    )
    assert record.chunk_id == "abc-123"
    assert record.dimensions == 1536
    assert isinstance(record.created_at, datetime)


def test_search_result_without_score():
    chunk = DocumentChunk(document_id="doc1", chunk_index=0, text="hello")
    result = SearchResult(chunk=chunk)
    assert result.score is None


def test_search_result_with_score():
    chunk = DocumentChunk(document_id="doc1", chunk_index=0, text="hello")
    result = SearchResult(chunk=chunk, score=0.92)
    assert result.score == 0.92
