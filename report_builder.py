"""
report_builder.py
Assembles the final PDF report: title, charts (matplotlib), grouped
data tables, and the LLM-generated narrative insights.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)


def make_bar_chart(df, x_col, y_col, title, out_path):
    plt.figure(figsize=(6, 3.2))
    plt.bar(df[x_col].astype(str), df[y_col], color="#5B4FDB")
    plt.title(title, fontsize=11)
    plt.xticks(rotation=20, ha="right", fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def make_line_chart(df, x_col, y_col, title, out_path):
    plt.figure(figsize=(6, 3.2))
    plt.plot(df[x_col], df[y_col], marker="o", color="#5B4FDB")
    plt.title(title, fontsize=11)
    plt.xticks(rotation=20, ha="right", fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def df_to_table(df, max_rows=10):
    data = [list(df.columns)] + df.head(max_rows).astype(str).values.tolist()
    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5B4FDB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F0FC")]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def build_report(
    title: str,
    output_path: str,
    region_summary_df,
    trend_df,
    anomalies_df,
    insights_text: str,
    chart_dir: str = "./output",
):
    Path(chart_dir).mkdir(exist_ok=True)
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                             topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", fontSize=20, leading=24,
                               textColor=colors.HexColor("#2E1F91"), spaceAfter=6))
    styles.add(ParagraphStyle(name="SectionHeader", fontSize=13, leading=16,
                               textColor=colors.HexColor("#5B4FDB"), spaceBefore=14, spaceAfter=6))
    styles.add(ParagraphStyle(name="Body", fontSize=9.5, leading=14))

    story = []
    story.append(Paragraph(title, styles["ReportTitle"]))
    story.append(Paragraph(f"Generated {datetime.now().strftime('%d %B %Y, %H:%M')}", styles["Body"]))
    story.append(Spacer(1, 10))

    # Revenue by region chart + table
    story.append(Paragraph("Revenue by Region", styles["SectionHeader"]))
    chart_path = make_bar_chart(region_summary_df, region_summary_df.columns[0], "sum",
                                 "Total Revenue by Region", f"{chart_dir}/region_chart.png")
    story.append(Image(chart_path, width=5.5 * inch, height=2.9 * inch))
    story.append(Spacer(1, 6))
    story.append(df_to_table(region_summary_df))

    # Trend chart
    story.append(Paragraph("Revenue Trend Over Time", styles["SectionHeader"]))
    trend_chart_path = make_line_chart(trend_df, trend_df.columns[0], trend_df.columns[1],
                                        "Monthly Revenue Trend", f"{chart_dir}/trend_chart.png")
    story.append(Image(trend_chart_path, width=5.5 * inch, height=2.9 * inch))

    # Anomalies
    story.append(Paragraph("Detected Anomalies", styles["SectionHeader"]))
    if len(anomalies_df) > 0:
        story.append(df_to_table(anomalies_df))
    else:
        story.append(Paragraph("No significant statistical anomalies detected.", styles["Body"]))

    # Insights (LLM-generated)
    story.append(Paragraph("Insights & Analysis", styles["SectionHeader"]))
    for para in insights_text.split("\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), styles["Body"]))
            story.append(Spacer(1, 4))

    doc.build(story)
    return output_path
