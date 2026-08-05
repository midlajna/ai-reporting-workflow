"""
tabular_ingestor.py
Loads and normalizes structured/tabular files into a single pandas DataFrame.
Supports: .csv, .xlsx, .xls, .json
"""

from pathlib import Path
from typing import List, Optional
import pandas as pd


SUPPORTED_TABULAR = {".csv", ".xlsx", ".xls", ".json"}


def _load_one(path: Path) -> Optional[pd.DataFrame]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            return pd.read_csv(path)
        if suffix in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        if suffix == ".json":
            # Try records / list-of-dicts first, fall back to nested
            df = pd.read_json(path)
            if isinstance(df, pd.Series):
                df = df.to_frame().T
            return df
    except Exception as e:
        print(f"[tabular_ingestor] Failed to load {path.name}: {e}")
    return None


def load_tabular(files: List[Path]) -> pd.DataFrame:
    """
    Load all supported tabular files and concatenate them.
    Columns that appear in only some files are filled with NaN.
    """
    frames = []
    for f in files:
        if f.suffix.lower() not in SUPPORTED_TABULAR:
            continue
        df = _load_one(f)
        if df is not None and not df.empty:
            df["_source_file"] = f.name
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True, sort=False)
    return combined
