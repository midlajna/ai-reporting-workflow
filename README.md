# AI Reporting Workflow

An end-to-end pipeline that turns raw business data into a polished,
AI-written PDF report — combining classic data analysis with LLM-driven
summarization and narrative insight generation.

## What it does

1. **Ingests any mix of files from a folder** — just point it at a directory:
   - Structured/tabular: `.csv`, `.xlsx`, `.xls`, `.json`
   - Text/context: `.pdf`, `.txt`, `.docx`, `.pptx`
   - Images: `.png`, `.jpg`, `.jpeg` (OCR'd into text via tesseract)
   - Live: JSON API endpoints (`ingestion/api_ingestor.py`)

   A universal router (`ingestion/universal_ingestor.py`) detects each file's
   type by extension and normalizes everything into two buckets — tabular
   data (merged and analyzed together) or text (summarized together) —
   before either hits the LLM.
2. **Analyzes** the structured data with pandas: totals by category, monthly
   trends, and statistical anomaly detection (z-score based).
3. **Summarizes** the unstructured documents using the Anthropic API, extracting
   the qualitative context behind the numbers.
4. **Synthesizes insights**: an LLM call combines the numeric findings and the
   document summary to write a narrative "Insights & Analysis" section —
   explaining what happened, why (if the evidence supports it), and what to
   do next.
5. **Generates a report**: a formatted PDF with charts, tables, and the
   AI-written narrative, built with ReportLab + matplotlib.

## Why this project

Most "AI report generator" demos just summarize text. This project shows a
more realistic workflow: reconciling structured numeric data with
unstructured qualitative context, the way an actual analyst would — using
the LLM specifically where it adds value (synthesis, narrative), and plain
pandas where it's more reliable (statistics).

## Project structure

```
ai-reporting-workflow/
├── ingestion/
│   ├── tabular_ingestor.py   # CSV/Excel loader
│   ├── document_ingestor.py  # PDF/text extractor
│   └── api_ingestor.py       # Live API fetcher
├── analysis/
│   └── data_analyzer.py      # Stats, trends, anomaly detection
├── llm/
│   ├── summarizer.py         # Document summarization
│   └── insight_generator.py  # Narrative insight synthesis
├── report/
│   └── report_builder.py     # PDF report assembly
├── sample_data/
│   ├── sales_data.csv
│   └── market_notes.txt
├── main.py                   # Pipeline orchestrator
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
```

## Run

```bash
python main.py --input sample_data --out output/AI_Report.pdf
```

Drop any mix of supported files into the input folder — CSVs, an Excel
export, a JSON API dump, a Word memo, a PDF report, a slide deck, even a
screenshot of a table — and the pipeline sorts them automatically, merges
all tabular data together, summarizes all text/context together, and
produces `output/AI_Report.pdf` with revenue-by-region charts, a monthly
trend chart, a table of detected anomalies, and an AI-generated insights
section tying the numbers to the qualitative context.

## Backend & security

`app.py` wraps the pipeline in a minimal Flask API for web-based use:

- `POST /generate-report` — upload files (`multipart/form-data`, field name `files`), get a PDF back
- `GET /health` — health check, no auth required

Security measures in place:
- **HTTP Basic Auth** on the report endpoint (`REPORT_APP_USER` / `REPORT_APP_PASSWORD` env vars)
- **File extension allowlist** — anything not in the supported list (e.g. `.exe`) is rejected before it touches disk
- **10 MB request size cap** (configurable)
- **Isolated per-request temp directories** — uploads and generated files live in a fresh temp folder per request and are deleted immediately after the response is sent; nothing persists between requests
- **PII redaction before any LLM call** (`llm/pii_scrubber.py`) — emails, phone numbers, SSNs, credit-card-like numbers, and Aadhaar-like numbers are regex-redacted from text *before* it's sent to the Anthropic API
- **API key stays server-side** — read from an environment variable, never returned to the client

Run the server:
```bash
export ANTHROPIC_API_KEY=your_key
export REPORT_APP_USER=admin
export REPORT_APP_PASSWORD=change_me
python app.py
```

**What this does NOT cover (known gaps for a real production deployment):**
- No rate limiting — add something like Flask-Limiter
- No HTTPS termination — put this behind nginx/a reverse proxy with TLS
- No audit logging of who generated what report
- No malware/antivirus scanning of uploaded files
- Basic Auth over plain HTTP is not safe on its own — only use it behind HTTPS
- Raw row-level data from tabular sources is never sent to the LLM — only aggregated summary stats and the anomaly table are (see `main.py` step 5), which is a meaningful boundary but not a replacement for full data classification if you're handling regulated data (PII/financial/health records)



- Swap `api_ingestor.py`'s demo endpoint for a real internal API (sales CRM,
  analytics platform, etc.)
- Add a scheduler (cron / Airflow) to `main.py` to run this as a recurring
  weekly/monthly report job
- Add an email-delivery step to send the generated PDF automatically
- Swap ReportLab for a Markdown/HTML report if a PDF isn't required

## Deployment

The app is stateless (nothing persists between requests — see Backend &
Security above), so it can be deployed on any container-friendly platform
with just three environment variables set as secrets: `ANTHROPIC_API_KEY`,
`REPORT_APP_USER`, `REPORT_APP_PASSWORD`.

### What to check after deploying

- `GET /health` returns `{"status": "ok"}` with no auth
- `POST /generate-report` with valid auth + a supported file returns a PDF
- An unsupported file (e.g. `.exe`) is rejected with a 400, not a 500
- Missing/wrong credentials return 401, not a stack trace

## Tech stack

Python · pandas · NumPy · matplotlib · ReportLab · pdfplumber · Anthropic API
