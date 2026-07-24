"""
local_summarizer.py
Extractive text summarization using pure Python — no external API,
no API key, no network call. Scores sentences by word frequency
(a lightweight, classic technique) and picks the highest-scoring ones,
preserving their original order.
"""
import re

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "for", "with", "by", "from", "as",
    "and", "or", "but", "if", "this", "that", "these", "those", "it",
    "its", "has", "have", "had", "will", "would", "could", "should",
    "not", "no", "so", "than", "then", "there", "their", "they", "them",
    "which", "who", "what", "when", "where", "how", "into", "over",
    "also", "been", "does", "do", "did", "can", "may", "might", "such",
}


def _split_sentences(text: str) -> list:
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]


def _word_freq(sentences: list) -> dict:
    freq = {}
    for s in sentences:
        for w in re.findall(r"[a-zA-Z']+", s.lower()):
            if w in STOPWORDS or len(w) < 3:
                continue
            freq[w] = freq.get(w, 0) + 1
    return freq


def summarize_text(text: str, max_sentences: int = 5, focus: str = None) -> str:
    """
    Extractive summary: scores each sentence by the frequency of its
    (non-stopword) words across the whole document, then returns the
    top-scoring sentences as a bullet list, in their original order.
    `focus` is accepted for API-compatibility with the old LLM version
    but isn't used here — there's no model to steer.
    """
    sentences = _split_sentences(text)
    if not sentences:
        return "- No readable text content found in the provided document(s)."

    if len(sentences) <= max_sentences:
        return "\n".join(f"- {s}" for s in sentences)

    freq = _word_freq(sentences)
    scored = []
    for i, s in enumerate(sentences):
        words = re.findall(r"[a-zA-Z']+", s.lower())
        score = sum(freq.get(w, 0) for w in words if w not in STOPWORDS)
        score = score / (len(words) + 1)  # normalize so long sentences don't win by default
        scored.append((i, score, s))

    top = sorted(scored, key=lambda x: x[1], reverse=True)[:max_sentences]
    top_in_order = sorted(top, key=lambda x: x[0])
    return "\n".join(f"- {s}" for _, _, s in top_in_order)


if __name__ == "__main__":
    sample = """
    The North region saw a sharp decline in Widget A sales during June, largely
    attributed to a temporary supplier shortage. Field teams report demand
    remained strong; this looks like a supply issue, not a demand issue.
    The East region's Widget B performance has been steadily improving since
    March, helped by a new regional distributor partnership signed in February.
    South region Widget A sales have been volatile month to month.
    """
    print(summarize_text(sample, max_sentences=3))
