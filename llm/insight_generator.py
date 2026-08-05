"""
insight_generator.py
Rule-based / templated insight synthesis.
Combines numeric analysis results + document summary into a coherent
"Insights & Analysis" narrative using plain Python string logic.
No model call.
"""

from typing import Dict, Any, List


def generate_insights(analysis: Dict[str, Any], doc_summary: str) -> str:
    """
    Produce a multi-paragraph insights section.
    """
    paragraphs: List[str] = []

    # 1. Overview
    rows = analysis.get("row_count", 0)
    cols = analysis.get("column_count", 0)
    paragraphs.append(
        f"This report is based on {rows:,} records across {cols} columns. "
        "The following analysis reconciles quantitative findings with qualitative context extracted from the accompanying documents."
    )

    # 2. Key numeric highlights
    numeric = analysis.get("numeric_summary", {})
    if numeric:
        highlights = []
        for col, stats in list(numeric.items())[:4]:
            highlights.append(
                f"{col}: total {stats['sum']:,.2f}, average {stats['mean']:,.2f} "
                f"(range {stats['min']:,.2f} – {stats['max']:,.2f})"
            )
        paragraphs.append(
            "Key quantitative metrics: " + "; ".join(highlights) + "."
        )

    # 3. Category ranking
    cat_totals = analysis.get("category_totals", {})
    for cat, totals in list(cat_totals.items())[:2]:
        if not totals:
            continue
        ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)
        top = ranked[:3]
        top_str = ", ".join(f"{k} ({v:,.0f})" for k, v in top)
        paragraphs.append(
            f"By {cat}, the leading contributors are: {top_str}."
        )
        if len(ranked) > 3:
            bottom = ranked[-1]
            paragraphs.append(
                f"The lowest contributor in this dimension is {bottom[0]} ({bottom[1]:,.0f})."
            )

    # 4. Time trends
    trends = analysis.get("time_trends", {})
    if trends:
        items = list(trends.items())
        if len(items) >= 2:
            first_val = items[0][1]
            last_val = items[-1][1]
            change = last_val - first_val
            pct = (change / first_val * 100) if first_val else 0
            direction = "increased" if change > 0 else "decreased" if change < 0 else "remained stable"
            paragraphs.append(
                f"Over the observed period the primary metric {direction} "
                f"from {first_val:,.0f} to {last_val:,.0f} "
                f"({pct:+.1f}% overall)."
            )

    # 5. Anomalies
    anomalies = analysis.get("anomalies", [])
    if anomalies:
        paragraphs.append(
            f"{len(anomalies)} statistical anomalies (z-score > 2.5) were detected. "
            "These outliers warrant further investigation as they may indicate data-quality issues, "
            "one-off events, or emerging risks."
        )
        # Mention a couple of concrete examples
        examples = anomalies[:3]
        ex_strs = [
            f"{a['column']} = {a['value']:,.2f} (z={a['z_score']:.1f})"
            for a in examples
        ]
        paragraphs.append("Notable examples: " + "; ".join(ex_strs) + ".")

    # 6. Qualitative context from documents
    if doc_summary and "No document text" not in doc_summary:
        paragraphs.append(
            "Qualitative context from source documents: " + doc_summary
        )
    else:
        paragraphs.append(
            "No additional qualitative documents were supplied; the narrative above is driven solely by the tabular analysis."
        )

    # 7. Closing recommendation
    paragraphs.append(
        "Recommendation: Review the flagged anomalies and the top/bottom category contributors "
        "in conjunction with the document summary to prioritize follow-up actions. "
        "Consider enriching future runs with additional context files for deeper narrative synthesis."
    )

    return "\n\n".join(paragraphs)
