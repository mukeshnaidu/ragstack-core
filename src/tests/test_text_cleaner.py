"""
Tests for the enterprise text cleaning pipeline.

Each test is focused on a single responsibility so failures pinpoint the
exact step that regressed. The integration tests at the bottom validate
the steps work correctly as a composed pipeline.
"""

from ragstack_core.cleaners.base_cleaner import CleanContext, CleaningResult
from ragstack_core.cleaners.pipeline import TextCleaningPipeline
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
from ragstack_core.cleaners.text_cleaner import TextCleaner
from ragstack_core.models.document_block import DocumentBlock

_CTX = CleanContext()
_PDF_CTX = CleanContext(file_type="pdf")
_MD_CTX = CleanContext(file_type="md")


# ---------------------------------------------------------------------------
# Individual step tests
# ---------------------------------------------------------------------------


class TestEncodingFixer:
    def test_fixes_mojibake(self):
        # "é" encoded as UTF-8 but decoded as Latin-1 produces "Ã©"
        result = EncodingFixer().clean("CafÃ©", _CTX)
        assert result == "Café"

    def test_passthrough_clean_text(self):
        result = EncodingFixer().clean("Hello world", _CTX)
        assert result == "Hello world"


class TestUnicodeNormalizer:
    def test_nfkc_fullwidth_letters(self):
        # Full-width ASCII characters should normalise to ASCII
        result = UnicodeNormalizer().clean("ｈｅｌｌｏ", _CTX)
        assert result == "hello"

    def test_nfkc_fraction(self):
        # ½ (U+00BD) → "1⁄2" under NFKC (U+2044 fraction slash, not ASCII /)
        result = UnicodeNormalizer().clean("½", _CTX)
        assert result == "1⁄2"


class TestControlCharCleaner:
    def test_removes_null_byte(self):
        result = ControlCharCleaner().clean("hello\x00world", _CTX)
        assert "\x00" not in result
        assert "helloworld" == result

    def test_removes_form_feed(self):
        result = ControlCharCleaner().clean("page1\x0cpage2", _CTX)
        assert "\x0c" not in result

    def test_removes_zero_width_space(self):
        result = ControlCharCleaner().clean("hel​lo", _CTX)
        assert "​" not in result
        assert "hello" == result

    def test_preserves_newlines(self):
        # Structural newlines must survive
        result = ControlCharCleaner().clean("line1\nline2", _CTX)
        assert "\n" in result


class TestLigatureExpander:
    def test_fi_ligature(self):
        assert LigatureExpander().clean("ﬁle", _CTX) == "file"

    def test_oe_ligature(self):
        assert LigatureExpander().clean("œuvre", _CTX) == "oeuvre"

    def test_ae_ligature(self):
        assert LigatureExpander().clean("æsthetics", _CTX) == "aesthetics"

    def test_ff_ligature(self):
        assert LigatureExpander().clean("ﬀ", _CTX) == "ff"


class TestTypographyCleaner:
    def test_smart_double_quotes(self):
        result = TypographyCleaner().clean("“Hello”", _CTX)
        assert result == '"Hello"'

    def test_smart_single_quotes(self):
        result = TypographyCleaner().clean("‘it’s", _CTX)
        assert result == "'it's"

    def test_em_dash(self):
        result = TypographyCleaner().clean("word—word", _CTX)
        assert result == "word--word"

    def test_ellipsis(self):
        result = TypographyCleaner().clean("wait…", _CTX)
        assert result == "wait..."

    def test_non_breaking_space(self):
        result = TypographyCleaner().clean("a b", _CTX)
        assert result == "a b"


class TestHtmlTagStripper:
    def test_strips_bold_tag(self):
        result = HtmlTagStripper().clean("<b>text</b>", _CTX)
        assert result == "text"

    def test_strips_anchor_tag(self):
        result = HtmlTagStripper().clean('<a href="x">link</a>', _CTX)
        assert result == "link"

    def test_decodes_html_entity(self):
        result = HtmlTagStripper().clean("AT&amp;T", _CTX)
        assert result == "AT&T"

    def test_decodes_nbsp(self):
        result = HtmlTagStripper().clean("a&nbsp;b", _CTX)
        assert result == "a\xa0b"  # unescape gives NBSP; whitespace step collapses it

    def test_multiline_tag(self):
        result = HtmlTagStripper().clean("<div\n  class='x'>content</div>", _CTX)
        assert result == "content"


