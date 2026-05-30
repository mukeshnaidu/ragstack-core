import logging
from collections.abc import Iterator
from pathlib import Path

from pypdf import PdfReader

from ragstack_core.loaders.base_loader import BaseLoader
from ragstack_core.models.document_block import DocumentBlock
from ragstack_core.models.document_info import DocumentInfo

logger = logging.getLogger(__name__)


class PdfLoader(BaseLoader):
    def __init__(self, pages_per_block: int = 1) -> None:
        if pages_per_block <= 0:
            raise ValueError("pages_per_block must be greater than 0")
        self._pages_per_block = pages_per_block

    def load_info(self, file_path: str | Path) -> DocumentInfo:
        return DocumentInfo.from_path(file_path)

    def load_blocks(
        self,
        file_path: str | Path,
        document_info: DocumentInfo,
    ) -> Iterator[DocumentBlock]:
        reader = PdfReader(str(file_path))
        total_pages = len(reader.pages)
        block_index = 0

        for start in range(0, total_pages, self._pages_per_block):
            end = min(start + self._pages_per_block, total_pages)
            texts: list[str] = []

            for page_num in range(start, end):
                try:
                    text = reader.pages[page_num].extract_text() or ""
                    texts.append(text)
                except Exception:
                    logger.warning(
                        "Failed to extract text from page %d of %s",
                        page_num + 1,
                        file_path,
                    )

            yield self._create_block(
                document_info=document_info,
                block_index=block_index,
                text="\n\n".join(texts),
                start_page=start + 1,
                end_page=end,
                total_pages=total_pages,
            )
            block_index += 1

    def _create_block(
        self,
        document_info: DocumentInfo,
        block_index: int,
        text: str,
        start_page: int,
        end_page: int,
        total_pages: int,
    ) -> DocumentBlock:
        return DocumentBlock(
            document_id=document_info.document_id,
            block_index=block_index,
            text=text,
            metadata={
                "file_name": document_info.file_name,
                "file_type": document_info.file_type,
                "source_path": document_info.source_path,
                "block_type": "page_group",
                "pages_per_block": self._pages_per_block,
                "start_page": start_page,
                "end_page": end_page,
                "total_pages": total_pages,
            },
        )
