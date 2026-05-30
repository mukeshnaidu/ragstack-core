import re

from ragstack_core.cleaners.base_cleaner import CleanContext

# Characters to strip outright (non-printable, non-structural):
#   \x00        null byte
#   \x0B        vertical tab
#   \x0C        form feed (page break in PDFs)
#   \x1A        substitute (legacy Windows EOF marker)
#   ­      soft hyphen (invisible, causes tokenisation splits)
#   ​      zero-width space
#   ‌      zero-width non-joiner
#   ‍      zero-width joiner
#   ‎/F    left/right-to-right marks
#   ‪-‮  bidirectional embedding controls
#   ﻿      zero-width no-break space / BOM (when mid-text)
_CONTROL_CHARS = re.compile(
    r"[\x00\x0B\x0C\x1A"
    r"­​‌‍‎‏"
    r"‪-‮﻿]"
)


class ControlCharCleaner:
    """Strips invisible and non-printable control characters.

    Preserves structural whitespace (\n, \r, \t, space) so downstream
    whitespace normalization can handle those deliberately.
    """

    name = "control_char_cleaner"

    def clean(self, text: str, context: CleanContext) -> str:
        return _CONTROL_CHARS.sub("", text)
