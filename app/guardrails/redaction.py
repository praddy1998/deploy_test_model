"""PII and secret redaction utilities."""

from __future__ import annotations

import re

# Email pattern
_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# Token / API key patterns (e.g., sk-..., sk_live_..., Bearer ..., key-...)
_TOKEN_RE = re.compile(
    r"(?:sk|api|key|token|bearer|secret)[\-_]?[a-zA-Z0-9_\-]{16,}",
    re.IGNORECASE,
)


def redact_pii(text: str) -> str:
    """Redact email addresses and token-like strings from text."""
    text = _EMAIL_RE.sub("[EMAIL_REDACTED]", text)
    text = _TOKEN_RE.sub("[TOKEN_REDACTED]", text)
    return text


def redact_for_logging(data: str) -> str:
    """Apply all redaction rules for safe logging."""
    return redact_pii(data)
