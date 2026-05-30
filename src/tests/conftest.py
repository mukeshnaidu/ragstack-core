"""Shared test fixtures for ragstack tests."""

import pytest
from unittest.mock import MagicMock

from ragstack_core.models.document_block import DocumentBlock
from ragstack_core.models.document_chunk import DocumentChunk


@pytest.fixture
def fake_embedder():
    """A mock embedder returning fixed 4-dimensional vectors."""
    embedder = MagicMock()
    embedder.model_name = "fake-model"
    embedder.dimensions = 4
    embedder.embed = MagicMock(side_effect=lambda texts: [[0.1, 0.2, 0.3, 0.4]] * len(texts))
    return embedder


@pytest.fixture
def sample_block():
    """A minimal DocumentBlock for testing."""
    return DocumentBlock(
        document_id="doc-1",
        block_index=0,
        text="The quick brown fox jumps over the lazy dog",
        metadata={"file_name": "test.txt", "file_type": "txt", "source_path": "/test.txt"},
    )


@pytest.fixture
def sample_chunk():
    """A minimal DocumentChunk for testing."""
    return DocumentChunk(
        document_id="doc-1",
        chunk_index=0,
        text="The quick brown fox",
        metadata={"file_type": "txt"},
    )
