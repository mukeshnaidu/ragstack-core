from abc import ABC,abstractmethod
from ragstack_core.models.document_info import DocumentInfo
from ragstack_core.models.document_block import DocumentBlock
from pathlib import Path
from collections.abc import Iterator


class BaseLoader(ABC):

    @abstractmethod
    def load_info(
        self, 
        file_path: str | Path
    ) -> DocumentInfo:
        pass

    @abstractmethod
    def load_blocks(
        self, 
        file_path: str | Path,
        document_info: DocumentInfo,
    ) -> Iterator[DocumentBlock]:
        pass