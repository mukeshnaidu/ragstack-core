import unicodedata
from ragstack_core.cleaners.base_cleaner import CleanContext


class UnicodeNormalizer:
    """Applies NFKC Unicode normalization.

    NFKC decomposes compatibility characters and recomposes them canonically.
    This ensures that visually identical characters (e.g. ｆｕｌｌ-ｗｉｄｔｈ letters)
    have the same byte representation, preventing duplicate embeddings for
    semantically identical tokens.
    """

    name = "unicode_normalizer"

    def clean(self, text: str, context: CleanContext) -> str:
        return unicodedata.normalize("NFKC", text)
