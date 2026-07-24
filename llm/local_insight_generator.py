"""
local_insight_generator.py
Generates the "Insights & Analysis" section using pure Python templating
over the pandas outputs — no external API, no API key. Less flexible
than an LLM-written narrative, but fully deterministic, free, and
requires no network access at all.
"""


def generate_insights(stats_summary: dict, anomalies: str, text_summary: str) -> str:
    """
    Build a narrative section from:
      stats_summary: {category: total_value, ...}
      anomalies: pre-formatted string (table or "None detected.")
      text_summary: bullet-point string from local_summarizer.summarize_text
    """
    paragraphs = []

    # --- Ranking paragraph ---
    if stats_summary:
        ranked = sorted(stats_summary.items(), key=lambda kv: kv[1], reverse=True)
        top_cat, top_val = ranked[0]
        bottom_cat, bottom_val = ranked[-1]
        others = ", ".join(f"{cat} ({val:,.0f})" for cat, val in ranked[1:-1]) if len(ranked) > 2 else ""

        para = (
            f"{top_cat} leads with a total of {top_val:,.0f}, while {bottom_cat} trails "
            f"at {bottom_val:,.0f}"
        )
        if others:
            para += f". The remaining categories fall in between: {others}"
        para += "."
        paragraphs.append(para)

        if len(ranked) >= 2 and bottom_val > 0:
            gap_pct = (top_val - bottom_val) / bottom_val * 100
            if gap_pct > 30:
                paragraphs.append(
                    f"The gap between the strongest and weakest category is significant "
                    f"({gap_pct:,.0f}%), which may be worth investigating — check whether this "
                    f"reflects genuine demand differences, uneven coverage, or a data collection gap."
                )

    # --- Anomalies paragraph ---
    if anomalies and anomalies.strip() and anomalies.strip() != "None detected.":
        anomaly_lines = [l for l in anomalies.strip().split("\n") if l.strip()]
        count = max(len(anomaly_lines) - 1, 0)  # subtract header row
        paragraphs.append(
            f"The data contains {count} statistical outlier(s) flagged by z-score analysis "
            f"(values unusually far from their category's typical range). These are worth a "
            f"manual look to confirm whether they reflect a real event or a data entry issue."
        )
    else:
        paragraphs.append(
            "No statistical anomalies were detected in this dataset — values stayed within "
            "their expected range for each category."
        )

    # --- Context from documents ---
    if text_summary and "No readable text" not in text_summary and "No supporting" not in text_summary:
        paragraphs.append(
            "Supporting documents provided additional context:\n" + text_summary
        )

    # --- Next steps (generic but useful) ---
    paragraphs.append(
        "Recommended next steps: 1) Review the flagged anomalies against source records to "
        "confirm they're accurate, 2) Investigate the cause of the largest gap between "
        "top and bottom performing categories, 3) Re-run this report next period to see "
        "whether these patterns persist or were one-off."
    )

    return "\n\n".join(paragraphs)


if __name__ == "__main__":
    stats = {"North": 22050, "East": 18680, "West": 18160, "South": 16500}
    anomalies = "date region product units_sold\n2026-06-05 North Widget A 30"
    text_summary = "- North supplier shortage delayed restocking in June."
    print(generate_insights(stats, anomalies, text_summary))
