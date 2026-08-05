"""
report_builder.py
Assembles a polished multi-page PDF report using ReportLab + matplotlib charts.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


def _make_category_chart(cat_totals: Dict[str, float], title: str, out_path: Path) -> Optional[Path]:
    if not cat_totals:
        return None
    items = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    labels = [k[:20] for k, _ in items]
    values = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(7, 3.8))
    bars = ax.barh(labels[::-1], values[::-1], color="#3b82f6")
    ax.set_xlabel("Value")
    ax.set_title(title, fontsize=11, pad=8)
    ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _make_trend_chart(trends: Dict[str, float], out_path: Path) -> Optional[Path]:
    if not trends or len(trends) < 2:
        return None
    dates = list(trends.keys())
    values = list(trends.values())

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.plot(dates, values, marker="o", linewidth=2, color="#10b981")
    ax.fill_between(dates, values, alpha=0.15, color="#10b981")
    ax.set_title("Monthly Trend", fontsize=11, pad=8)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out_path


def build_report(
    analysis: Dict[str, Any],
    insights: str,
    output_path: Path,
    title: str = "AI Reporting Workflow – Analysis Report",
) -> Path:
    """
    Generate the final PDF and return its path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Temporary chart files
    chart_dir = Path(tempfile.mkdtemp(prefix="report_charts_"))
    charts = []

    # Category chart (first category dimension)
    cat_totals = analysis.get("category_totals", {})
    if cat_totals:
        first_cat = next(iter(cat_totals))
        chart_path = chart_dir / "category.png"
        if _make_category_chart(cat_totals[first_cat], f"Totals by {first_cat}", chart_path):
            charts.append(("Category Breakdown", chart_path))

    # Trend chart
    trends = analysis.get("time_trends", {})
    if trends:
        chart_path = chart_dir / "trend.png"
        if _make_trend_chart(trends, chart_path):
            charts.append(("Time Trend", chart_path))

    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=6,
        textColor=colors.HexColor("#1e3a5f"),
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="SectionHead",
        parent=styles["Heading1"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=6,
        textColor=colors.HexColor("#1e3a5f"),
    ))
    styles.add(ParagraphStyle(
        name="BodyJust",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Small",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
    ))

    story = []

    # Title
    story.append(Paragraph(title, styles["ReportTitle"]))
    story.append(Paragraph(
        f"Generated from {analysis.get('row_count', 0):,} records · "
        f"{len(analysis.get('anomalies', []))} anomalies flagged",
        styles["Small"]
    ))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e3a5f")))
    story.append(Spacer(1, 10))

    # Insights section
    story.append(Paragraph("Insights & Analysis", styles["SectionHead"]))
    for para in insights.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), styles["BodyJust"]))

    # Charts
    for chart_title, chart_path in charts:
        story.append(Spacer(1, 8))
        story.append(Paragraph(chart_title, styles["SectionHead"]))
        img = Image(str(chart_path), width=6.2 * inch, height=3.3 * inch)
        story.append(img)

    # Numeric summary table
    numeric = analysis.get("numeric_summary", {})
    if numeric:
        story.append(Paragraph("Numeric Summary", styles["SectionHead"]))
        header = [
            Paragraph("<b>Metric</b>", styles["BodyJust"]),
            Paragraph("<b>Sum</b>", styles["BodyJust"]),
            Paragraph("<b>Mean</b>", styles["BodyJust"]),
            Paragraph("<b>Min</b>", styles["BodyJust"]),
            Paragraph("<b>Max</b>", styles["BodyJust"]),
        ]
        rows = [header]
        for col, stats in numeric.items():
            rows.append([
                Paragraph(str(col)[:30], styles["BodyJust"]),
                Paragraph(f"{stats['sum']:,.1f}", styles["BodyJust"]),
                Paragraph(f"{stats['mean']:,.1f}", styles["BodyJust"]),
                Paragraph(f"{stats['min']:,.1f}", styles["BodyJust"]),
                Paragraph(f"{stats['max']:,.1f}", styles["BodyJust"]),
            ])
        t = Table(rows, colWidths=[1.8*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t)

    # Anomalies table
    anomalies = analysis.get("anomalies", [])
    if anomalies:
        story.append(Paragraph("Detected Anomalies (z-score > 2.5)", styles["SectionHead"]))
        header = [
            Paragraph("<b>Column</b>", styles["BodyJust"]),
            Paragraph("<b>Value</b>", styles["BodyJust"]),
            Paragraph("<b>Z-Score</b>", styles["BodyJust"]),
            Paragraph("<b>Mean</b>", styles["BodyJust"]),
        ]
        rows = [header]
        for a in anomalies[:15]:
            rows.append([
                Paragraph(str(a["column"])[:25], styles["BodyJust"]),
                Paragraph(f"{a['value']:,.2f}", styles["BodyJust"]),
                Paragraph(f"{a['z_score']:.2f}", styles["BodyJust"]),
                Paragraph(f"{a['mean']:,.2f}", styles["BodyJust"]),
            ])
        t = Table(rows, colWidths=[2.0*inch, 1.5*inch, 1.2*inch, 1.5*inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fee2e2")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t)
        if len(anomalies) > 15:
            story.append(Paragraph(
                f"… and {len(anomalies) - 15} more anomalies (truncated for brevity).",
                styles["Small"]
            ))

    # Footer note
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph(
        "Generated locally by ai-reporting-workflow · No external AI API calls · Deterministic pipeline",
        styles["Small"]
    ))

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    doc.build(story)

    # Cleanup charts
    for _, p in charts:
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass
    try:
        chart_dir.rmdir()
    except Exception:
        pass

    return output_path
