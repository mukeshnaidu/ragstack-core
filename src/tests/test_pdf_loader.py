import pytest
from pathlib import Path

from pypdf import PdfWriter

from ragstack_core.loaders.pdf_loader import PdfLoader


def make_pdf(path: Path, num_pages: int) -> None:
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=612, height=792)
    with open(path, "wb") as f:
        writer.write(f)


def test_load_info_returns_document_info(tmp_path):
    path = tmp_path / "sample.pdf"
    make_pdf(path, 1)
    info = PdfLoader().load_info(path)
    assert info.file_name == "sample.pdf"
    assert info.file_type == "pdf"


def test_load_blocks_one_block_per_page_by_default(tmp_path):
    path = tmp_path / "doc.pdf"
    make_pdf(path, 3)
    loader = PdfLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert len(blocks) == 3


def test_load_blocks_groups_pages(tmp_path):
    path = tmp_path / "doc.pdf"
    make_pdf(path, 4)
    loader = PdfLoader(pages_per_block=2)
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert len(blocks) == 2


def test_load_blocks_metadata_correct(tmp_path):
    path = tmp_path / "doc.pdf"
    make_pdf(path, 3)
    loader = PdfLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))

    assert blocks[0].metadata["start_page"] == 1
    assert blocks[0].metadata["end_page"] == 1
    assert blocks[0].metadata["total_pages"] == 3
    assert blocks[0].metadata["block_type"] == "page_group"
    assert blocks[0].metadata["pages_per_block"] == 1
    assert blocks[2].metadata["start_page"] == 3


def test_load_blocks_document_id_consistent(tmp_path):
    path = tmp_path / "doc.pdf"
    make_pdf(path, 3)
    loader = PdfLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert all(b.document_id == info.document_id for b in blocks)


def test_load_blocks_block_index_sequential(tmp_path):
    path = tmp_path / "doc.pdf"
    make_pdf(path, 3)
    loader = PdfLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert [b.block_index for b in blocks] == [0, 1, 2]


def test_load_blocks_empty_pdf_yields_no_blocks(tmp_path):
    path = tmp_path / "empty.pdf"
    make_pdf(path, 0)
    loader = PdfLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert blocks == []


def test_load_info_raises_for_missing_file():
    with pytest.raises(FileNotFoundError):
        PdfLoader().load_info("/nonexistent/file.pdf")


def test_init_raises_for_invalid_pages_per_block():
    with pytest.raises(ValueError):
        PdfLoader(pages_per_block=0)
