import re

from ragstack_core.cleaners.base_cleaner import CleanContext

# RFC 5322-simplified email pattern — covers the vast majority of real addresses
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")

# E.164 and common national formats:
#   +1-800-555-0199  (800) 555-0199  800.555.0199  8005550199
_PHONE = re.compile(
    r"(?<!\d)"  # no digit before
    r"(\+?\d{1,3}[\s\-.]?)?"  # optional country code
    r"(\(?\d{3}\)?[\s\-.]?)"  # area code
    r"(\d{3}[\s\-.]?)"  # exchange
    r"(\d{4})"  # subscriber
    r"(?!\d)"  # no digit after
)

# URLs: http, https, ftp
_URL = re.compile(
    r"https?://[^\s\"'<>]+"
    r"|ftp://[^\s\"'<>]+"
)

# IPv4 addresses
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


class PiiRedactor:
    """Replaces personally-identifiable information with labelled placeholders.

    Disabled by default in all preset pipelines. Enable via:

        pipeline = TextCleaningPipeline.with_pii_redaction(
            TextCleaningPipeline.default()
        )

    Masks are configurable so downstream systems can distinguish redacted
    spans if needed (e.g. '[EMAIL]' vs '<EMAIL_REDACTED>').
    """

    name = "pii_redactor"

    def __init__(
        self,
        email_mask: str = "[EMAIL]",
        phone_mask: str = "[PHONE]",
        url_mask: str = "[URL]",
        ip_mask: str = "[IP]",
        redact_emails: bool = True,
        redact_phones: bool = True,
        redact_urls: bool = True,
        redact_ips: bool = False,
    ):
        self._email_mask = email_mask
        self._phone_mask = phone_mask
        self._url_mask = url_mask
        self._ip_mask = ip_mask
        self._redact_emails = redact_emails
        self._redact_phones = redact_phones
        self._redact_urls = redact_urls
        self._redact_ips = redact_ips

    def clean(self, text: str, context: CleanContext) -> str:
        # URLs before emails so "user@host" inside a URL isn't double-masked
        if self._redact_urls:
            text = _URL.sub(self._url_mask, text)
        if self._redact_emails:
            text = _EMAIL.sub(self._email_mask, text)
        if self._redact_phones:
            text = _PHONE.sub(self._phone_mask, text)
        if self._redact_ips:
            text = _IPV4.sub(self._ip_mask, text)
        return text
