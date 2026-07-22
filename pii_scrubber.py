"""
pii_scrubber.py
Lightweight regex-based PII redaction, run on all text BEFORE it is sent
to the Anthropic API (summarizer.py / insight_generator.py). This is not
a substitute for a proper DLP system, but it catches the common cases:
emails, phone numbers, credit-card-like numbers, and SSN-like numbers.
"""
import re

PATTERNS = {
    "EMAIL": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "PHONE": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "AADHAAR": re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"),  # common in Indian business docs
}


def scrub_text(text: str, replace_with_label: bool = True) -> tuple[str, dict]:
    """
    Redact common PII patterns from a block of text.

    Returns (scrubbed_text, counts) where counts is a dict like
    {"EMAIL": 2, "PHONE": 1} so you can log what was redacted without
    logging the values themselves.
    """
    scrubbed = text
    counts = {}

    for label, pattern in PATTERNS.items():
        matches = pattern.findall(scrubbed)
        if matches:
            counts[label] = len(matches)
            replacement = f"[REDACTED_{label}]" if replace_with_label else "[REDACTED]"
            scrubbed = pattern.sub(replacement, scrubbed)

    return scrubbed, counts


def scrub_dataframe_column(df, column: str):
    """Scrub PII out of a specific text column in a DataFrame (e.g. free-text notes)."""
    df = df.copy()
    total_counts = {}

    def _scrub(val):
        if not isinstance(val, str):
            return val
        cleaned, counts = scrub_text(val)
        for k, v in counts.items():
            total_counts[k] = total_counts.get(k, 0) + v
        return cleaned

    df[column] = df[column].apply(_scrub)
    return df, total_counts


if __name__ == "__main__":
    sample = "Contact John at john.doe@example.com or 555-123-4567. Card: 4111 1111 1111 1111."
    clean, counts = scrub_text(sample)
    print(clean)
    print(counts)
