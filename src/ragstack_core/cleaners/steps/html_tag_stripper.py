import re
from html import unescape
from ragstack_core.cleaners.base_cleaner import CleanContext

# Matches any HTML/XML tag including self-closing and multiline tags.
_TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)

# Common HTML entities that survive unescape() when malformed.
_LEFTOVER_ENTITIES = re.compile(r"&[a-zA-Z]{2,8};|&#\d{1,5};|&#x[0-9a-fA-F]{1,5};")


class HtmlTagStripper:
    """Strips HTML/XML markup and decodes HTML entities.

    Applied by default because PDF extractors and DOCX converters frequently
    embed HTML fragments. Also required before MarkdownCleaner since Markdown
    permits raw HTML.
    """

    name = "html_tag_stripper"

    def clean(self, text: str, context: CleanContext) -> str:
        text = _TAG_RE.sub("", text)
        text = unescape(text)
        # Remove any malformed entities that unescape() did not handle
        text = _LEFTOVER_ENTITIES.sub("", text)
        return text
