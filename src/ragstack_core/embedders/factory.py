from ragstack_core.embedders.base_embedder import EmbedderProtocol, EmbeddingProvider


def create_embedder(
    provider: EmbeddingProvider,
    model_name: str | None = None,
    batch_size: int | None = None,
    **kwargs,
) -> EmbedderProtocol:
    match provider:
        case EmbeddingProvider.OPENAI:
            from ragstack_core.embedders.openai_embedder import OpenAIEmbedder

            return OpenAIEmbedder(
                model_name=model_name, batch_size=batch_size, **kwargs
            )
        case EmbeddingProvider.LOCAL:
            from ragstack_core.embedders.local_embedder import LocalEmbedder

            return LocalEmbedder(model_name=model_name, batch_size=batch_size, **kwargs)
        case _:
            raise ValueError(f"Unknown provider: {provider!r}")
