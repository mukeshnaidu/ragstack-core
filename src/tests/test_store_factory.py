import pytest

from ragstack_core.stores.base_store import VectorStoreProtocol, VectorStoreProvider
from ragstack_core.stores.factory import create_store


def test_create_qdrant_store_returns_protocol():
    store = create_store(VectorStoreProvider.QDRANT, connection_string=":memory:")
    assert isinstance(store, VectorStoreProtocol)


def test_create_chroma_store_returns_protocol():
    store = create_store(VectorStoreProvider.CHROMA, connection_string=":memory:")
    assert isinstance(store, VectorStoreProtocol)


def test_create_store_with_collection_name():
    store = create_store(
        VectorStoreProvider.QDRANT,
        connection_string=":memory:",
        collection_name="my_docs",
    )
    assert store._collection_name == "my_docs"


def test_create_store_unknown_provider_raises():
    with pytest.raises(ValueError, match="Unknown provider"):
        create_store("bad_provider", connection_string=":memory:")  # type: ignore
