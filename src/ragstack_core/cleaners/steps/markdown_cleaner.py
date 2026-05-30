import re
from ragstack_core.cleaners.base_cleaner import CleanContext

# Order matters: process fenced blocks before inline code to avoid
# leaving backtick residue, process links before emphasis to avoid
# leaving bracket residue.

# Fenced code blocks: ```...``` or ~~~...~~~
_FENCED_CODE = re.compile(r"```[\s\S]*?```|~~~[\s\S]*?~~~", re.MULTILINE)
# Inline code: `code`
_INLINE_CODE = re.compile(r"`[^`\n]+`")
# Images: ![alt](url) — discard entirely (no readable content)
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
# Links: [text](url) → text
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
# Reference links: [text][ref] → text
_REF_LINK = re.compile(r"\[([^\]]+)\]\[[^\]]*\]")
# Setext headings (underline style)
_SETEXT_H1 = re.compile(r"^=+\s*$", re.MULTILINE)
_SETEXT_H2 = re.compile(r"^-+\s*$", re.MULTILINE)
# ATX headings: # Heading
_ATX_HEADING = re.compile(r"^#{1,6}\s+", re.MULTILINE)
# Bold/italic combinations: ***text***, **text**, *text*, ___text___, __text__, _text_
_BOLD_ITALIC = re.compile(
    r"\*{1,3}([^*\n]+)\*{1,3}"
    r"|(?<!\w)_{1,3}([^_\n]+)_{1,3}(?!\w)"
)
# Strikethrough: ~~text~~
_STRIKETHROUGH = re.compile(r"~~([^~\n]+)~~")
# Blockquote markers at line start
_BLOCKQUOTE = re.compile(r"^>+\s?", re.MULTILINE)
# Horizontal rules
_HR = re.compile(r"^(\*{3,}|-{3,}|_{3,})\s*$", re.MULTILINE)
# Unordered list markers: -, *, + at line start
_LIST_MARKER = re.compile(r"^\s*[-*+]\s+", re.MULTILINE)
# Ordered list markers: 1. 2. etc.
_ORDERED_LIST = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)
# Definition list syntax: :   term
_DEF_LIST = re.compile(r"^\s*:\s+", re.MULTILINE)
# Bare URLs (http/https)
_BARE_URL = re.compile(r"https?://\S+")


class MarkdownCleaner:
    """Strips Markdown syntax leaving only plain readable text.

    Only applied when context.file_type is 'md' or 'markdown', unless
    the caller explicitly instantiates this step for a different format.
    The step is intentionally applied after HtmlTagStripper because
    Markdown documents frequently embed raw HTML.
    """

    name = "markdown_cleaner"

    def __init__(self, strip_urls: bool = True):
        self._strip_urls = strip_urls

    def clean(self, text: str, context: CleanContext) -> str:
        # Only act on markdown sources; pass through everything else
        if context.file_type not in (None, "md", "markdown"):
            return text

        text = _FENCED_CODE.sub("", text)
        text = _INLINE_CODE.sub("", text)
        text = _IMAGE.sub("", text)
        text = _LINK.sub(r"\1", text)
        text = _REF_LINK.sub(r"\1", text)
        text = _SETEXT_H1.sub("", text)
        text = _SETEXT_H2.sub("", text)
        text = _ATX_HEADING.sub("", text)
        text = _BOLD_ITALIC.sub(lambda m: m.group(1) or m.group(2), text)
        text = _STRIKETHROUGH.sub(r"\1", text)
        text = _BLOCKQUOTE.sub("", text)
        text = _HR.sub("", text)
        text = _LIST_MARKER.sub("", text)
        text = _ORDERED_LIST.sub("", text)
        text = _DEF_LIST.sub("", text)
        if self._strip_urls:
            text = _BARE_URL.sub("", text)
        return text
