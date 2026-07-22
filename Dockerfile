# AI Reporting Workflow — production container
FROM python:3.12-slim

# System dependency for OCR (pytesseract needs the tesseract binary)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

ENV PORT=8080
EXPOSE 8080

# 2 workers, 120s timeout to allow for LLM + PDF generation time
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 2 --timeout 120 app:app"]
