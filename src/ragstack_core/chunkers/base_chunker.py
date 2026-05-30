from abc import ABC, abstractmethod
from collections.abc import Iterator
from ragstack_core.models.document_block import DocumentBlock
from ragstack_core.models.document_chunk import DocumentChunk

class BaseChunker(ABC):
    
    @abstractmethod
    def chunk_block(self, block: DocumentBlock) -> Iterator[DocumentChunk]:
        pass