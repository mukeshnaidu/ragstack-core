"""Tests for TextLoader — load_info and load_blocks."""

import pytest
from pathlib import Path

from ragstack_core.loaders.text_loader import TextLoader
from ragstack_core.models.document_info import DocumentInfo


@pytest.fixture
def sample_txt(tmp_path: Path) -> Path:
    content = "\n".join(f"Line {i}" for i in range(100))
    p = tmp_path / "sample.txt"
    p.write_text(content, encoding="utf-8")
    return p


def test_load_info_returns_document_info(sample_txt: Path):
    loader = TextLoader(lines_per_block=50)
    info = loader.load_info(sample_txt)
    assert isinstance(info, DocumentInfo)
    assert info.file_name == "sample.txt"
    assert info.file_size_bytes > 0


def test_load_blocks_yields_correct_count(sample_txt: Path):
    loader = TextLoader(lines_per_block=50)
    info = loader.load_info(sample_txt)
    blocks = list(loader.load_blocks(sample_txt, info))
    assert len(blocks) == 2


def test_load_blocks_document_id_matches(sample_txt: Path):
    loader = TextLoader(lines_per_block=50)
    info = loader.load_info(sample_txt)
    for block in loader.load_blocks(sample_txt, info):
        assert block.document_id == info.document_id


def test_load_blocks_sequential_indices(sample_txt: Path):
    loader = TextLoader(lines_per_block=50)
    info = loader.load_info(sample_txt)
    blocks = list(loader.load_blocks(sample_txt, info))
    assert [b.block_index for b in blocks] == list(range(len(blocks)))


def test_text_loader_encoding_error(tmp_path: Path):
    p = tmp_path / "binary.txt"
    p.write_bytes(b"\x80\x81\x82\x83")
    loader = TextLoader()
    info = loader.load_info(p)
    with pytest.raises(UnicodeDecodeError):
        list(loader.load_blocks(p, info))


def test_load_info_raises_for_missing_file():
    with pytest.raises(FileNotFoundError):
        TextLoader().load_info("/nonexistent/file.txt")


def test_init_raises_for_invalid_lines_per_block():
    with pytest.raises(ValueError):
        TextLoader(lines_per_block=0)
