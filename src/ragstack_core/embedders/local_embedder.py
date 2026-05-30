import asyncio

from ragstack_core.exceptions import MissingDependencyError

_DEFAULT_MODEL = "all-MiniLM-L6-v2"
_DEFAULT_BATCH_SIZE = 64


class LocalEmbedder:

    def __init__(
        self,
        model_name: str | None = None,
        batch_size: int | None = None,
        device: str | None = None,
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise MissingDependencyError(
                "sentence-transformers is not installed. Run: uv add 'ragstack[local]'"
            )
        self._model_name = model_name or _DEFAULT_MODEL
        self._batch_size = batch_size or _DEFAULT_BATCH_SIZE
        self._model = SentenceTransformer(
            self._model_name, device=device or "cpu"
        )
        get_dim = getattr(
            self._model, "get_embedding_dimension", None
        ) or getattr(self._model, "get_sentence_embedding_dimension")
        self._dimensions: int = get_dim()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            texts,
            batch_size=self._batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return vectors.tolist()

    async def embed_async(self, texts: list[str]) -> list[list[float]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.embed, texts)
