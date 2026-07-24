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
    export REPORT_APP_USER=admin
    export REPORT_APP_PASSWORD=change_me
    python app.py
"""
import os
import shutil
import tempfile
from functools import wraps
from pathlib import Path

from flask import Flask, request, send_file, jsonify, render_template
from werkzeug.utils import secure_filename

from ingestion.universal_ingestor import TABULAR_EXTENSIONS, TEXT_EXTENSIONS, IMAGE_EXTENSIONS
from main import run_pipeline

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB per request, tune as needed

ALLOWED_EXTENSIONS = TABULAR_EXTENSIONS | TEXT_EXTENSIONS | IMAGE_EXTENSIONS

HOME_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Reporting Workflow</title>
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; background:#0d0d14; color:#e8e8f0;
         max-width:560px; margin:0 auto; padding:32px 20px; }
  h1 { font-size:1.5rem; color:#a99cff; margin-bottom:4px; }
  p.sub { color:#9a9ab0; margin-top:0; font-size:0.9rem; }
  label { display:block; margin:16px 0 6px; font-size:0.85rem; color:#c8c8dc; }
  input[type=text], input[type=password] { width:100%; padding:10px; border-radius:8px; border:1px solid #35354a;
         background:#16161f; color:#fff; box-sizing:border-box; }
  input[type=file] { width:100%; padding:10px 0; }
  button { margin-top:20px; width:100%; padding:12px; border:none; border-radius:8px;
         background:#5B4FDB; color:#fff; font-size:1rem; font-weight:600; cursor:pointer; }
  button:disabled { background:#3a3a55; }
  #status { margin-top:16px; font-size:0.9rem; white-space:pre-wrap; }
  a.download { display:inline-block; margin-top:12px; padding:10px 16px; background:#2fbf71;
         color:#0d0d14; border-radius:8px; text-decoration:none; font-weight:600; }
</style>
</head>
<body>
  <h1>AI Reporting Workflow</h1>
  <p class="sub">Upload sales data + supporting documents. Get back an AI-generated PDF report.</p>

  <form id="reportForm">
    <label>Username</label>
    <input type="text" id="username" required>

    <label>Password</label>
    <input type="password" id="password" required>

    <label>Files (CSV, XLSX, JSON, PDF, TXT, DOCX, PPTX, images)</label>
    <input type="file" id="files" multiple required>

    <button type="submit" id="submitBtn">Generate Report</button>
  </form>

  <div id="status"></div>

<script>
document.getElementById('reportForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('submitBtn');
  const statusEl = document.getElementById('status');
  const user = document.getElementById('username').value;
  const pass = document.getElementById('password').value;
  const files = document.getElementById('files').files;

  if (files.length === 0) { statusEl.textContent = 'Select at least one file.'; return; }

  const formData = new FormData();
  for (const f of files) formData.append('files', f);

  btn.disabled = true;
  statusEl.textContent = 'Generating report... this can take 20-60 seconds.';

  try {
    const resp = await fetch('/generate-report', {
      method: 'POST',
      headers: { 'Authorization': 'Basic ' + btoa(user + ':' + pass) },
      body: formData
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({error: resp.statusText}));
      statusEl.textContent = 'Error: ' + (err.error || resp.status);
      btn.disabled = false;
      return;
    }

    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    statusEl.innerHTML = 'Report ready. <br><a class="download" href="' + url + '" download="AI_Report.pdf">Download PDF</a>';
  } catch (err) {
    statusEl.textContent = 'Request failed: ' + err.message;
  }
  btn.disabled = false;
});
</script>
</body>
</html>
"""


def check_auth(username, password):
    expected_user = os.environ.get("REPORT_APP_USER", "admin")
    expected_pass = os.environ.get("REPORT_APP_PASSWORD")
    if not expected_pass:
        raise EnvironmentError("Set REPORT_APP_PASSWORD before running the server.")
    return username == expected_user and password == expected_pass


def authenticate():
    # Deliberately omit the WWW-Authenticate header. If present, browsers
    # intercept 401 responses at the network level and show their own
    # native login popup — even for fetch()/XHR calls with a manually set
    # Authorization header. Since this endpoint is only ever called from
    # our own page's JavaScript, we want our custom error message instead.
    return jsonify({"error": "Invalid username or password."}), 401


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


@app.route("/", methods=["GET"])
def home():
    return render_template("login.html")


@app.route("/upload", methods=["GET"])
def upload_page():
    return render_template("upload.html")


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
    if not os.environ.get("REPORT_APP_PASSWORD"):
        print("WARNING: REPORT_APP_PASSWORD not set — server will refuse to start on first request.")
    app.run(host="127.0.0.1", port=5000, debug=False)
  
