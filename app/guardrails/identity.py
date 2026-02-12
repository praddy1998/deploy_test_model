"""Identity handling: email hashing for audit purposes."""

from __future__ import annotations

import hashlib


def hash_email(email: str) -> str:
    """
    Normalize and hash an email address.

    - Strips whitespace
    - Lowercases
    - Returns SHA-256 hex digest
    """
    normalized = email.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
