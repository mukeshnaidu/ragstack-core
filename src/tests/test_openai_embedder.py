from unittest.mock import MagicMock, patch

import pytest

from ragstack_core.embedders.openai_embedder import OpenAIEmbedder


@pytest.fixture
def mock_openai():
    with (
        patch("openai.OpenAI") as mock_cls,
        patch("openai.AsyncOpenAI") as mock_async_cls,
    ):
        mock_client = MagicMock()
        mock_async_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_async_cls.return_value = mock_async_client
        yield mock_client, mock_async_client


def _make_response(vectors: list[list[float]]):
    response = MagicMock()
    response.data = [MagicMock(embedding=v) for v in vectors]
    return response


def test_model_name_and_dimensions(mock_openai):
    embedder = OpenAIEmbedder(api_key="test-key")
    assert embedder.model_name == "text-embedding-3-small"
    assert embedder.dimensions == 1536


def test_embed_returns_vectors(mock_openai):
    mock_client, _ = mock_openai
    mock_client.embeddings.create.return_value = _make_response([[0.1] * 1536])
    embedder = OpenAIEmbedder(api_key="test-key")
    result = embedder.embed(["hello world"])
    assert len(result) == 1
    assert len(result[0]) == 1536
    mock_client.embeddings.create.assert_called_once()


def test_embed_empty_list(mock_openai):
    embedder = OpenAIEmbedder(api_key="test-key")
    result = embedder.embed([])
    assert result == []


def test_embed_batches_large_input(mock_openai):
    mock_client, _ = mock_openai
    mock_client.embeddings.create.side_effect = [
        _make_response([[0.1] * 1536, [0.2] * 1536]),
        _make_response([[0.3] * 1536, [0.4] * 1536]),
        _make_response([[0.5] * 1536]),
    ]
    embedder = OpenAIEmbedder(api_key="test-key", batch_size=2)
    result = embedder.embed(["a", "b", "c", "d", "e"])
    assert len(result) == 5
    assert mock_client.embeddings.create.call_count == 3


def test_raises_embedding_error_on_api_failure(mock_openai):
    from ragstack_core.exceptions import EmbeddingError

    mock_client, _ = mock_openai
    mock_client.embeddings.create.side_effect = Exception("rate limit")
    embedder = OpenAIEmbedder(api_key="test-key")
    with pytest.raises(EmbeddingError, match="rate limit"):
        embedder.embed(["hello"])


def test_requires_api_key():
    import os

    os.environ.pop("OPENAI_API_KEY", None)
    with pytest.raises(ValueError, match="api_key"):
        with patch("openai.OpenAI"), patch("openai.AsyncOpenAI"):
            OpenAIEmbedder()


@pytest.mark.asyncio
async def test_embed_async_returns_vectors(mock_openai):
    _, mock_async_client = mock_openai

    async def fake_create(**kw):
        return _make_response([[0.1] * 1536])

    mock_async_client.embeddings.create = fake_create
    embedder = OpenAIEmbedder(api_key="test-key")
    result = await embedder.embed_async(["hello"])
    assert len(result) == 1
    assert len(result[0]) == 1536


@pytest.mark.asyncio
async def test_embed_async_empty_list(mock_openai):
    embedder = OpenAIEmbedder(api_key="test-key")
    result = await embedder.embed_async([])
    assert result == []
