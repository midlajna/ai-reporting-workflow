"""
main.py
AI Reporting Workflow — end-to-end pipeline.

Point it at a folder containing ANY mix of supported files:
    .csv, .xlsx, .xls, .json          -> treated as structured/tabular data
    .pdf, .txt, .docx, .pptx          -> treated as text/context
    .png, .jpg, .jpeg                 -> OCR'd into text

It merges all tabular files, runs statistical analysis, summarizes all
text files, synthesizes narrative insights tying the two together, and
outputs a polished PDF report.

Usage:
    export GEMINI_API_KEY=your_key_here
    python main.py --input sample_data --out output/AI_Report.pdf
"""
import argparse
from pathlib import Path
import pandas as pd

from ingestion.universal_ingestor import ingest_folder
from analysis.data_analyzer import group_summary, trend_by_period, detect_anomalies
from llm.local_summarizer import summarize_text
from llm.local_insight_generator import generate_insights
from llm.pii_scrubber import scrub_text
from report.report_builder import build_report


def run_pipeline(
    input_folder: str,
    output_pdf: str = "output/AI_Report.pdf",
    date_col: str = "date",
    group_col: str = "region",
    value_col: str = "revenue",
):
    print(f"[1/6] Scanning and ingesting files in {input_folder} ...")
    results = ingest_folder(input_folder)

    tabular_frames = [r["data"] for r in results if r["type"] == "tabular"]
    text_blocks = [f"--- {r['source']} ---\n{r['data']}" for r in results if r["type"] == "text"]

    if not tabular_frames:
        raise ValueError("No tabular files (.csv/.xlsx/.json) found — need at least one for analysis.")

    print("[2/6] Merging tabular data ...")
    df = pd.concat(tabular_frames, ignore_index=True) if len(tabular_frames) > 1 else tabular_frames[0]

    print("[3/6] Running statistical analysis ...")
    region_summary = group_summary(df, group_col, value_col)
    trend = trend_by_period(df, date_col, value_col, freq="MS")
    anomalies = detect_anomalies(df, group_col, "units_sold") if "units_sold" in df.columns else pd.DataFrame()

    print("[4/6] Scrubbing PII and summarizing document context (local, no API) ...")
    if text_blocks:
        combined_text = "\n\n".join(text_blocks)
        combined_text, pii_counts = scrub_text(combined_text)
        if pii_counts:
            print(f"        Redacted before sending to LLM: {pii_counts}")
        text_summary = summarize_text(combined_text)
    else:
        text_summary = "No supporting text documents were provided."

    print("[5/6] Generating narrative insights (local, no API) ...")
    stats_for_llm = region_summary.set_index(group_col)["sum"].to_dict()
    anomalies_text = anomalies.to_string(index=False) if len(anomalies) else "None detected."
    insights = generate_insights(stats_for_llm, anomalies_text, text_summary)

    print(f"[6/6] Building PDF report at {output_pdf} ...")
    Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)
    build_report(
        title="AI-Generated Business Report",
        output_path=output_pdf,
        region_summary_df=region_summary,
        trend_df=trend,
        anomalies_df=anomalies,
        insights_text=insights,
        chart_dir=str(Path(output_pdf).parent),
    )
    print("Done ->", output_pdf)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Reporting Workflow")
    parser.add_argument("--input", default="sample_data", help="Folder containing any mix of supported files")
    parser.add_argument("--out", default="output/AI_Report.pdf")
    args = parser.parse_args()

    run_pipeline(args.input, args.out)
    
