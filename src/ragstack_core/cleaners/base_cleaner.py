from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


class CleanContext(BaseModel):
    """Carries source metadata so steps can make file-type-aware decisions."""

    file_type: str | None = None  # "pdf", "txt", "md", "csv", "xlsx", "docx"
    metadata: dict[str, Any] = {}


class CleaningResult(BaseModel):
    """Returned by TextCleaningPipeline.clean() — includes audit trail."""

    text: str
    original_length: int
    cleaned_length: int
    steps_applied: list[str]


@runtime_checkable
class CleanerStep(Protocol):
    """Protocol every cleaning step must satisfy."""

    name: str

    def clean(self, text: str, context: CleanContext) -> str: ...
