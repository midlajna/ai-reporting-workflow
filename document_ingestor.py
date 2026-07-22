"""
document_ingestor.py
Extracts raw text from PDFs or plain text files for later summarization.
"""
from pathlib import Path


def load_document_text(filepath: str) -> str:
    """Extract text from a PDF or .txt file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"No such file: {filepath}")

    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8")

    if path.suffix.lower() == ".pdf":
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("pdfplumber is required for PDF ingestion: pip install pdfplumber")

        text_chunks = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_chunks.append(page_text)
        return "\n".join(text_chunks)

    raise ValueError(f"Unsupported document format: {path.suffix}")


if __name__ == "__main__":
    text = load_document_text("../sample_data/market_notes.txt")
    print(text[:300])
