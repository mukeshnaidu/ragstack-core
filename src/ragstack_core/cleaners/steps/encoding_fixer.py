import ftfy

from ragstack_core.cleaners.base_cleaner import CleanContext


class EncodingFixer:
    """Repairs mojibake and removes byte-order marks using ftfy.

    Mojibake example: "Ã©" (UTF-8 bytes decoded as Latin-1) → "é"
    This is common in PDFs and older Word documents extracted by parsers.
    """

    name = "encoding_fixer"

    def clean(self, text: str, context: CleanContext) -> str:
        return ftfy.fix_text(text)
