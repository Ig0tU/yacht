from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .cache import ensure_dirs, image_dir, read_json
from .image_ref import parse_image_ref
from .remote_docker import RemoteDocker, load_profile
from .registry import RegistryClient

app = FastAPI(title="Yacht Web Interface")

# Use a simple inline template for simplicity in this MVP
TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Yacht Web Interface</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #0B0F1A; color: white; }
        .card { background: #161C2C; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        input, button { padding: 10px; border-radius: 4px; border: 1px solid #2C3444; background: #0B0F1A; color: white; }
        button { background: #00D1FF; color: #0B0F1A; font-weight: bold; cursor: pointer; }
        pre { background: #000; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Yacht Web Interface</h1>

    <div class="card">
        <h2>Remote Status</h2>
        <div hx-get="/status" hx-trigger="load, every 10s">
            Checking remote status...
        </div>
    </div>

    <div class="card">
        <h2>Pull Image</h2>
        <form hx-post="/pull" hx-target="#pull-result" hx-indicator="#pull-indicator">
            <input type="text" name="image" placeholder="e.g. alpine:latest" style="width: 70%;">
            <button type="submit">Pull</button>
        </form>
        <div id="pull-indicator" class="htmx-indicator">Pulling...</div>
        <div id="pull-result"></div>
    </div>

    <div class="card">
        <h2>Run Container (Remote)</h2>
        <form hx-post="/run" hx-target="#run-result">
            <input type="text" name="image" placeholder="image" style="width: 30%;">
            <input type="text" name="cmd" placeholder="command (optional)" style="width: 40%;">
            <button type="submit">Run</button>
        </form>
        <div id="run-result"></div>
    </div>
</body>
</html>
"""

with open(TEMPLATES_DIR / "index.html", "w") as f:
    f.write(INDEX_HTML)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/status")
async def get_status():
    try:
        profile = load_profile()
        client = RemoteDocker(profile)
        pong = client.ping()
        return HTMLResponse(f"<strong>Host:</strong> {profile.host}<br><strong>Status:</strong> {pong}")
    except Exception as e:
        return HTMLResponse(f"<span style='color: red;'>Error: {e}</span>")

@app.post("/pull")
async def pull_image(image: str = Form(...)):
    try:
        ref = parse_image_ref(image)
        client = RegistryClient(ref)
        client.pull(platform="linux/arm64", with_layers=False)
        return HTMLResponse(f"<p style='color: #00FF94;'>Successfully pulled {image}</p>")
    except Exception as e:
        return HTMLResponse(f"<p style='color: red;'>Pull failed: {e}</p>")

@app.post("/run")
async def run_container(image: str = Form(...), cmd: str = Form(None)):
    try:
        profile = load_profile()
        remote = RemoteDocker(profile)
        remote.ensure_image(image)
        command = cmd.split() if cmd else None
        cid = remote.create_container(image=image, command=command)
        remote.start_container(cid)
        return HTMLResponse(f"<p style='color: #00FF94;'>Started container: <code>{cid[:12]}</code></p>")
    except Exception as e:
        return HTMLResponse(f"<p style='color: red;'>Run failed: {e}</p>")
