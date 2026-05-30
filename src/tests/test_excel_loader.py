import pytest
import openpyxl
from pathlib import Path

from ragstack_core.loaders.excel_loader import ExcelLoader


def make_xlsx(path: Path, sheets: dict[str, list[list]]) -> None:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for sheet_name, rows in sheets.items():
        ws = wb.create_sheet(title=sheet_name)
        for row in rows:
            ws.append(row)
    wb.save(path)


def test_load_info_returns_document_info(tmp_path):
    path = tmp_path / "data.xlsx"
    make_xlsx(path, {"Sheet1": [["name"], ["alice"]]})
    info = ExcelLoader().load_info(path)
    assert info.file_name == "data.xlsx"
    assert info.file_type == "xlsx"


def test_load_blocks_groups_rows(tmp_path):
    path = tmp_path / "data.xlsx"
    make_xlsx(path, {"Sheet1": [["a"]] + [[str(i)] for i in range(5)]})
    loader = ExcelLoader(rows_per_block=2)
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert len(blocks) == 3


def test_load_blocks_all_sheets_processed(tmp_path):
    path = tmp_path / "data.xlsx"
    make_xlsx(path, {
        "Sheet1": [["col"], ["a"], ["b"]],
        "Sheet2": [["col"], ["c"]],
    })
    loader = ExcelLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    sheet_names = {b.metadata["sheet_name"] for b in blocks}
    assert sheet_names == {"Sheet1", "Sheet2"}
    assert len(blocks) == 2


def test_load_blocks_block_index_is_global_across_sheets(tmp_path):
    path = tmp_path / "data.xlsx"
    make_xlsx(path, {
        "Sheet1": [["col"], ["a"]],
        "Sheet2": [["col"], ["b"]],
    })
    loader = ExcelLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert [b.block_index for b in blocks] == [0, 1]


def test_load_blocks_row_text_format(tmp_path):
    path = tmp_path / "data.xlsx"
    make_xlsx(path, {"Sheet1": [["name", "age"], ["alice", 30]]})
    loader = ExcelLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert blocks[0].text == "name: alice | age: 30"


def test_load_blocks_metadata_correct(tmp_path):
    path = tmp_path / "data.xlsx"
    make_xlsx(path, {"Sheet1": [["name"], ["alice"], ["bob"]]})
    loader = ExcelLoader(rows_per_block=2)
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    meta = blocks[0].metadata
    assert meta["sheet_name"] == "Sheet1"
    assert meta["column_names"] == ["name"]
    assert meta["start_row"] == 1
    assert meta["end_row"] == 2
    assert meta["block_type"] == "row_group"


def test_load_blocks_document_id_consistent(tmp_path):
    path = tmp_path / "data.xlsx"
    make_xlsx(path, {"Sheet1": [["a"]] + [[str(i)] for i in range(5)]})
    loader = ExcelLoader(rows_per_block=2)
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert all(b.document_id == info.document_id for b in blocks)


def test_load_blocks_header_only_yields_no_blocks(tmp_path):
    path = tmp_path / "data.xlsx"
    make_xlsx(path, {"Sheet1": [["name", "age"]]})
    loader = ExcelLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert blocks == []


def test_load_blocks_empty_sheet_yields_no_blocks(tmp_path):
    path = tmp_path / "data.xlsx"
    make_xlsx(path, {"Sheet1": []})
    loader = ExcelLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert blocks == []


def test_load_info_raises_for_missing_file():
    with pytest.raises(FileNotFoundError):
        ExcelLoader().load_info("/nonexistent/file.xlsx")


def test_init_raises_for_invalid_rows_per_block():
    with pytest.raises(ValueError):
        ExcelLoader(rows_per_block=0)
