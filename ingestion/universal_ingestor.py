"""
universal_ingestor.py
Detects file types by extension and routes them to the correct loader.
Returns two buckets: tabular DataFrame + combined text string.
"""

from pathlib import Path
from typing import Tuple, List
import pandas as pd

from .tabular_ingestor import load_tabular, SUPPORTED_TABULAR
from .document_ingestor import load_documents, SUPPORTED_DOCS


def ingest_directory(input_dir: Path) -> Tuple[pd.DataFrame, str, List[str]]:
    """
    Scan a directory, route every supported file, and return:
      - combined tabular DataFrame
      - combined document text
      - list of skipped/unsupported filenames
    """
    input_dir = Path(input_dir)
    if not input_dir.is_dir():
        raise ValueError(f"Input path is not a directory: {input_dir}")

    all_files = [p for p in input_dir.iterdir() if p.is_file()]
    tabular_files = []
    doc_files = []
    skipped = []

    for f in all_files:
        suffix = f.suffix.lower()
        if suffix in SUPPORTED_TABULAR:
            tabular_files.append(f)
        elif suffix in SUPPORTED_DOCS:
            doc_files.append(f)
        else:
            skipped.append(f.name)

    df = load_tabular(tabular_files)
    text = load_documents(doc_files)

    return df, text, skipped
