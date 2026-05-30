import uuid
import pytest
import tiktoken

from ragstack_core.models.document_block import DocumentBlock
from ragstack_core.chunkers.fixed_size_chunker import FixedSizeChunker, ModelType

_ENC = tiktoken.get_encoding("cl100k_base")


def make_block(text: str) -> DocumentBlock:
    return DocumentBlock(
        document_id=str(uuid.uuid4()),
        block_index=3,
        text=text,
        metadata={"file_name": "doc.txt", "file_type": "txt", "source_path": "/doc.txt"},
    )


def long_text(num_tokens: int) -> str:
    # "token " encodes to roughly 1-2 tokens; repeat enough to exceed target
    return ("ragstack " * (num_tokens * 2))


# --- ModelType presets ---

def test_openai_embedding_preset():
    c = FixedSizeChunker(model_type=ModelType.OPENAI_EMBEDDING)
    assert c.chunk_size == 512
    assert c.overlap == 50


def test_sentence_transformer_preset():
    c = FixedSizeChunker(model_type=ModelType.SENTENCE_TRANSFORMER)
    assert c.chunk_size == 256
    assert c.overlap == 32


def test_cohere_preset():
    c = FixedSizeChunker(model_type=ModelType.COHERE)
    assert c.chunk_size == 512
    assert c.overlap == 50


def test_claude_preset():
    c = FixedSizeChunker(model_type=ModelType.CLAUDE)
    assert c.chunk_size == 1024
    assert c.overlap == 100


def test_general_preset():
    c = FixedSizeChunker(model_type=ModelType.GENERAL)
    assert c.chunk_size == 512
    assert c.overlap == 50


# --- Explicit overrides ---

def test_explicit_chunk_size_overrides_preset():
    c = FixedSizeChunker(model_type=ModelType.CLAUDE, chunk_size=200)
    assert c.chunk_size == 200
    assert c.overlap == 100  # preset overlap still used


def test_explicit_overlap_overrides_preset():
    c = FixedSizeChunker(model_type=ModelType.CLAUDE, overlap=10)
    assert c.chunk_size == 1024
    assert c.overlap == 10


# --- Construction validation ---

def test_raises_when_chunk_size_is_zero():
    with pytest.raises(ValueError):
        FixedSizeChunker(chunk_size=0)


def test_raises_when_chunk_size_is_negative():
    with pytest.raises(ValueError):
        FixedSizeChunker(chunk_size=-1)


def test_raises_when_overlap_is_negative():
    with pytest.raises(ValueError):
        FixedSizeChunker(overlap=-1)


def test_raises_when_overlap_equals_chunk_size():
    with pytest.raises(ValueError):
        FixedSizeChunker(chunk_size=100, overlap=100)


def test_raises_when_overlap_exceeds_chunk_size():
    with pytest.raises(ValueError):
        FixedSizeChunker(chunk_size=100, overlap=101)


# --- Chunking behaviour ---

def test_empty_text_yields_no_chunks():
    block = make_block("")
    chunks = list(FixedSizeChunker().chunk_block(block))
    assert chunks == []


def test_short_text_yields_single_chunk():
    block = make_block("Hello world")
    chunks = list(FixedSizeChunker().chunk_block(block))
    assert len(chunks) == 1
    assert chunks[0].text == "Hello world"


def test_long_text_yields_multiple_chunks():
    block = make_block(long_text(600))
    chunks = list(FixedSizeChunker(chunk_size=100, overlap=10).chunk_block(block))
    assert len(chunks) >= 2


def test_each_chunk_within_token_limit():
    block = make_block(long_text(600))
    chunk_size = 100
    chunks = list(FixedSizeChunker(chunk_size=chunk_size, overlap=10).chunk_block(block))
    for chunk in chunks:
        assert len(_ENC.encode(chunk.text)) <= chunk_size


def test_chunk_index_is_sequential():
    block = make_block(long_text(400))
    chunks = list(FixedSizeChunker(chunk_size=100, overlap=10).chunk_block(block))
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_document_id_consistent_across_chunks():
    block = make_block(long_text(400))
    chunks = list(FixedSizeChunker(chunk_size=100, overlap=10).chunk_block(block))
    assert all(c.document_id == block.document_id for c in chunks)


def test_chunk_ids_are_unique():
    block = make_block(long_text(400))
    chunks = list(FixedSizeChunker(chunk_size=100, overlap=10).chunk_block(block))
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_adjacent_chunks_share_overlap_tokens():
    block = make_block(long_text(400))
    chunk_size = 100
    overlap = 20
    chunks = list(FixedSizeChunker(chunk_size=chunk_size, overlap=overlap).chunk_block(block))
    assert len(chunks) >= 2

    tokens_0 = _ENC.encode(chunks[0].text)
    tokens_1 = _ENC.encode(chunks[1].text)
    assert tokens_0[-overlap:] == tokens_1[:overlap]


def test_parent_metadata_forwarded_to_chunks():
    block = make_block("Some text here")
    chunks = list(FixedSizeChunker().chunk_block(block))
    meta = chunks[0].metadata
    assert meta["file_name"] == "doc.txt"
    assert meta["file_type"] == "txt"
    assert meta["source_path"] == "/doc.txt"


def test_chunk_metadata_contains_token_count():
    block = make_block("Hello world")
    chunks = list(FixedSizeChunker().chunk_block(block))
    assert "token_count" in chunks[0].metadata
    expected = len(_ENC.encode("Hello world"))
    assert chunks[0].metadata["token_count"] == expected


def test_chunk_metadata_contains_char_count():
    block = make_block("Hello world")
    chunks = list(FixedSizeChunker().chunk_block(block))
    assert chunks[0].metadata["char_count"] == len("Hello world")


def test_chunk_metadata_contains_model_type():
    block = make_block("Hello world")
    chunks = list(FixedSizeChunker(model_type=ModelType.CLAUDE).chunk_block(block))
    assert chunks[0].metadata["model_type"] == "claude"


def test_chunk_metadata_contains_block_index():
    block = make_block("Hello world")
    chunks = list(FixedSizeChunker().chunk_block(block))
    assert chunks[0].metadata["block_index"] == block.block_index


def test_chunk_metadata_contains_chunk_size_and_overlap():
    block = make_block("Hello world")
    chunks = list(FixedSizeChunker(chunk_size=200, overlap=20).chunk_block(block))
    assert chunks[0].metadata["chunk_size"] == 200
    assert chunks[0].metadata["overlap"] == 20
