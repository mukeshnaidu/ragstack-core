import asyncio

import pytest

from ragstack_core.embedders.local_embedder import LocalEmbedder


@pytest.fixture(scope="module")
def embedder():
    return LocalEmbedder()


def test_model_name(embedder):
    assert embedder.model_name == "all-MiniLM-L6-v2"


def test_dimensions(embedder):
    assert embedder.dimensions == 384


def test_embed_single_text(embedder):
    result = embedder.embed(["hello world"])
    assert len(result) == 1
    assert len(result[0]) == 384
    assert all(isinstance(v, float) for v in result[0])


def test_embed_multiple_texts(embedder):
    result = embedder.embed(["hello", "world", "foo"])
    assert len(result) == 3
    assert all(len(v) == 384 for v in result)


def test_embed_empty_list_returns_empty(embedder):
    result = embedder.embed([])
    assert result == []


def test_embed_async(embedder):
    result = asyncio.run(embedder.embed_async(["hello"]))
    assert len(result) == 1
    assert len(result[0]) == 384
