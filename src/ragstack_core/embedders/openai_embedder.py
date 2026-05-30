import os

from ragstack_core.exceptions import EmbeddingError, MissingDependencyError

_MODEL_DIMENSIONS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}

_DEFAULT_MODEL = "text-embedding-3-small"
_DEFAULT_BATCH_SIZE = 512


class OpenAIEmbedder:
    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        batch_size: int | None = None,
    ) -> None:
        try:
            from openai import AsyncOpenAI, OpenAI
        except ImportError:
            raise MissingDependencyError(
                "openai is not installed. Run: uv add 'ragstack[openai]'"
            )
        resolved_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "OpenAI API key required: pass api_key= or set OPENAI_API_KEY env var"
            )
        self._client = OpenAI(api_key=resolved_key, max_retries=3)
        self._async_client = AsyncOpenAI(api_key=resolved_key, max_retries=3)
        self._model_name = model_name or _DEFAULT_MODEL
        self._batch_size = batch_size or _DEFAULT_BATCH_SIZE
        self._dimensions = _MODEL_DIMENSIONS.get(self._model_name, 1536)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        results: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            try:
                response = self._client.embeddings.create(
                    model=self._model_name, input=batch
                )
                results.extend(item.embedding for item in response.data)
            except Exception as exc:
                raise EmbeddingError(str(exc)) from exc
        return results

    async def embed_async(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        results: list[list[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            try:
                response = await self._async_client.embeddings.create(
                    model=self._model_name, input=batch
                )
                results.extend(item.embedding for item in response.data)
            except Exception as exc:
                raise EmbeddingError(str(exc)) from exc
        return results
