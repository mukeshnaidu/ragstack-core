import re
from collections import Counter

from ragstack_core.cleaners.base_cleaner import CleanContext

# A line that is just a number (page number), optionally surrounded by
# common decorators like "- 3 -", "Page 3", "3 of 120"
_PAGE_NUM = re.compile(
    r"^[\s\-–—]*"  # optional leading dashes/spaces
    r"(Page\s+)?"  # optional "Page " prefix
    r"\d{1,5}"  # the number itself
    r"(\s+of\s+\d{1,5})?"  # optional "of N"
    r"[\s\-–—]*$",  # optional trailing dashes/spaces
    re.IGNORECASE,
)

# Lines that look like "CHAPTER 3" or "SECTION 2.1" standalone
_CHAPTER_HEADER = re.compile(
    r"^(chapter|section|part|appendix)\s+[\dIVXivx]+[.\s]",
    re.IGNORECASE,
)

# Minimum length a line must have to be considered real content.
# Very short lines that repeat frequently are likely headers/footers.
_MIN_CONTENT_LEN = 3
# If a line appears in more than this fraction of the blocks, treat it
# as a repeating header/footer (only used by detect_and_remove_repeating).
_REPEAT_THRESHOLD = 0.4


class PdfArtifactCleaner:
    """Removes common PDF extraction artifacts.

    Handles two categories:
    1. Structural — lone page numbers, "Page N of M" lines.
    2. Repeating — headers/footers that appear on nearly every page;
       detected by frequency analysis across the full document text
       when clean_block() is called with multi-block context.

    When used via TextCleaningPipeline.clean() on a single block the
    repeating-header detection is skipped (there is only one block to
    analyse). Use the pipeline-level clean_document() for full detection.
    """

    name = "pdf_artifact_cleaner"

    def __init__(self, remove_chapter_headers: bool = False):
        self._remove_chapter_headers = remove_chapter_headers

    def clean(self, text: str, context: CleanContext) -> str:
        if context.file_type not in (None, "pdf"):
            return text

        lines = text.splitlines()
        cleaned: list[str] = []

        for line in lines:
            stripped = line.strip()

            if not stripped:
                cleaned.append(line)
                continue

            # Drop lone page-number lines
            if len(stripped) <= 20 and _PAGE_NUM.match(stripped):
                continue

            # Optionally drop standalone chapter/section headings
            if self._remove_chapter_headers and _CHAPTER_HEADER.match(stripped):
                continue

            cleaned.append(line)

        return "\n".join(cleaned)

    @staticmethod
    def detect_repeating_lines(
        blocks_text: list[str], threshold: float = _REPEAT_THRESHOLD
    ) -> set[str]:
        """Identifies lines that repeat across enough blocks to be headers/footers.

        Args:
            blocks_text: Raw text of each block in document order.
            threshold: Fraction of blocks a line must appear in to be flagged.

        Returns:
            Set of line strings to remove.
        """
        n_blocks = len(blocks_text)
        if n_blocks < 3:
            return set()

        line_counts: Counter[str] = Counter()
        for block in blocks_text:
            # Count each unique line once per block (not total occurrences)
            seen = set()
            for line in block.splitlines():
                stripped = line.strip()
                if stripped and stripped not in seen:
                    line_counts[stripped] += 1
                    seen.add(stripped)

        return {
            line
            for line, count in line_counts.items()
            if count / n_blocks >= threshold and len(line) < 120
        }

    def remove_repeating(self, text: str, repeating: set[str]) -> str:
        """Removes previously detected repeating lines from a block."""
        if not repeating:
            return text
        lines = [line for line in text.splitlines() if line.strip() not in repeating]
        return "\n".join(lines)
