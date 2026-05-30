from ragstack_core.cleaners.base_cleaner import CleanContext

# Typographic ligatures that PDF extractors emit as single characters.
# Without expansion, "ﬁle" and "file" would have different embeddings.
_LIGATURES: dict[str, str] = {
    "ﬀ": "ff",  # ﬀ
    "ﬁ": "fi",  # ﬁ
    "ﬂ": "fl",  # ﬂ
    "ﬃ": "ffi",  # ﬃ
    "ﬄ": "ffl",  # ﬄ
    "ﬅ": "st",  # ﬅ
    "ﬆ": "st",  # ﬆ
    "Œ": "OE",  # Œ
    "œ": "oe",  # œ
    "Æ": "AE",  # Æ
    "æ": "ae",  # æ
    "Ĳ": "IJ",  # Ĳ
    "ĳ": "ij",  # ĳ
    "ẞ": "SS",  # ẞ (capital sharp s)
    "ß": "ss",  # ß
}

_TABLE = str.maketrans(_LIGATURES)


class LigatureExpander:
    """Expands typographic ligatures to their ASCII equivalents.

    Runs after UnicodeNormalizer because NFKC already handles some
    compatibility ligatures; this catches the ones that survive normalization.
    """

    name = "ligature_expander"

    def clean(self, text: str, context: CleanContext) -> str:
        return text.translate(_TABLE)
