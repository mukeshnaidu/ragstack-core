from ragstack_core.models.document_chunk import DocumentChunk


def test_chunk_id_is_hex_string():
    chunk = DocumentChunk(document_id="doc-1", chunk_index=0, text="hello")
    assert len(chunk.chunk_id) == 16
    int(chunk.chunk_id, 16)


def test_chunk_id_is_deterministic():
    a = DocumentChunk(document_id="doc-1", chunk_index=0, text="hello")
    b = DocumentChunk(document_id="doc-1", chunk_index=0, text="hello")
    assert a.chunk_id == b.chunk_id


def test_chunk_id_differs_by_text():
    a = DocumentChunk(document_id="doc-1", chunk_index=0, text="hello")
    b = DocumentChunk(document_id="doc-1", chunk_index=0, text="world")
    assert a.chunk_id != b.chunk_id


def test_chunk_id_differs_by_index():
    a = DocumentChunk(document_id="doc-1", chunk_index=0, text="hello")
    b = DocumentChunk(document_id="doc-1", chunk_index=1, text="hello")
    assert a.chunk_id != b.chunk_id


def test_chunk_id_differs_by_document():
    a = DocumentChunk(document_id="doc-1", chunk_index=0, text="hello")
    b = DocumentChunk(document_id="doc-2", chunk_index=0, text="hello")
    assert a.chunk_id != b.chunk_id


def test_user_provided_chunk_id_preserved():
    chunk = DocumentChunk(
        document_id="doc-1", chunk_id="custom-id", chunk_index=0, text="hello"
    )
    assert chunk.chunk_id == "custom-id"
