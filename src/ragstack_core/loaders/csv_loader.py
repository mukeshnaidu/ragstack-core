import csv
from collections.abc import Iterator
from pathlib import Path

from ragstack_core.loaders.base_loader import BaseLoader
from ragstack_core.models.document_block import DocumentBlock
from ragstack_core.models.document_info import DocumentInfo


class CsvLoader(BaseLoader):
    def __init__(self, rows_per_block: int = 100, encoding: str = "utf-8") -> None:
        if rows_per_block <= 0:
            raise ValueError("rows_per_block must be greater than 0")
        self._rows_per_block = rows_per_block
        self._encoding = encoding

    def load_info(self, file_path: str | Path) -> DocumentInfo:
        return DocumentInfo.from_path(file_path)

    def load_blocks(
        self,
        file_path: str | Path,
        document_info: DocumentInfo,
    ) -> Iterator[DocumentBlock]:
        path = Path(file_path)
        with path.open("r", encoding=self._encoding, newline="") as f:
            reader = csv.DictReader(f)
            column_names = reader.fieldnames
            if not column_names:
                return

            column_names = list(column_names)
            block_rows: list[str] = []
            block_index = 0
            start_row = 1
            current_row = 0

            for row in reader:
                current_row += 1
                block_rows.append(" | ".join(f"{k}: {v}" for k, v in row.items()))

                if len(block_rows) >= self._rows_per_block:
                    yield self._create_block(
                        document_info=document_info,
                        block_index=block_index,
                        block_rows=block_rows,
                        column_names=column_names,
                        start_row=start_row,
                        end_row=current_row,
                    )
                    block_index += 1
                    block_rows = []
                    start_row = current_row + 1

            if block_rows:
                yield self._create_block(
                    document_info=document_info,
                    block_index=block_index,
                    block_rows=block_rows,
                    column_names=column_names,
                    start_row=start_row,
                    end_row=current_row,
                )

    def _create_block(
        self,
        document_info: DocumentInfo,
        block_index: int,
        block_rows: list[str],
        column_names: list[str],
        start_row: int,
        end_row: int,
    ) -> DocumentBlock:
        return DocumentBlock(
            document_id=document_info.document_id,
            block_index=block_index,
            text="\n".join(block_rows),
            metadata={
                "file_name": document_info.file_name,
                "file_type": document_info.file_type,
                "source_path": document_info.source_path,
                "block_type": "row_group",
                "rows_per_block": self._rows_per_block,
                "start_row": start_row,
                "end_row": end_row,
                "column_names": column_names,
            },
        )
