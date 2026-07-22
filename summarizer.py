"""
summarizer.py
Uses the Anthropic API to summarize unstructured text documents
(e.g. PDF reports, market notes) into concise bullet-point summaries.
"""
import os
import anthropic

MODEL = "claude-sonnet-4-5"  # swap for whichever model your API key has access to


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Set the ANTHROPIC_API_KEY environment variable before running this module."
        )
    return anthropic.Anthropic(api_key=api_key)


def summarize_text(text: str, focus: str = "key business insights") -> str:
    """Summarize a block of text into concise bullet points."""
    client = get_client()
    prompt = f"""Summarize the following document into 4-6 concise bullet points,
focused on {focus}. Be factual and specific. Do not add information that
isn't in the text.

DOCUMENT:
{text}
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from ingestion.document_ingestor import load_document_text

    text = load_document_text("../sample_data/market_notes.txt")
    print(summarize_text(text))
