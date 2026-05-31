"""
cleaning.py — Demonstrates TextCleaningPipeline presets.

No file I/O needed. A DocumentBlock is constructed manually with intentionally
dirty text and run through three pipeline presets.
"""
from ragstack_core.cleaners.base_cleaner import CleanContext
from ragstack_core.cleaners.pipeline import TextCleaningPipeline
from ragstack_core.models.document_block import DocumentBlock

DIRTY_TEXT = (
    "<p>The  quick\t\tbrown  fox</p>\n"
    "<b>jumped</b> over the lazy dog.\n"
    "He said: “Hello!” and she replied: ‘Fine.’\n"
    "Coeﬃcient of reﬂection is 0.85.\n"
    "   Extra   spaces   everywhere.   \n"
)


def _separator(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print("─" * 60)


def demo_preset(
    name: str,
    pipeline: TextCleaningPipeline,
    context: CleanContext | None = None,
) -> None:
    result = pipeline.clean(DIRTY_TEXT, context)
    print(f"\nPreset: {name}")
    print(f"  original_length : {result.original_length}")
    print(f"  cleaned_length  : {result.cleaned_length}")
    print(f"  steps_applied   : {result.steps_applied}")
    print(f"  cleaned text    : {result.text!r}")


def demo_clean_block() -> None:
    _separator("clean_block() — operates directly on a DocumentBlock")
    block = DocumentBlock(
        document_id="doc-001",
        block_index=0,
        text=DIRTY_TEXT,
        metadata={"file_type": "txt", "source_path": "/fake/path.txt"},
    )
    pipeline = TextCleaningPipeline.default()
    cleaned_block = pipeline.clean_block(block)
    print(f"  original text  : {block.text!r}")
    print(f"  cleaned text   : {cleaned_block.text!r}")
    print(f"  cleaning audit : {cleaned_block.metadata['cleaning']}")


if __name__ == "__main__":
    _separator("Dirty input text")
    print(repr(DIRTY_TEXT))

    _separator("Pipeline Presets")
    demo_preset("default()", TextCleaningPipeline.default())
    demo_preset(
        "for_pdf()",
        TextCleaningPipeline.for_pdf(),
        CleanContext(file_type="pdf"),
    )
    demo_preset(
        "for_markdown()",
        TextCleaningPipeline.for_markdown(),
        CleanContext(file_type="md"),
    )

    demo_clean_block()
