"""
data_analyzer.py
Performs classic pandas analysis on the combined tabular data:
  - column detection / basic stats
  - category totals (if categorical columns exist)
  - monthly / time trends (if date-like columns exist)
  - z-score anomaly detection on numeric columns
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def _detect_date_column(df: pd.DataFrame) -> Optional[str]:
    for col in df.columns:
        if col.startswith("_"):
            continue
        # Try parsing a sample
        sample = df[col].dropna().head(20)
        if sample.empty:
            continue
        try:
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().mean() > 0.7:
                return col
        except Exception:
            continue
    return None


def _detect_category_columns(df: pd.DataFrame, max_unique: int = 30) -> List[str]:
    cats = []
    for col in df.columns:
        if col.startswith("_") or pd.api.types.is_numeric_dtype(df[col]):
            continue
        nunique = df[col].nunique(dropna=True)
        if 1 < nunique <= max_unique:
            cats.append(col)
    return cats


def _detect_numeric_columns(df: pd.DataFrame) -> List[str]:
    return [
        c for c in df.columns
        if not c.startswith("_") and pd.api.types.is_numeric_dtype(df[c])
    ]


def analyze(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run the full analysis suite and return a structured results dict
    that the insight generator and report builder can consume.
    """
    results: Dict[str, Any] = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "numeric_summary": {},
        "category_totals": {},
        "time_trends": {},
        "anomalies": [],
        "date_column": None,
        "category_columns": [],
        "numeric_columns": [],
    }

    if df.empty:
        return results

    numeric_cols = _detect_numeric_columns(df)
    cat_cols = _detect_category_columns(df)
    date_col = _detect_date_column(df)

    results["numeric_columns"] = numeric_cols
    results["category_columns"] = cat_cols
    results["date_column"] = date_col

    # Basic numeric summary
    for col in numeric_cols:
        s = df[col].dropna()
        if s.empty:
            continue
        results["numeric_summary"][col] = {
            "sum": float(s.sum()),
            "mean": float(s.mean()),
            "median": float(s.median()),
            "std": float(s.std()) if len(s) > 1 else 0.0,
            "min": float(s.min()),
            "max": float(s.max()),
            "count": int(s.count()),
        }

    # Category totals (sum of first numeric column, or count)
    value_col = numeric_cols[0] if numeric_cols else None
    for cat in cat_cols:
        if value_col:
            totals = df.groupby(cat, dropna=False)[value_col].sum().sort_values(ascending=False)
            results["category_totals"][cat] = {
                str(k): float(v) for k, v in totals.items()
            }
        else:
            counts = df[cat].value_counts(dropna=False)
            results["category_totals"][cat] = {
                str(k): int(v) for k, v in counts.items()
            }

    # Time trends (monthly aggregation on first numeric column)
    if date_col and value_col:
        try:
            tmp = df.copy()
            tmp["_parsed_date"] = pd.to_datetime(tmp[date_col], errors="coerce")
            tmp = tmp.dropna(subset=["_parsed_date"])
            if not tmp.empty:
                monthly = (
                    tmp.set_index("_parsed_date")
                    .resample("ME")[value_col]
                    .sum()
                    .dropna()
                )
                results["time_trends"] = {
                    str(idx.date()): float(val) for idx, val in monthly.items()
                }
        except Exception as e:
            print(f"[data_analyzer] Time-trend failed: {e}")

    # Z-score anomaly detection on numeric columns
    anomalies = []
    for col in numeric_cols:
        s = df[col].dropna()
        if len(s) < 5:
            continue
        mean = s.mean()
        std = s.std()
        if std == 0:
            continue
        z = (s - mean) / std
        outlier_mask = z.abs() > 2.5
        for idx in s[outlier_mask].index:
            anomalies.append({
                "column": col,
                "row_index": int(idx) if isinstance(idx, (int, np.integer)) else str(idx),
                "value": float(s.loc[idx]),
                "z_score": float(z.loc[idx]),
                "mean": float(mean),
            })
    results["anomalies"] = anomalies[:50]  # cap for report size

    return results
