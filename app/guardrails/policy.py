"""Policy guardrails for detecting disallowed intent in input text."""

from __future__ import annotations

# Disallowed phrases that trigger a policy block
DISALLOWED_PHRASES: list[str] = [
    "steal credentials",
    "bypass access controls",
    "phish",
    "exfiltrate data",
]


def check_policy_block(texts: list[str]) -> bool:
    """
    Return True if any text contains a disallowed phrase.

    Matching is case-insensitive.
    """
    for text in texts:
        text_lower = text.lower()
        for phrase in DISALLOWED_PHRASES:
            if phrase in text_lower:
                return True
    return False
