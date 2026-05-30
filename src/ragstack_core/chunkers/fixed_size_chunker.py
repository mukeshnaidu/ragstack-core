from collections.abc import Iterator
from enum import Enum

import tiktoken

from ragstack_core.chunkers.base_chunker import BaseChunker
from ragstack_core.models.document_block import DocumentBlock
from ragstack_core.models.document_chunk import DocumentChunk

_ENCODING = tiktoken.get_encoding("cl100k_base")

_PRESETS: dict[str, dict[str, int]] = {
    "openai_embedding": {"chunk_size": 512, "overlap": 50},
    "sentence_transformer": {"chunk_size": 256, "overlap": 32},
    "cohere": {"chunk_size": 512, "overlap": 50},
    "claude": {"chunk_size": 1024, "overlap": 100},
    "general": {"chunk_size": 512, "overlap": 50},
}


class ModelType(str, Enum):
    OPENAI_EMBEDDING = "openai_embedding"
    SENTENCE_TRANSFORMER = "sentence_transformer"
    COHERE = "cohere"
    CLAUDE = "claude"
    GENERAL = "general"


class FixedSizeChunker(BaseChunker):
    def __init__(
        self,
        model_type: ModelType = ModelType.GENERAL,
        chunk_size: int | None = None,
        overlap: int | None = None,
    ) -> None:
        preset = _PRESETS[model_type.value]
        self.chunk_size = chunk_size if chunk_size is not None else preset["chunk_size"]
        self.overlap = overlap if overlap is not None else preset["overlap"]
        self._model_type = model_type

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if self.overlap < 0:
            raise ValueError("overlap must be non-negative")
        if self.overlap >= self.chunk_size:
            raise ValueError("overlap must be less than chunk_size")

    def chunk_block(self, block: DocumentBlock) -> Iterator[DocumentChunk]:
        tokens = _ENCODING.encode(block.text)
        if not tokens:
            return

        chunk_index = 0
        start = 0

        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            text = _ENCODING.decode(chunk_tokens)

            yield self._create_chunk(
                block=block,
                chunk_index=chunk_index,
                text=text,
                token_count=len(chunk_tokens),
            )

            chunk_index += 1
            if end == len(tokens):
                break
            start = end - self.overlap

    def _create_chunk(
        self,
        block: DocumentBlock,
        chunk_index: int,
        text: str,
        token_count: int,
    ) -> DocumentChunk:
        metadata = {
            **block.metadata,
            "block_index": block.block_index,
            "chunk_size": self.chunk_size,
            "overlap": self.overlap,
            "model_type": self._model_type.value,
            "token_count": token_count,
            "char_count": len(text),
        }
        return DocumentChunk(
            document_id=block.document_id,
            chunk_index=chunk_index,
            text=text,
            metadata=metadata,
        )
