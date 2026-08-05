# AI Reporting Workflow

An end-to-end pipeline that turns raw business data into a polished PDF report — combining classic data analysis (pandas) with local, deterministic text summarization and templated insight generation.

**Runs entirely offline after startup:** no external AI API, no API key, no per-request cost.

---

## What it does

1. **Ingests** any mix of files from a folder:
   - Structured/tabular: `.csv`, `.xlsx`, `.xls`, `.json`
   - Text/context: `.pdf`, `.txt`, `.docx`, `.pptx`
   - Images: `.png`, `.jpg`, `.jpeg` (OCR via Tesseract)

2. **Analyzes** structured data with pandas — totals by category, monthly trends, z-score anomaly detection.

3. **Summarizes** unstructured documents using a local extractive summarizer (word-frequency sentence scoring).

4. **Synthesizes insights** with a rule-based generator that combines numeric findings + document summary into a templated narrative.

5. **Generates a PDF report** with charts, tables, and the generated insights (ReportLab + matplotlib).

---

## Project structure

```
ai-reporting-workflow/
├── ingestion/
│   ├── tabular_ingestor.py    # CSV / Excel / JSON loader
│   ├── document_ingestor.py   # PDF / text / DOCX / PPTX / OCR
│   └── universal_ingestor.py  # Routes files by extension
├── analysis/
│   └── data_analyzer.py       # Stats, trends, anomaly detection
├── llm/
│   ├── pii_scrubber.py        # Regex PII redaction
│   ├── summarizer.py          # Local extractive summarizer
│   └── insight_generator.py   # Templated insight synthesis
├── report/
│   └── report_builder.py      # PDF assembly
├── templates/
│   └── index.html             # Web UI
├── main.py                    # CLI pipeline orchestrator
├── app.py                     # Flask web API + frontend
├── requirements.txt
└── README.md
```

---

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/ai-reporting-workflow.git
cd ai-reporting-workflow

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

No API keys required.

> **Optional (for image OCR):** install [Tesseract](https://github.com/tesseract-ocr/tesseract) on your system.

---

## Usage

### CLI

```bash
python main.py --input path/to/your/data/folder --out output/AI_Report.pdf
```

Optional title:

```bash
python main.py -i ./my_data -o output/Report.pdf -t "Q4 Sales Pipeline Review"
```

### Web UI

```bash
python app.py
```

Open **http://localhost:8080**

- Drag & drop files (or click to browse)
- Optional report title
- Click **Generate Report** → PDF downloads automatically

#### Optional Basic Auth

```bash
export REPORT_APP_USER=admin
export REPORT_APP_PASSWORD=change_me
python app.py
```

#### API endpoints

| Method | Path               | Auth     | Description                    |
|--------|--------------------|----------|--------------------------------|
| GET    | `/`                | No       | Web UI                         |
| GET    | `/health`          | No       | Health check                   |
| POST   | `/generate-report` | Optional | Upload files → download PDF    |

Example with curl:

```bash
curl -u admin:change_me \
  -F "files=@sales.csv" \
  -F "files=@notes.txt" \
  -F "title=Monthly Sales Report" \
  http://localhost:8080/generate-report \
  --output AI_Report.pdf
```

---

## Security notes

- File extension allowlist — unsupported types (e.g. `.exe`) are rejected
- 10 MB request size cap
- Isolated per-request temp directories (cleaned after response)
- Optional HTTP Basic Auth
- PII redaction (emails, phones, SSNs, card-like & Aadhaar-like numbers) before summarization

**Production recommendations:**
- Put behind HTTPS (nginx / Caddy / cloud load balancer)
- Add rate limiting (e.g. Flask-Limiter)
- Enable Basic Auth and keep credentials as secrets
- Consider malware scanning of uploads for public deployments

---

## Tech stack

Python · pandas · NumPy · matplotlib · ReportLab · pdfplumber · Flask · openpyxl · python-docx · python-pptx · Pillow · pytesseract

---

## Known gaps (for real production)

- No rate limiting
- No audit logging
- No antivirus scanning of uploads
- Basic Auth over plain HTTP is not safe — only use behind TLS

---

## License

MIT (or your preferred license)
