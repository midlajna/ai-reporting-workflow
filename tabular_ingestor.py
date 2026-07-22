"""
tabular_ingestor.py
Loads structured data (CSV or Excel) into a clean pandas DataFrame.
"""
import pandas as pd
from pathlib import Path


def load_tabular_data(filepath: str) -> pd.DataFrame:
    """Load a CSV or Excel file into a DataFrame, with basic cleaning."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"No such file: {filepath}")

    if path.suffix.lower() in [".csv"]:
        df = pd.read_csv(path)
    elif path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    else:
        raise ValueError(f"Unsupported tabular format: {path.suffix}")

    # Basic cleaning
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    df = df.dropna(how="all")
    return df


if __name__ == "__main__":
    df = load_tabular_data("../sample_data/sales_data.csv")
    print(df.head())
    print(df.dtypes)
