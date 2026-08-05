#!/usr/bin/env python3
"""
app.py – Minimal Flask frontend + API for ai-reporting-workflow

Endpoints:
  GET  /          → web UI
  GET  /health    → health check (no auth)
  POST /generate-report → upload files, get PDF back
"""

import os
import shutil
import tempfile
from pathlib import Path
from functools import wraps

from flask import (
    Flask, request, send_file, jsonify, render_template,
    Response, abort
)
from werkzeug.utils import secure_filename

from main import run_pipeline

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {
    ".csv", ".xlsx", ".xls", ".json",
    ".pdf", ".txt", ".docx", ".pptx",
    ".png", ".jpg", ".jpeg",
}

# Optional Basic Auth (set via env vars)
AUTH_USER = os.environ.get("REPORT_APP_USER")
AUTH_PASS = os.environ.get("REPORT_APP_PASSWORD")


def check_auth(username: str, password: str) -> bool:
    if not AUTH_USER or not AUTH_PASS:
        return True  # auth disabled if env vars not set
    return username == AUTH_USER and password == AUTH_PASS


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not AUTH_USER or not AUTH_PASS:
            return f(*args, **kwargs)
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                "Authentication required",
                401,
                {"WWW-Authenticate": 'Basic realm="AI Report Generator"'},
            )
        return f(*args, **kwargs)
    return decorated


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate-report", methods=["POST"])
@requires_auth
def generate_report():
    if "files" not in request.files and "files[]" not in request.files:
        # Accept both "files" and "files[]" field names
        files = request.files.getlist("files") or request.files.getlist("files[]")
    else:
        files = request.files.getlist("files") or request.files.getlist("files[]")

    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "No files uploaded"}), 400

    # Reject unsupported extensions early
    for f in files:
        if f.filename and not allowed_file(f.filename):
            return jsonify({
                "error": f"Unsupported file type: {f.filename}. "
                         f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            }), 400

    tmp_dir = Path(tempfile.mkdtemp(prefix="report_upload_"))
    try:
        for f in files:
            if f.filename:
                safe_name = secure_filename(f.filename)
                f.save(tmp_dir / safe_name)

        output_path = tmp_dir / "AI_Report.pdf"
        title = request.form.get("title") or "AI Reporting Workflow – Analysis Report"

        run_pipeline(tmp_dir, output_path, title=title)

        if not output_path.exists():
            return jsonify({"error": "Report generation failed"}), 500

        return send_file(
            output_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="AI_Report.pdf",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp dir after response is sent is hard;
        # best-effort cleanup (file is already in memory for send_file)
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting AI Report Generator on http://0.0.0.0:{port}")
    if AUTH_USER and AUTH_PASS:
        print("Basic Auth is ENABLED")
    else:
        print("Basic Auth is DISABLED (set REPORT_APP_USER / REPORT_APP_PASSWORD to enable)")
    app.run(host="0.0.0.0", port=port, debug=False)
