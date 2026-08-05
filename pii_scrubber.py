"""
pii_scrubber.py
Simple regex-based PII redaction (defense-in-depth).
Redacts emails, phone numbers, SSN-like, credit-card-like, and Aadhaar-like patterns.
"""

import re

PATTERNS = [
    # Email
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL]"),
    # US-style phone
    (re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "[PHONE]"),
    # SSN-like
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    # Credit-card-like (13-19 digits with optional separators)
    (re.compile(r"\b(?:\d[ -]*?){13,19}\b"), "[CARD]"),
    # Aadhaar-like (12 digits, often space-separated)
    (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[AADHAAR]"),
]


def scrub(text: str) -> str:
    if not text:
        return text
    result = text
    for pattern, replacement in PATTERNS:
        result = pattern.sub(replacement, result)
    return result
