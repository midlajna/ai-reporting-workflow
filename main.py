#!/usr/bin/env python3
"""
main.py – Pipeline orchestrator for ai-reporting-workflow

Usage:
    python main.py --input /path/to/folder --out output/Report.pdf
"""

import argparse
from pathlib import Path
import sys

# Ensure package imports work when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingestion.universal_ingestor import ingest_directory
from analysis.data_analyzer import analyze
from llm.pii_scrubber import scrub
from llm.summarizer import summarize
from llm.insight_generator import generate_insights
from report.report_builder import build_report


def run_pipeline(input_dir: Path, output_path: Path, title: str = None) -> Path:
    print(f"[1/5] Ingesting files from: {input_dir}")
    df, text, skipped = ingest_directory(input_dir)

    if skipped:
        print(f"       Skipped unsupported files: {skipped}")

    print(f"       Tabular rows: {len(df)}  |  Document text length: {len(text)} chars")

    print("[2/5] Analyzing structured data …")
    analysis = analyze(df)
    print(f"       Numeric columns: {analysis['numeric_columns']}")
    print(f"       Category columns: {analysis['category_columns']}")
    print(f"       Anomalies found: {len(analysis['anomalies'])}")

    print("[3/5] Scrubbing PII & summarizing documents …")
    clean_text = scrub(text)
    doc_summary = summarize(clean_text, max_sentences=8)
    print(f"       Summary length: {len(doc_summary)} chars")

    print("[4/5] Generating insights …")
    insights = generate_insights(analysis, doc_summary)

    print("[5/5] Building PDF report …")
    report_title = title or "AI Reporting Workflow – Analysis Report"
    final_path = build_report(analysis, insights, output_path, title=report_title)
    print(f"       Report written to: {final_path}")

    return final_path


def main():
    parser = argparse.ArgumentParser(description="AI Reporting Workflow – local deterministic pipeline")
    parser.add_argument("--input", "-i", required=True, help="Directory containing input files")
    parser.add_argument("--out", "-o", default="output/AI_Report.pdf", help="Output PDF path")
    parser.add_argument("--title", "-t", default=None, help="Report title")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_path = Path(args.out)

    if not input_dir.is_dir():
        print(f"Error: {input_dir} is not a directory")
        sys.exit(1)

    run_pipeline(input_dir, output_path, title=args.title)


if __name__ == "__main__":
    main()
