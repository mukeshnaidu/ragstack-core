from ragstack_core.embedders.base_embedder import EmbedderProtocol, EmbeddingProvider


def test_embedding_provider_values():
    assert EmbeddingProvider.OPENAI == "openai"
    assert EmbeddingProvider.LOCAL == "local"


def test_embedder_protocol_is_runtime_checkable():
    class FakeEmbedder:
        @property
        def model_name(self) -> str:
            return "fake"

        @property
        def dimensions(self) -> int:
            return 4

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[0.1, 0.2, 0.3, 0.4] for _ in texts]

        async def embed_async(self, texts: list[str]) -> list[list[float]]:
            return self.embed(texts)

    assert isinstance(FakeEmbedder(), EmbedderProtocol)
