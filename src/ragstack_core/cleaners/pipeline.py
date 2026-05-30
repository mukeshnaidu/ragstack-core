from ragstack_core.cleaners.base_cleaner import (
    CleanContext,
    CleanerStep,
    CleaningResult,
)
from ragstack_core.cleaners.steps import (
    ControlCharCleaner,
    EncodingFixer,
    HtmlTagStripper,
    LigatureExpander,
    MarkdownCleaner,
    PdfArtifactCleaner,
    PiiRedactor,
    TypographyCleaner,
    UnicodeNormalizer,
    WhitespaceNormalizer,
)
from ragstack_core.models.document_block import DocumentBlock


class TextCleaningPipeline:
    """Composable pipeline that runs text through an ordered list of CleanerStep
    instances.

    Usage — preset factories:
        pipeline = TextCleaningPipeline.for_pdf()
        result   = pipeline.clean(raw_text, CleanContext(file_type="pdf"))

    Usage — custom pipeline:
        pipeline = TextCleaningPipeline([
            EncodingFixer(),
            WhitespaceNormalizer(),
        ])

    Usage — integrate with the loader layer:
        block = pipeline.clean_block(document_block)

    The pipeline is stateless after construction; the same instance can be
    shared across threads.
    """

    def __init__(self, steps: list[CleanerStep]):
        self._steps = steps

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def clean(self, text: str, context: CleanContext | None = None) -> CleaningResult:
        """Run all steps and return a CleaningResult with audit metadata."""
        ctx = context or CleanContext()
        original_length = len(text)
        steps_applied: list[str] = []

        for step in self._steps:
            before = text
            text = step.clean(text, ctx)
            if text != before:
                steps_applied.append(step.name)

        return CleaningResult(
            text=text,
            original_length=original_length,
            cleaned_length=len(text),
            steps_applied=steps_applied,
        )

    def clean_block(self, block: DocumentBlock) -> DocumentBlock:
        """Clean a DocumentBlock in-place (returns a new immutable instance).

        Reads file_type from block.metadata so the correct type-specific
        steps activate automatically.
        """
        file_type = block.metadata.get("file_type")
        context = CleanContext(file_type=file_type, metadata=dict(block.metadata))

        result = self.clean(block.text, context)

        updated_metadata = {
            **block.metadata,
            "cleaning": {
                "original_length": result.original_length,
                "cleaned_length": result.cleaned_length,
                "steps_applied": result.steps_applied,
            },
        }

        return DocumentBlock(
            document_id=block.document_id,
            block_index=block.block_index,
            text=result.text,
            metadata=updated_metadata,
        )

    def clean_blocks(self, blocks: list[DocumentBlock]) -> list[DocumentBlock]:
        """Clean a full list of blocks.

        For PDF documents this also runs repeating-header detection across
        the entire set before applying per-block cleaning.
        """
        if not blocks:
            return []

        cleaned = [self.clean_block(block) for block in blocks]

        file_type = blocks[0].metadata.get("file_type")
        if file_type == "pdf":
            pdf_step = next(
                (s for s in self._steps if isinstance(s, PdfArtifactCleaner)), None
            )
            if pdf_step is not None:
                repeating_lines = PdfArtifactCleaner.detect_repeating_lines(
                    [b.text for b in cleaned]
                )
                if repeating_lines:
                    cleaned = [
                        DocumentBlock(
                            document_id=cb.document_id,
                            block_index=cb.block_index,
                            text=pdf_step.remove_repeating(cb.text, repeating_lines),
                            metadata=cb.metadata,
                        )
                        for cb in cleaned
                    ]

        return cleaned

    # ------------------------------------------------------------------
    # Preset factories — opinionated defaults for each file type
    # ------------------------------------------------------------------

    @classmethod
    def default(cls) -> "TextCleaningPipeline":
        """General-purpose pipeline for plain text and unknown sources.

        Order rationale:
          1. Fix encoding first so all subsequent steps operate on valid text.
          2. Normalize Unicode so character comparisons are stable.
          3. Remove invisible control characters (do not affect whitespace logic).
          4. Expand ligatures — must be after Unicode normalization.
          5. Normalize typography — must be after ligature expansion.
          6. Normalize whitespace last — consolidates any spaces left by prior steps.
        """
        return cls(
            [
                EncodingFixer(),
                UnicodeNormalizer(),
                ControlCharCleaner(),
                LigatureExpander(),
                TypographyCleaner(),
                WhitespaceNormalizer(),
            ]
        )

    @classmethod
    def for_pdf(cls) -> "TextCleaningPipeline":
        """Pipeline tuned for text extracted from PDF files.

        Adds HtmlTagStripper (some PDF extractors emit HTML fragments) and
        PdfArtifactCleaner (page numbers, running headers/footers) on top of
        the default steps.
        """
        return cls(
            [
                EncodingFixer(),
                UnicodeNormalizer(),
                ControlCharCleaner(),
                LigatureExpander(),
                TypographyCleaner(),
                HtmlTagStripper(),
                PdfArtifactCleaner(),
                WhitespaceNormalizer(),
            ]
        )

    @classmethod
    def for_markdown(cls) -> "TextCleaningPipeline":
        """Pipeline tuned for Markdown documents.

        Markdown permits embedded HTML, so HtmlTagStripper runs before
        MarkdownCleaner. MarkdownCleaner's file_type guard ensures it only
        activates when context.file_type is 'md' or 'markdown'.
        """
        return cls(
            [
                EncodingFixer(),
                UnicodeNormalizer(),
                ControlCharCleaner(),
                LigatureExpander(),
                TypographyCleaner(),
                HtmlTagStripper(),
                MarkdownCleaner(),
                WhitespaceNormalizer(),
            ]
        )

    @classmethod
    def for_tabular(cls) -> "TextCleaningPipeline":
        """Pipeline for text cells extracted from CSV or Excel files.

        Tabular data rarely contains markup; the focus is on encoding repair,
        typography normalisation, and whitespace cleanup.
        """
        return cls(
            [
                EncodingFixer(),
                UnicodeNormalizer(),
                ControlCharCleaner(),
                LigatureExpander(),
                TypographyCleaner(),
                WhitespaceNormalizer(),
            ]
        )

    @classmethod
    def for_docx(cls) -> "TextCleaningPipeline":
        """Pipeline for text extracted from Word (.docx) documents.

        DOCX extractors sometimes emit residual HTML/XML fragments and smart
        punctuation from the Office XML schema.
        """
        return cls(
            [
                EncodingFixer(),
                UnicodeNormalizer(),
                ControlCharCleaner(),
                LigatureExpander(),
                TypographyCleaner(),
                HtmlTagStripper(),
                WhitespaceNormalizer(),
            ]
        )

    @classmethod
    def with_pii_redaction(
        cls,
        base: "TextCleaningPipeline",
        redactor: PiiRedactor | None = None,
    ) -> "TextCleaningPipeline":
        """Append PII redaction to any existing pipeline.

        Example:
            pipeline = TextCleaningPipeline.with_pii_redaction(
                TextCleaningPipeline.for_pdf(),
                PiiRedactor(redact_ips=True),
            )
        """
        pii = redactor or PiiRedactor()
        steps = list(base._steps)

        # Insert PII redactor before whitespace normalizer (last step)
        if steps and steps[-1].name == "whitespace_normalizer":
            steps.insert(-1, pii)
        else:
            steps.append(pii)

        return cls(steps)
