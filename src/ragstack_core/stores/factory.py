from ragstack_core.stores.base_store import VectorStoreProtocol, VectorStoreProvider


def create_store(
    provider: VectorStoreProvider,
    connection_string: str,
    collection_name: str = "ragstack",
    **kwargs,
) -> VectorStoreProtocol:
    match provider:
        case VectorStoreProvider.PGVECTOR:
            from ragstack_core.stores.pgvector_store import PgVectorStore

            return PgVectorStore(
                connection_string=connection_string,
                collection_name=collection_name,
                **kwargs,
            )
        case VectorStoreProvider.QDRANT:
            from ragstack_core.stores.qdrant_store import QdrantStore

            return QdrantStore(
                connection_string=connection_string,
                collection_name=collection_name,
                **kwargs,
            )
        case VectorStoreProvider.CHROMA:
            from ragstack_core.stores.chroma_store import ChromaStore

            return ChromaStore(
                connection_string=connection_string,
                collection_name=collection_name,
                **kwargs,
            )
        case _:
            raise ValueError(f"Unknown provider: {provider!r}")
