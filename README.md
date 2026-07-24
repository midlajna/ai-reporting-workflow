# AI Reporting Workflow

An end-to-end pipeline that turns raw business data into a polished
PDF report — combining classic data analysis (pandas) with local,
deterministic text summarization and templated insight generation.
Runs entirely offline after startup: no external AI API, no API key,
no per-request cost.

## What it does

1. **Ingests any mix of files from a folder** — just point it at a directory:
   - Structured/tabular: `.csv`, `.xlsx`, `.xls`, `.json`
   - Text/context: `.pdf`, `.txt`, `.docx`, `.pptx`
   - Images: `.png`, `.jpg`, `.jpeg` (OCR'd into text via tesseract)
   - Live: JSON API endpoints (`ingestion/api_ingestor.py`)

   A universal router (`ingestion/universal_ingestor.py`) detects each file's
   type by extension and normalizes everything into two buckets — tabular
   data (merged and analyzed together) or text (summarized together).
2. **Analyzes** the structured data with pandas: totals by category, monthly
   trends, and statistical anomaly detection (z-score based).
3. **Summarizes** the unstructured documents using a local, deterministic
   extractive summarizer (word-frequency sentence scoring) — no external
   AI API, no API key, no network call for this step, extracting
   the qualitative context behind the numbers.
4. **Synthesizes insights**: a rule-based generator (`llm/local_insight_generator.py`)
   combines the numeric findings and the document summary into a templated
   "Insights & Analysis" section — ranking categories, flagging anomalies,
   and folding in the qualitative context, all with plain Python string
   logic rather than a model call.
5. **Generates a report**: a formatted PDF with charts, tables, and the
   generated narrative, built with ReportLab + matplotlib.

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
```

No API keys or accounts needed — everything runs locally.

## Run

```bash
python main.py --input sample_data --out output/AI_Report.pdf
```

Drop any mix of supported files into the input folder — CSVs, an Excel
export, a JSON API dump, a Word memo, a PDF report, a slide deck, even a
screenshot of a table — and the pipeline sorts them automatically, merges
all tabular data together, summarizes all text/context together, and
produces `output/AI_Report.pdf` with revenue-by-region charts, a monthly
trend chart, a table of detected anomalies, and a generated insights
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
- **PII redaction before summarization/insights** (`llm/pii_scrubber.py`) — emails, phone numbers, SSNs, credit-card-like numbers, and Aadhaar-like numbers are regex-redacted from text. Since there's no external API call anymore, this data never leaves the server at all — the redaction is defense-in-depth for logs and the output PDF itself.

Run the server:
```bash
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
- Raw row-level data from tabular sources never leaves the server at all now — there's no external API call in the pipeline; only aggregated summary stats and the anomaly table feed into the local insight generator (see `main.py` step 5)



- Swap `api_ingestor.py`'s demo endpoint for a real internal API (sales CRM,
  analytics platform, etc.)
- Add a scheduler (cron / Airflow) to `main.py` to run this as a recurring
  weekly/monthly report job
- Add an email-delivery step to send the generated PDF automatically
- Swap ReportLab for a Markdown/HTML report if a PDF isn't required

## Deployment

The app is stateless (nothing persists between requests — see Backend &
Security above), so it can be deployed on any container-friendly platform
with just two environment variables set as secrets: `REPORT_APP_USER`,
`REPORT_APP_PASSWORD`. No AI API key is needed at all — everything runs
locally in the container.

### Option A — Docker, run anywhere (VPS, EC2, your own server)

```bash
docker build -t ai-reporting-workflow .
docker run -d \
  -p 8080:8080 \
  -e REPORT_APP_USER=admin \
  -e REPORT_APP_PASSWORD=change_me \
  --name ai-report ai-reporting-workflow
```

Test it:
```bash
curl -u admin:change_me -F "files=@sample_data/sales_data.csv" \
  -F "files=@sample_data/market_notes.txt" \
  http://localhost:8080/generate-report --output AI_Report.pdf
```

Put this behind nginx or Caddy for HTTPS — Basic Auth is only safe over TLS.

### Option B — Render (easiest for a portfolio demo, free tier available)

1. Push this repo to GitHub.
2. On Render: New → Web Service → connect the repo → it auto-detects the `Dockerfile`.
3. Add the two environment variables as secrets in the Render dashboard.
4. Render gives you HTTPS and a public URL automatically — no reverse proxy setup needed.

### Option C — Railway / Fly.io

Both auto-build from a `Dockerfile` the same way:
- **Railway**: New Project → Deploy from GitHub repo → add env vars in the Variables tab.
- **Fly.io**: `fly launch` (detects the Dockerfile), then `fly secrets set REPORT_APP_USER=... REPORT_APP_PASSWORD=...`, then `fly deploy`.

### What to check after deploying

- `GET /health` returns `{"status": "ok"}` with no auth
- `POST /generate-report` with valid auth + a supported file returns a PDF
- An unsupported file (e.g. `.exe`) is rejected with a 400, not a 500
- Missing/wrong credentials return 401, not a stack trace

## Tech stack

Python · pandas · NumPy · matplotlib · ReportLab · pdfplumber · Flask
