from enum import Enum
from typing import Protocol, runtime_checkable


class EmbeddingProvider(str, Enum):
    OPENAI = "openai"
    LOCAL  = "local"


@runtime_checkable
class EmbedderProtocol(Protocol):
    @property
    def model_name(self) -> str: ...

    @property
    def dimensions(self) -> int: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...

    async def embed_async(self, texts: list[str]) -> list[list[float]]: ...

