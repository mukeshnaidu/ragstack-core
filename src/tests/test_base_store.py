from ragstack_core.stores.base_store import VectorStoreProtocol, VectorStoreProvider


def test_vector_store_provider_values():
    assert VectorStoreProvider.PGVECTOR == "pgvector"
    assert VectorStoreProvider.QDRANT == "qdrant"
    assert VectorStoreProvider.CHROMA == "chroma"


def test_vector_store_protocol_is_runtime_checkable():
    class FakeStore:
        def upsert(self, chunks, embedder): pass
        async def upsert_async(self, chunks, embedder): pass
        def search(self, query, embedder, top_k=5): return []
        def search_with_scores(self, query, embedder, top_k=5): return []
        async def search_async(self, query, embedder, top_k=5): return []
        async def search_with_scores_async(self, query, embedder, top_k=5): return []
        def delete(self, chunk_ids): pass
        def delete_by_document_id(self, document_id): pass
        async def delete_async(self, chunk_ids): pass
        async def delete_by_document_id_async(self, document_id): pass
        def close(self): pass

    assert isinstance(FakeStore(), VectorStoreProtocol)
