import os
from unittest.mock import MagicMock

import pytest

from ragstack_core.stores.pgvector_store import PgVectorStore


@pytest.fixture
def connection_string():
    url = os.environ.get("TEST_POSTGRES_URL")
    if not url:
        pytest.skip("TEST_POSTGRES_URL not set — skipping pgvector integration tests")
    return url


def test_upsert_and_search(connection_string, fake_embedder, sample_chunk):
    store = PgVectorStore(connection_string)
    store.upsert([sample_chunk], fake_embedder)
    fake_embedder.embed = MagicMock(return_value=[[0.1, 0.2, 0.3, 0.4]])
    results = store.search("fox", fake_embedder, top_k=1)
    assert len(results) == 1
    assert results[0].document_id == "doc-1"
    assert results[0].text == "The quick brown fox"


def test_search_with_scores(connection_string, fake_embedder, sample_chunk):
    store = PgVectorStore(connection_string)
    store.upsert([sample_chunk], fake_embedder)
    fake_embedder.embed = MagicMock(return_value=[[0.1, 0.2, 0.3, 0.4]])
    results = store.search_with_scores("fox", fake_embedder, top_k=1)
    assert len(results) == 1
    chunk, score = results[0]
    assert chunk.document_id == "doc-1"
    assert 0.0 <= score <= 1.0


def test_upsert_is_idempotent(connection_string, fake_embedder, sample_chunk):
    store = PgVectorStore(connection_string)
    store.upsert([sample_chunk], fake_embedder)
    store.upsert([sample_chunk], fake_embedder)
    fake_embedder.embed = MagicMock(return_value=[[0.1, 0.2, 0.3, 0.4]])
    results = store.search("fox", fake_embedder, top_k=5)
    assert len(results) == 1


def test_top_k_validation(connection_string, fake_embedder):
    store = PgVectorStore(connection_string)
    with pytest.raises(ValueError, match="top_k"):
        store.search_with_scores("anything", fake_embedder, top_k=0)


def test_upsert_empty_list_is_noop(connection_string, fake_embedder):
    store = PgVectorStore(connection_string)
    store.upsert([], fake_embedder)
