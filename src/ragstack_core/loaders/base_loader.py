from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from ragstack_core.models.document_block import DocumentBlock
from ragstack_core.models.document_info import DocumentInfo


class BaseLoader(ABC):
    @abstractmethod
    def load_info(self, file_path: str | Path) -> DocumentInfo:
        pass

    @abstractmethod
    def load_blocks(
        self,
        file_path: str | Path,
        document_info: DocumentInfo,
    ) -> Iterator[DocumentBlock]:
        pass
