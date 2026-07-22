"""
data_analyzer.py
Runs statistical analysis over tabular data: summary stats, trends,
and simple anomaly detection using z-scores.
"""
import pandas as pd
import numpy as np


def summarize_numeric(df: pd.DataFrame) -> dict:
    """Basic descriptive stats for all numeric columns."""
    numeric_df = df.select_dtypes(include=[np.number])
    return numeric_df.describe().round(2).to_dict()


def trend_by_period(df: pd.DataFrame, date_col: str, value_col: str, freq: str = "M") -> pd.DataFrame:
    """Aggregate a value column over time (e.g. monthly totals)."""
    grouped = (
        df.set_index(date_col)
        .resample(freq)[value_col]
        .sum()
        .reset_index()
    )
    grouped["pct_change"] = grouped[value_col].pct_change().round(3) * 100
    return grouped


def group_summary(df: pd.DataFrame, group_col: str, value_col: str) -> pd.DataFrame:
    """Sum/mean of a value column grouped by a categorical column."""
    return (
        df.groupby(group_col)[value_col]
        .agg(["sum", "mean", "count"])
        .round(2)
        .sort_values("sum", ascending=False)
        .reset_index()
    )


def detect_anomalies(df: pd.DataFrame, group_col: str, value_col: str, z_thresh: float = 1.5) -> pd.DataFrame:
    """
    Flag rows where a value is an outlier (by z-score) within its group.
    Useful for catching things like 'North region Widget A crashed in June'.
    """
    result_rows = []
    for group_val, sub in df.groupby(group_col):
        values = sub[value_col]
        if values.std(ddof=0) == 0 or len(values) < 3:
            continue
        z_scores = (values - values.mean()) / values.std(ddof=0)
        flagged = sub[np.abs(z_scores) > z_thresh].copy()
        flagged["z_score"] = z_scores[np.abs(z_scores) > z_thresh].round(2)
        result_rows.append(flagged)

    if result_rows:
        return pd.concat(result_rows).sort_values("z_score")
    return pd.DataFrame(columns=list(df.columns) + ["z_score"])


def profit_margin(df: pd.DataFrame, revenue_col: str, cost_col: str) -> pd.DataFrame:
    """Add a profit margin % column."""
    df = df.copy()
    df["profit"] = df[revenue_col] - df[cost_col]
    df["margin_pct"] = (df["profit"] / df[revenue_col] * 100).round(2)
    return df


if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from ingestion.tabular_ingestor import load_tabular_data

    df = load_tabular_data("../sample_data/sales_data.csv")
    print("=== Group Summary (by region) ===")
    print(group_summary(df, "region", "revenue"))
    print("\n=== Anomalies ===")
    print(detect_anomalies(df, "region", "units_sold"))
