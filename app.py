"""FastAPI web demo for DOCX PII Redaction.

Upload a .docx file, download the redacted version.
"""

import io
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse

from pii_redactor.main import redact_document

app = FastAPI(title="DOCX PII Redaction System")


@app.get("/", response_class=HTMLResponse)
async def index():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DOCX PII Redaction</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           background: #f5f5f5; display: flex; justify-content: center;
           align-items: center; min-height: 100vh; }
    .card { background: white; border-radius: 12px; padding: 40px;
            box-shadow: 0 2px 20px rgba(0,0,0,0.08); max-width: 480px; width: 100%; }
    h1 { font-size: 22px; margin-bottom: 8px; color: #1a1a1a; }
    p { color: #666; font-size: 14px; margin-bottom: 24px; }
    .upload-zone { border: 2px dashed #d0d0d0; border-radius: 8px; padding: 32px;
                   text-align: center; cursor: pointer; transition: all 0.2s; }
    .upload-zone:hover { border-color: #4a90d9; background: #f0f7ff; }
    .upload-zone.dragover { border-color: #4a90d9; background: #e8f2ff; }
    .upload-zone input { display: none; }
    .upload-zone .icon { font-size: 36px; margin-bottom: 8px; }
    .upload-zone .label { color: #888; font-size: 13px; }
    .btn { display: block; width: 100%; padding: 12px; margin-top: 16px;
           border: none; border-radius: 8px; font-size: 15px; font-weight: 600;
           cursor: pointer; transition: all 0.2s; }
    .btn-primary { background: #4a90d9; color: white; }
    .btn-primary:hover { background: #3a7bc8; }
    .btn-primary:disabled { background: #ccc; cursor: not-allowed; }
    .btn-download { background: #2ecc71; color: white; text-decoration: none;
                    display: block; text-align: center; margin-top: 16px;
                    padding: 12px; border-radius: 8px; font-weight: 600; }
    .btn-download:hover { background: #27ae60; }
    .status { margin-top: 16px; font-size: 13px; color: #888; text-align: center; }
    .stats { margin-top: 16px; background: #f9f9f9; border-radius: 8px; padding: 16px; }
    .stats h3 { font-size: 14px; margin-bottom: 8px; color: #333; }
    .stats div { font-size: 13px; color: #555; padding: 2px 0; }
    .hidden { display: none; }
  </style>
</head>
<body>
  <div class="card">
    <h1>DOCX PII Redaction</h1>
    <p>Upload a .docx file to detect and redact all PII with fake replacements.</p>

    <form id="form" enctype="multipart/form-data">
      <div class="upload-zone" id="dropzone" onclick="document.getElementById('file').click()">
        <div class="icon">&#128196;</div>
        <div class="label" id="filelabel">Click to select a .docx file</div>
        <input type="file" id="file" name="file" accept=".docx">
      </div>
      <button type="submit" class="btn btn-primary" id="submitBtn" disabled>Redact PII</button>
    </form>

    <div id="status" class="status hidden"></div>
    <div id="stats" class="stats hidden"></div>
    <a id="download" class="btn-download hidden" href="#">Download Redacted File</a>
  </div>

  <script>
    const form = document.getElementById('form');
    const fileInput = document.getElementById('file');
    const dropzone = document.getElementById('dropzone');
    const submitBtn = document.getElementById('submitBtn');
    const status = document.getElementById('status');
    const stats = document.getElementById('stats');
    const download = document.getElementById('download');
    const filelabel = document.getElementById('filelabel');

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        filelabel.textContent = fileInput.files[0].name;
        submitBtn.disabled = false;
      }
    });

    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => { dropzone.classList.remove('dragover'); });
    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      fileInput.files = e.dataTransfer.files;
      filelabel.textContent = fileInput.files[0].name;
      submitBtn.disabled = false;
    });

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!fileInput.files.length) return;

      submitBtn.disabled = true;
      status.textContent = 'Processing... Detecting and redacting PII.';
      status.classList.remove('hidden');
      stats.classList.add('hidden');
      download.classList.add('hidden');

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);

      try {
        const resp = await fetch('/redact', { method: 'POST', body: formData });
        if (!resp.ok) throw new Error('Redaction failed');

        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        download.href = url;
        download.download = fileInput.files[0].name.replace('.docx', '_redacted.docx');
        download.classList.remove('hidden');

        const meta = resp.headers.get('X-Redaction-Stats');
        if (meta) {
          const data = JSON.parse(meta);
          let html = '<h3>Redaction Summary</h3>';
          for (const [type, info] of Object.entries(data)) {
            html += `<div><strong>${type}</strong>: ${info.occurrences_replaced} replaced</div>`;
          }
          stats.innerHTML = html;
          stats.classList.remove('hidden');
        }

        status.textContent = 'Done! Your redacted document is ready.';
      } catch (err) {
        status.textContent = 'Error: ' + err.message;
      } finally {
        submitBtn.disabled = false;
      }
    });
  </script>
</body>
</html>"""


@app.post("/redact")
async def redact(file: UploadFile = File(...)):
    if not file.filename.endswith(".docx"):
        return HTMLResponse("Only .docx files are supported.", status_code=400)

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        return HTMLResponse("File too large (max 10MB).", status_code=400)

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp_in:
        tmp_in.write(content)
        tmp_in_path = tmp_in.name

    tmp_out_path = tmp_in_path.replace(".docx", "_redacted.docx")

    try:
        stats = redact_document(tmp_in_path, tmp_out_path)

        with open(tmp_out_path, "rb") as f:
            out_bytes = f.read()

        import json
        summary = {}
        for pii_type, data in stats.items():
            summary[pii_type] = {
                "unique_originals": data["unique_originals"],
                "occurrences_replaced": data["occurrences_replaced"],
            }

        return StreamingResponse(
            io.BytesIO(out_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{file.filename.replace(".docx", "_redacted.docx")}"',
                "X-Redaction-Stats": json.dumps(summary),
            },
        )
    finally:
        Path(tmp_in_path).unlink(missing_ok=True)
        Path(tmp_out_path).unlink(missing_ok=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
