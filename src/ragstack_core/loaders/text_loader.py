from collections.abc import Iterator
from pathlib import Path

from ragstack_core.loaders.base_loader import BaseLoader
from ragstack_core.models.document_block import DocumentBlock
from ragstack_core.models.document_info import DocumentInfo


class TextLoader(BaseLoader):
    def __init__(self, lines_per_block: int = 50):
        if lines_per_block <= 0:
            raise ValueError("lines_per_block must be greater than 0")
        self._lines_per_block = lines_per_block

    def load_info(self, file_path: str | Path) -> DocumentInfo:
        return DocumentInfo.from_path(file_path)

    def load_blocks(
        self,
        file_path: str | Path,
        document_info: DocumentInfo,
    ) -> Iterator[DocumentBlock]:
        path = Path(file_path)

        block_lines: list[str] = []
        block_index = 0
        start_line_number: int | None = None
        current_line_number = 0

        with path.open("r", encoding="utf-8") as file:
            for line in file:
                current_line_number += 1
                clean_line = line.strip()

                if not clean_line:
                    continue

                if start_line_number is None:
                    start_line_number = current_line_number

                block_lines.append(clean_line)

                if len(block_lines) >= self._lines_per_block:
                    yield self._create_block(
                        document_info=document_info,
                        block_index=block_index,
                        block_lines=block_lines,
                        start_line_number=start_line_number,
                        end_line_number=current_line_number,
                    )

                    block_index += 1
                    block_lines = []
                    start_line_number = None

        if block_lines:
            yield self._create_block(
                document_info=document_info,
                block_index=block_index,
                block_lines=block_lines,
                start_line_number=start_line_number or 1,
                end_line_number=current_line_number,
            )

    def _create_block(
        self,
        document_info: DocumentInfo,
        block_index: int,
        block_lines: list[str],
        start_line_number: int,
        end_line_number: int,
    ) -> DocumentBlock:
        return DocumentBlock(
            document_id=document_info.document_id,
            block_index=block_index,
            text="\n".join(block_lines),
            metadata={
                "file_name": document_info.file_name,
                "file_type": document_info.file_type,
                "source_path": document_info.source_path,
                "block_type": "line_group",
                "lines_per_block": self._lines_per_block,
                "start_line_number": start_line_number,
                "end_line_number": end_line_number,
            },
        )
