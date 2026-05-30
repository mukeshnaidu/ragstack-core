from ragstack_core.chunkers.base_chunker import BaseChunker


def test_base_chunker_importable_from_base_chunker_module():
    assert BaseChunker is not None
