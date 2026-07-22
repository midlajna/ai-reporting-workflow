"""
app.py
Minimal Flask backend exposing the pipeline as a web upload endpoint.

Security measures included:
  - HTTP Basic Auth (username/password from environment variables)
  - File extension allowlist (rejects anything not explicitly supported)
  - File size limit (default 10 MB per file)
  - Uploads saved to an isolated temp folder per request, deleted after
    the report is generated (nothing lingers on disk)
  - API key for Anthropic is read server-side only, never exposed to the client

Run:
    export ANTHROPIC_API_KEY=your_key
    export REPORT_APP_USER=admin
    export REPORT_APP_PASSWORD=change_me
    python app.py
"""
import os
import shutil
import tempfile
from functools import wraps
from pathlib import Path

from flask import Flask, request, send_file, jsonify, Response
from werkzeug.utils import secure_filename

from ingestion.universal_ingestor import TABULAR_EXTENSIONS, TEXT_EXTENSIONS, IMAGE_EXTENSIONS
from main import run_pipeline

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB per request, tune as needed

ALLOWED_EXTENSIONS = TABULAR_EXTENSIONS | TEXT_EXTENSIONS | IMAGE_EXTENSIONS


def check_auth(username, password):
    expected_user = os.environ.get("REPORT_APP_USER", "admin")
    expected_pass = os.environ.get("REPORT_APP_PASSWORD")
    if not expected_pass:
        raise EnvironmentError("Set REPORT_APP_PASSWORD before running the server.")
    return username == expected_user and password == expected_pass


def authenticate():
    return Response(
        "Authentication required.", 401,
        {"WWW-Authenticate": 'Basic realm="Report Generator"'}
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def is_allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/generate-report", methods=["POST"])
@requires_auth
def generate_report():
    if "files" not in request.files:
        return jsonify({"error": "No files provided. Use form field name 'files'."}), 400

    uploaded = request.files.getlist("files")
    if not uploaded:
        return jsonify({"error": "No files provided."}), 400

    rejected = [f.filename for f in uploaded if not is_allowed(f.filename)]
    if rejected:
        return jsonify({
            "error": "Unsupported file type(s)",
            "rejected": rejected,
            "allowed_extensions": sorted(ALLOWED_EXTENSIONS),
        }), 400

    # Isolated temp workspace per request — nothing persists between requests
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_dir = Path(tmp_dir) / "input"
        output_dir = Path(tmp_dir) / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        for f in uploaded:
            safe_name = secure_filename(f.filename)
            f.save(input_dir / safe_name)

        output_pdf = output_dir / "AI_Report.pdf"
        try:
            run_pipeline(str(input_dir), str(output_pdf))
        except Exception as e:
            return jsonify({"error": f"Pipeline failed: {e}"}), 500

        # Copy the finished PDF out before the temp dir is cleaned up
        final_path = Path(tempfile.gettempdir()) / f"report_{os.urandom(4).hex()}.pdf"
        shutil.copy(output_pdf, final_path)

    response = send_file(final_path, as_attachment=True, download_name="AI_Report.pdf")

    @response.call_on_close
    def cleanup():
        final_path.unlink(missing_ok=True)

    return response


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("WARNING: ANTHROPIC_API_KEY not set — LLM steps will fail.")
    if not os.environ.get("REPORT_APP_PASSWORD"):
        print("WARNING: REPORT_APP_PASSWORD not set — server will refuse to start on first request.")
    app.run(host="127.0.0.1", port=5000, debug=False)
