"""
summarizer.py
Uses Google's Gemini API (free tier — no card, no trial expiry) to
summarize unstructured text documents (e.g. PDF reports, market notes)
into concise bullet-point summaries.
"""
import os
import google.generativeai as genai

MODEL = "gemini-2.5-flash"  # free-tier model with the highest daily quota headroom


def get_model() -> "genai.GenerativeModel":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Set the GEMINI_API_KEY environment variable before running this module. "
            "Get a free key at https://aistudio.google.com/apikey"
        )
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(MODEL)


def summarize_text(text: str, focus: str = "key business insights") -> str:
    """Summarize a block of text into concise bullet points."""
    model = get_model()
    prompt = f"""Summarize the following document into 4-6 concise bullet points,
focused on {focus}. Be factual and specific. Do not add information that
isn't in the text.

DOCUMENT:
{text}
"""
    response = model.generate_content(prompt)
    return response.text


if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from ingestion.document_ingestor import load_document_text

    text = load_document_text("../sample_data/market_notes.txt")
    print(summarize_text(text))
    
