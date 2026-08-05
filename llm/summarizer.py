"""
summarizer.py
Local, deterministic extractive summarizer.
Scores sentences by word frequency (classic TF approach) and returns the top-N.
No external API, no model download.
"""

import re
from collections import Counter
from typing import List


def _split_sentences(text: str) -> List[str]:
    # Simple sentence splitter
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 20]


def _tokenize(sentence: str) -> List[str]:
    return re.findall(r"\b[a-z]{3,}\b", sentence.lower())


def summarize(text: str, max_sentences: int = 8) -> str:
    """
    Extractive summary: rank sentences by average word frequency
    and return the highest-scoring ones in original order.
    """
    if not text or not text.strip():
        return "No document text available for summarization."

    sentences = _split_sentences(text)
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    # Global word frequencies (ignore very common stop-ish words lightly)
    all_tokens = []
    for s in sentences:
        all_tokens.extend(_tokenize(s))
    if not all_tokens:
        return " ".join(sentences[:max_sentences])

    freq = Counter(all_tokens)
    # Down-weight the most common words a bit
    max_f = max(freq.values()) if freq else 1
    for w in list(freq):
        if freq[w] > max_f * 0.6:
            freq[w] *= 0.3

    # Score each sentence
    scored = []
    for i, s in enumerate(sentences):
        tokens = _tokenize(s)
        if not tokens:
            score = 0.0
        else:
            score = sum(freq.get(t, 0) for t in tokens) / len(tokens)
        scored.append((score, i, s))

    # Keep top-N by score, then restore original order
    top = sorted(scored, key=lambda x: x[0], reverse=True)[:max_sentences]
    top_sorted = sorted(top, key=lambda x: x[1])
    return " ".join(s for _, _, s in top_sorted)
