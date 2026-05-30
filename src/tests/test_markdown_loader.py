import pytest

from ragstack_core.loaders.markdown_loader import MarkdownLoader


def test_load_info_returns_document_info(tmp_path):
    path = tmp_path / "doc.md"
    path.write_text("# Hello\nContent")
    info = MarkdownLoader().load_info(path)
    assert info.file_name == "doc.md"
    assert info.file_type == "md"


def test_load_blocks_splits_by_heading(tmp_path):
    path = tmp_path / "doc.md"
    path.write_text("# Section 1\nContent 1\n\n# Section 2\nContent 2")
    loader = MarkdownLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert len(blocks) == 2
    assert blocks[0].metadata["heading"] == "Section 1"
    assert blocks[1].metadata["heading"] == "Section 2"


def test_load_blocks_heading_level_in_metadata(tmp_path):
    path = tmp_path / "doc.md"
    path.write_text("# H1\ncontent\n## H2\ncontent\n### H3\ncontent")
    loader = MarkdownLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert blocks[0].metadata["heading_level"] == 1
    assert blocks[1].metadata["heading_level"] == 2
    assert blocks[2].metadata["heading_level"] == 3


def test_load_blocks_text_includes_heading_line(tmp_path):
    path = tmp_path / "doc.md"
    path.write_text("## Introduction\nSome text here")
    loader = MarkdownLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert blocks[0].text.startswith("## Introduction")
    assert "Some text here" in blocks[0].text


def test_load_blocks_preamble_before_first_heading(tmp_path):
    path = tmp_path / "doc.md"
    path.write_text("Preamble content\n\n# Section\nBody")
    loader = MarkdownLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert len(blocks) == 2
    assert blocks[0].metadata["heading"] == ""
    assert blocks[0].metadata["heading_level"] == 0
    assert "Preamble content" in blocks[0].text


def test_load_blocks_no_headings_yields_single_block(tmp_path):
    path = tmp_path / "doc.md"
    path.write_text("Just plain content\nwith no headings")
    loader = MarkdownLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert len(blocks) == 1
    assert blocks[0].metadata["heading"] == ""
    assert blocks[0].metadata["heading_level"] == 0


def test_load_blocks_section_index_sequential(tmp_path):
    path = tmp_path / "doc.md"
    path.write_text("# A\n# B\n# C")
    loader = MarkdownLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert [b.metadata["section_index"] for b in blocks] == [0, 1, 2]


def test_load_blocks_document_id_consistent(tmp_path):
    path = tmp_path / "doc.md"
    path.write_text("# A\ncontent\n# B\ncontent")
    loader = MarkdownLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert all(b.document_id == info.document_id for b in blocks)


def test_load_blocks_empty_file_yields_no_blocks(tmp_path):
    path = tmp_path / "empty.md"
    path.write_text("")
    loader = MarkdownLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert blocks == []


def test_load_info_raises_for_missing_file():
    with pytest.raises(FileNotFoundError):
        MarkdownLoader().load_info("/nonexistent/file.md")


def test_load_blocks_ignores_headings_in_code_blocks(tmp_path):
    path = tmp_path / "doc.md"
    path.write_text("# Real Heading\n```\n# Not a heading\n```\n")
    loader = MarkdownLoader()
    info = loader.load_info(path)
    blocks = list(loader.load_blocks(path, info))
    assert len(blocks) == 1
