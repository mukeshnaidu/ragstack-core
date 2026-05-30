"""ragstack-core: Enterprise-grade Python RAG SDK."""

__version__ = "0.1.0"

from ragstack_core.chunkers import BaseChunker, FixedSizeChunker, ModelType
from ragstack_core.cleaners import (
    CleanContext,
    CleanerStep,
    CleaningResult,
    TextCleaningPipeline,
)
from ragstack_core.embedders import EmbedderProtocol, EmbeddingProvider, create_embedder
from ragstack_core.exceptions import (
    EmbeddingError,
    MissingDependencyError,
    StorageError,
)
from ragstack_core.loaders import (
    CsvLoader,
    ExcelLoader,
    MarkdownLoader,
    PdfLoader,
    TextLoader,
)
from ragstack_core.models.document_block import DocumentBlock
from ragstack_core.models.document_chunk import DocumentChunk
from ragstack_core.models.document_info import DocumentInfo, FileType
from ragstack_core.models.embedding_record import EmbeddingRecord
from ragstack_core.models.search_result import SearchResult
from ragstack_core.stores import VectorStoreProtocol, VectorStoreProvider, create_store

__all__ = [
    "__version__",
    "DocumentInfo",
    "FileType",
    "DocumentBlock",
    "DocumentChunk",
    "EmbeddingRecord",
    "SearchResult",
    "TextLoader",
    "PdfLoader",
    "CsvLoader",
    "ExcelLoader",
    "MarkdownLoader",
    "TextCleaningPipeline",
    "CleanContext",
    "CleaningResult",
    "CleanerStep",
    "BaseChunker",
    "FixedSizeChunker",
    "ModelType",
    "EmbedderProtocol",
    "EmbeddingProvider",
    "create_embedder",
    "VectorStoreProtocol",
    "VectorStoreProvider",
    "create_store",
    "EmbeddingError",
    "StorageError",
    "MissingDependencyError",
]
