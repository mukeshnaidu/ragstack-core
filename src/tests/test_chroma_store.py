import pytest
from unittest.mock import MagicMock
from ragstack_core.models.document_chunk import DocumentChunk
from ragstack_core.stores.chroma_store import ChromaStore


@pytest.fixture
def store():
    s = ChromaStore(connection_string=":memory:", collection_name="test_collection")
    yield s
    s._client.reset()


def test_upsert_and_search(store, fake_embedder, sample_chunk):
    store.upsert([sample_chunk], fake_embedder)
    fake_embedder.embed = MagicMock(return_value=[[0.1, 0.2, 0.3, 0.4]])
    results = store.search("fox", fake_embedder, top_k=1)
    assert len(results) == 1
    assert results[0].document_id == "doc-1"
    assert results[0].text == "The quick brown fox"


def test_search_with_scores(store, fake_embedder, sample_chunk):
    store.upsert([sample_chunk], fake_embedder)
    fake_embedder.embed = MagicMock(return_value=[[0.1, 0.2, 0.3, 0.4]])
    results = store.search_with_scores("fox", fake_embedder, top_k=1)
    assert len(results) == 1
    chunk, score = results[0]
    assert chunk.document_id == "doc-1"
    assert 0.0 <= score <= 1.0


def test_upsert_is_idempotent(store, fake_embedder, sample_chunk):
    store.upsert([sample_chunk], fake_embedder)
    store.upsert([sample_chunk], fake_embedder)
    fake_embedder.embed = MagicMock(return_value=[[0.1, 0.2, 0.3, 0.4]])
    results = store.search("fox", fake_embedder, top_k=5)
    assert len(results) == 1


def test_upsert_empty_list_is_noop(store, fake_embedder):
    store.upsert([], fake_embedder)


def test_search_on_empty_index(store, fake_embedder):
    results = store.search("anything", fake_embedder, top_k=5)
    assert results == []


def test_top_k_validation(store, fake_embedder):
    with pytest.raises(ValueError, match="top_k"):
        store.search_with_scores("anything", fake_embedder, top_k=0)


def test_delete_chunks(store, fake_embedder, sample_chunk):
    store.upsert([sample_chunk], fake_embedder)
    store.delete([sample_chunk.chunk_id])
    fake_embedder.embed = MagicMock(return_value=[[0.1, 0.2, 0.3, 0.4]])
    results = store.search("fox", fake_embedder, top_k=5)
    assert len(results) == 0


def test_delete_by_document_id(store, fake_embedder, sample_chunk):
    store.upsert([sample_chunk], fake_embedder)
    store.delete_by_document_id(sample_chunk.document_id)
    fake_embedder.embed = MagicMock(return_value=[[0.1, 0.2, 0.3, 0.4]])
    results = store.search("fox", fake_embedder, top_k=5)
    assert len(results) == 0


def test_delete_empty_list_is_noop(store, fake_embedder):
    store.delete([])
