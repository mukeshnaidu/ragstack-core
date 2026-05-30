from ragstack_core.cleaners.pipeline import TextCleaningPipeline


class TextCleaner:
    """Backward-compatible wrapper around TextCleaningPipeline.

    Existing code that calls TextCleaner().clean_text(text) continues to
    work unchanged. For new code, prefer using TextCleaningPipeline directly
    so you get the full CleaningResult with audit metadata.
    """

    def __init__(self) -> None:
        self._pipeline = TextCleaningPipeline.default()

    def clean_text(self, text: str) -> str:
        return self._pipeline.clean(text).text
