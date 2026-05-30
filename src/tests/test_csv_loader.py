import csv
import pytest
from pathlib import Path

from ragstack_core.loaders.csv_loader import CsvLoader


def make_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_load_info_returns_document_info(tmp_path):
    path = tmp_path / "data.csv"
    make_csv(path, [{"name": "alice"}])
    info = CsvLoader().load_info(path)
    assert info.file_name == "data.csv"
    assert info.file_type == "csv"


def test_load_blocks_groups_rows(tmp_path):
    path = tmp_path / "data.csv"
    make_csv(path, [{"a": str(i)} for i in range(5)])
    loader = CsvLoader(rows_per_block=2)
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert len(blocks) == 3


def test_load_blocks_row_text_format(tmp_path):
    path = tmp_path / "data.csv"
    make_csv(path, [{"name": "alice", "age": "30"}])
    loader = CsvLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert blocks[0].text == "name: alice | age: 30"


def test_load_blocks_metadata_correct(tmp_path):
    path = tmp_path / "data.csv"
    make_csv(path, [{"name": "alice"}, {"name": "bob"}])
    loader = CsvLoader(rows_per_block=2)
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    meta = blocks[0].metadata
    assert meta["column_names"] == ["name"]
    assert meta["start_row"] == 1
    assert meta["end_row"] == 2
    assert meta["block_type"] == "row_group"
    assert meta["rows_per_block"] == 2


def test_load_blocks_start_row_tracks_across_blocks(tmp_path):
    path = tmp_path / "data.csv"
    make_csv(path, [{"a": str(i)} for i in range(4)])
    loader = CsvLoader(rows_per_block=2)
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert blocks[0].metadata["start_row"] == 1
    assert blocks[0].metadata["end_row"] == 2
    assert blocks[1].metadata["start_row"] == 3
    assert blocks[1].metadata["end_row"] == 4


def test_load_blocks_document_id_consistent(tmp_path):
    path = tmp_path / "data.csv"
    make_csv(path, [{"a": str(i)} for i in range(5)])
    loader = CsvLoader(rows_per_block=2)
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert all(b.document_id == info.document_id for b in blocks)


def test_load_blocks_empty_file_yields_no_blocks(tmp_path):
    path = tmp_path / "empty.csv"
    make_csv(path, [])
    loader = CsvLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert blocks == []


def test_load_blocks_header_only_yields_no_blocks(tmp_path):
    path = tmp_path / "header_only.csv"
    path.write_text("name,age\n")
    loader = CsvLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert blocks == []


def test_load_info_raises_for_missing_file():
    with pytest.raises(FileNotFoundError):
        CsvLoader().load_info("/nonexistent/file.csv")


def test_init_raises_for_invalid_rows_per_block():
    with pytest.raises(ValueError):
        CsvLoader(rows_per_block=0)
