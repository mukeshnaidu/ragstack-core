from ragstack_core.exceptions import EmbeddingError, StorageError, MissingDependencyError


def test_embedding_error_is_exception():
    err = EmbeddingError("api failed")
    assert isinstance(err, Exception)
    assert str(err) == "api failed"


def test_storage_error_is_exception():
    err = StorageError("db failed")
    assert isinstance(err, Exception)
    assert str(err) == "db failed"


def test_missing_dependency_error_is_import_error():
    err = MissingDependencyError("chromadb not installed. Run: uv add 'ragstack[chroma]'")
    assert isinstance(err, ImportError)
