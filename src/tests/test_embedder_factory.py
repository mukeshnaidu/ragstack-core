import pytest
from unittest.mock import patch, MagicMock
from ragstack_core.embedders.base_embedder import EmbedderProtocol, EmbeddingProvider
from ragstack_core.embedders.factory import create_embedder


def test_create_openai_embedder_returns_protocol():
    with patch("openai.OpenAI"), \
         patch("openai.AsyncOpenAI"):
        embedder = create_embedder(EmbeddingProvider.OPENAI, api_key="test-key")
    assert isinstance(embedder, EmbedderProtocol)


def test_create_local_embedder_returns_protocol():
    with patch("sentence_transformers.SentenceTransformer") as mock_st:
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.get_embedding_dimension.return_value = 384
        mock_st.return_value = mock_model
        embedder = create_embedder(EmbeddingProvider.LOCAL)
    assert isinstance(embedder, EmbedderProtocol)


def test_create_embedder_with_model_name_override():
    with patch("openai.OpenAI"), \
         patch("openai.AsyncOpenAI"):
        embedder = create_embedder(
            EmbeddingProvider.OPENAI,
            api_key="test-key",
            model_name="text-embedding-3-large",
        )
    assert embedder.model_name == "text-embedding-3-large"
    assert embedder.dimensions == 3072


def test_create_embedder_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        create_embedder("unknown_provider")  # type: ignore
