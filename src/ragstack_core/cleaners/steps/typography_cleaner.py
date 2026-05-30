from ragstack_core.cleaners.base_cleaner import CleanContext

# Map Unicode typographic characters to plain ASCII equivalents.
# Keeps punctuation semantics intact while ensuring consistent tokenisation.
_TYPOGRAPHY: dict[str, str] = {
    # Smart / curly quotes → straight quotes
    "‘": "'",  # '  left single quotation mark
    "’": "'",  # '  right single quotation mark
    "‚": "'",  # ‚  single low-9 quotation mark
    "‛": "'",  # ‛  single high-reversed-9 quotation mark
    "“": '"',  # "  left double quotation mark
    "”": '"',  # "  right double quotation mark
    "„": '"',  # „  double low-9 quotation mark
    "‟": '"',  # ‟  double high-reversed-9 quotation mark
    "‹": "<",  # ‹  single left-pointing angle quotation mark
    "›": ">",  # ›  single right-pointing angle quotation mark
    "«": '"',  # «  left-pointing double angle quotation mark
    "»": '"',  # »  right-pointing double angle quotation mark
    # Dashes → ASCII hyphens / double-hyphens
    "–": "--",  # –  en dash
    "—": "--",  # —  em dash
    "―": "--",  # ―  horizontal bar
    "‒": "-",  # ‒  figure dash
    "‐": "-",  # ‐  hyphen
    "‑": "-",  # ‑  non-breaking hyphen
    # Ellipsis
    "…": "...",  # …  horizontal ellipsis
    # Miscellaneous
    "·": ".",  # ·  middle dot
    "•": "-",  # •  bullet
    "‣": "-",  # ‣  triangular bullet
    "▪": "-",  # ▪  black small square (list bullet)
    " ": " ",  # non-breaking space → regular space
    " ": " ",  # narrow no-break space → regular space
    " ": " ",  # thin space → regular space
}

_TABLE = str.maketrans(_TYPOGRAPHY)


class TypographyCleaner:
    """Converts smart punctuation and typographic symbols to plain ASCII.

    Preserves meaning (e.g. quotes stay quotes, dashes stay dashes) while
    eliminating ambiguity for tokenisers that treat each Unicode code point
    as a distinct token.
    """

    name = "typography_cleaner"

    def clean(self, text: str, context: CleanContext) -> str:
        return text.translate(_TABLE)
