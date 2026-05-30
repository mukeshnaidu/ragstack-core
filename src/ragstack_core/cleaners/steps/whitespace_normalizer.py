import re
from ragstack_core.cleaners.base_cleaner import CleanContext

_MULTI_SPACE = re.compile(r"[ \t]+")
_MULTI_NEWLINE = re.compile(r"\n{3,}")
_TRAILING_SPACE = re.compile(r"[ \t]+$", re.MULTILINE)


class WhitespaceNormalizer:
    """Normalizes all forms of whitespace to a consistent representation.

    Applied last in the pipeline so earlier steps can leave structural
    newlines intact (e.g. paragraph breaks) and this step tidies them.

    Rules applied (in order):
      1. Collapse multiple spaces/tabs on a line to a single space.
      2. Strip trailing spaces from every line.
      3. Collapse three or more consecutive newlines to exactly two
         (preserving paragraph structure for downstream chunkers).
      4. Strip leading and trailing whitespace from the entire text.
    """

    name = "whitespace_normalizer"

    def clean(self, text: str, context: CleanContext) -> str:
        text = _MULTI_SPACE.sub(" ", text)
        text = _TRAILING_SPACE.sub("", text)
        text = _MULTI_NEWLINE.sub("\n\n", text)
        return text.strip()