class TestMarkdownCleaner:
    def _clean(self, text: str) -> str:
        return MarkdownCleaner().clean(text, _MD_CTX)

    def test_strips_atx_heading(self):
        assert self._clean("# Heading") == "Heading"

    def test_strips_h2(self):
        assert self._clean("## Sub") == "Sub"

    def test_strips_bold(self):
        assert self._clean("**bold text**") == "bold text"

    def test_strips_italic(self):
        assert self._clean("_italic_") == "italic"

    def test_link_becomes_text(self):
        assert self._clean("[click here](https://example.com)") == "click here"

    def test_image_removed(self):
        assert self._clean("![alt](image.png)") == ""

    def test_blockquote_stripped(self):
        assert self._clean("> quoted") == "quoted"

    def test_code_block_removed(self):
        result = self._clean("```python\ncode here\n```")
        assert "code here" not in result

    def test_passthrough_non_markdown(self):
        # Non-markdown file_type should pass through unchanged
        result = MarkdownCleaner().clean("# Heading", CleanContext(file_type="txt"))
        assert result == "# Heading"


class TestPdfArtifactCleaner:
    def _clean(self, text: str) -> str:
        return PdfArtifactCleaner().clean(text, _PDF_CTX)

    def test_removes_lone_page_number(self):
        text = "Some content.\n42\nMore content."
        result = self._clean(text)
        assert "\n42\n" not in result
        assert "Some content." in result

    def test_removes_page_n(self):
        text = "Content\nPage 12\nMore"
        result = self._clean(text)
        assert "Page 12" not in result

    def test_removes_n_of_m(self):
        text = "Content\n3 of 120\nMore"
        result = self._clean(text)
        assert "3 of 120" not in result

    def test_preserves_real_content(self):
        text = "The quick brown fox jumps over the lazy dog."
        assert self._clean(text) == text

    def test_passthrough_non_pdf(self):
        text = "42\nContent"
        result = PdfArtifactCleaner().clean(text, CleanContext(file_type="txt"))
        assert "42" in result

    def test_detect_repeating_lines(self):
        blocks = [
            "COMPANY CONFIDENTIAL\nReal content A",
            "COMPANY CONFIDENTIAL\nReal content B",
            "COMPANY CONFIDENTIAL\nReal content C",
        ]
        repeating = PdfArtifactCleaner.detect_repeating_lines(blocks)
        assert "COMPANY CONFIDENTIAL" in repeating

    def test_remove_repeating(self):
        cleaner = PdfArtifactCleaner()
        text = "COMPANY CONFIDENTIAL\nActual paragraph text."
        result = cleaner.remove_repeating(text, {"COMPANY CONFIDENTIAL"})
        assert "COMPANY CONFIDENTIAL" not in result
        assert "Actual paragraph text." in result


class TestWhitespaceNormalizer:
    def _clean(self, text: str) -> str:
        return WhitespaceNormalizer().clean(text, _CTX)

    def test_collapses_multiple_spaces(self):
        assert self._clean("a    b") == "a b"

    def test_collapses_tabs(self):
        assert self._clean("a\t\tb") == "a b"

    def test_strips_trailing_space(self):
        assert self._clean("line   \nline2") == "line\nline2"

    def test_normalises_excessive_newlines(self):
        result = self._clean("para1\n\n\n\n\npara2")
        assert result == "para1\n\npara2"

    def test_preserves_paragraph_break(self):
        result = self._clean("para1\n\npara2")
        assert result == "para1\n\npara2"

    def test_strips_surrounding_whitespace(self):
        assert self._clean("  hello  ") == "hello"


class TestPiiRedactor:
    def _clean(self, text: str) -> str:
        return PiiRedactor().clean(text, _CTX)

    def test_redacts_email(self):
        result = self._clean("Contact user@example.com for help.")
        assert "user@example.com" not in result
        assert "[EMAIL]" in result

    def test_redacts_phone(self):
        result = self._clean("Call 800-555-0199 now.")
        assert "[PHONE]" in result

    def test_redacts_url(self):
        result = self._clean("Visit https://example.com/path?q=1")
        assert "https://example.com" not in result
        assert "[URL]" in result

    def test_url_masked_before_email(self):
        # An email inside a URL should not be double-masked
        result = self._clean("See https://mail.example.com/u@x.com")
        assert "[URL]" in result

    def test_custom_masks(self):
        redactor = PiiRedactor(email_mask="<EMAIL_REMOVED>")
        result = redactor.clean("hi@test.org", _CTX)
        assert "<EMAIL_REMOVED>" in result

    def test_ip_redaction_disabled_by_default(self):
        result = self._clean("Server at 192.168.1.1")
        assert "192.168.1.1" in result

    def test_ip_redaction_enabled(self):
        redactor = PiiRedactor(redact_ips=True)
        result = redactor.clean("Server at 192.168.1.1", _CTX)
        assert "192.168.1.1" not in result
        assert "[IP]" in result


# ---------------------------------------------------------------------------
# Pipeline integration tests
# ---------------------------------------------------------------------------


class TestTextCleaningPipeline:
    def test_default_pipeline_end_to_end(self):
        dirty = "CafÃ©’s ﬁne   food\x00\n\n\n\nEnjoy!"
        result = TextCleaningPipeline.default().clean(dirty)
        assert isinstance(result, CleaningResult)
        assert result.text == "Café's fine food\n\nEnjoy!"
        assert result.original_length > result.cleaned_length
        assert len(result.steps_applied) > 0

    def test_for_pdf_removes_page_numbers(self):
        text = "Introduction\n\n3\n\nThis is body text."
        result = TextCleaningPipeline.for_pdf().clean(text, _PDF_CTX)
        assert "\n3\n" not in result.text
        assert "This is body text." in result.text

    def test_for_markdown_strips_syntax(self):
        text = "# Title\n\n**Bold** and _italic_ text."
        result = TextCleaningPipeline.for_markdown().clean(text, _MD_CTX)
        assert "#" not in result.text
        assert "**" not in result.text
        assert "Title" in result.text
        assert "Bold" in result.text

    def test_with_pii_redaction(self):
        pipeline = TextCleaningPipeline.with_pii_redaction(
            TextCleaningPipeline.default()
        )
        result = pipeline.clean("Email admin@corp.com for access.")
        assert "admin@corp.com" not in result.text
        assert "[EMAIL]" in result.text

    def test_clean_block_updates_metadata(self):
        block = DocumentBlock(
            document_id="doc-1",
            block_index=0,
            text="Hello  world\x00",
            metadata={"file_type": "txt", "source": "test.txt"},
        )
        cleaned = TextCleaningPipeline.default().clean_block(block)
        assert cleaned.text == "Hello world"
        assert "cleaning" in cleaned.metadata
        assert cleaned.metadata["cleaning"]["original_length"] > 0
        assert cleaned.document_id == block.document_id
        assert cleaned.block_index == block.block_index

    def test_clean_blocks_pdf_repeating_headers(self):
        blocks = [
            DocumentBlock(
                document_id="doc-1",
                block_index=i,
                text=f"ACME CORP\nContent paragraph {i}.",
                metadata={"file_type": "pdf"},
            )
            for i in range(5)
        ]
        cleaned = TextCleaningPipeline.for_pdf().clean_blocks(blocks)
        for block in cleaned:
            assert "ACME CORP" not in block.text

    def test_steps_applied_audit_trail(self):
        result = TextCleaningPipeline.default().clean("CafÃ©\x00")
        # encoding_fixer and control_char_cleaner should be in the audit trail
        assert "encoding_fixer" in result.steps_applied

    def test_empty_string(self):
        result = TextCleaningPipeline.default().clean("")
        assert result.text == ""
        assert result.original_length == 0


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------


class TestTextCleaner:
    def test_clean_text_returns_string(self):
        cleaner = TextCleaner()
        result = cleaner.clean_text("Hello   world\x00")
        assert isinstance(result, str)
        assert result == "Hello world"

    def test_empty_string(self):
        assert TextCleaner().clean_text("") == ""

    def test_existing_whitespace_behaviour(self):
        # The original TextCleaner collapsed multiple spaces and newlines;
        # the new implementation must preserve that contract.
        result = TextCleaner().clean_text("a  b\n\n\n\nc")
        assert result == "a b\n\nc"
