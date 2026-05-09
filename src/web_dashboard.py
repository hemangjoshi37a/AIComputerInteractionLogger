"""Interactive Web-Based Annotation & Session Editor Dashboard.

Provides a standalone, multi-threaded local web server that serves a gorgeous
glassmorphic single-page dashboard to preview, trim, AI-label, and export sessions.
"""

import os
import re
import csv
import json
import shutil
import zipfile
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs

try:
    from .dataset_exporter import DatasetExporter
    from .session_summarizer import SessionSummarizer
except ImportError:
    from dataset_exporter import DatasetExporter
    from session_summarizer import SessionSummarizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# HTML, CSS, and JS code embedded as a single premium glassmorphic single-page app
INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Interaction Logger - Web Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #0a0a0f;
            --card-bg: rgba(20, 20, 27, 0.7);
            --border-glow: rgba(0, 255, 255, 0.15);
            --accent-cyan: #00f2fe;
            --accent-purple: #4facfe;
            --text-main: #f0f4f8;
            --text-mute: #9aa8b6;
            --font-outfit: 'Outfit', sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background: radial-gradient(circle at top left, #12121e, var(--bg-deep));
            color: var(--text-main);
            font-family: var(--font-outfit);
            min-height: 100vh;
            overflow-x: hidden;
            padding-bottom: 40px;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 25px 50px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            background: rgba(10, 10, 15, 0.8);
            backdrop-filter: blur(12px);
            position: sticky;
            top: 0;
            z-index: 100;
        }

        header h1 {
            font-size: 24px;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .main-container {
            max-width: 1600px;
            margin: 40px auto;
            padding: 0 30px;
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 30px;
        }

        /* Glassmorphic Panel styling */
        .glass-panel {
            background: var(--card-bg);
            border: 1px solid var(--border-glow);
            border-radius: 16px;
            padding: 25px;
            backdrop-filter: blur(16px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        .glass-panel:hover {
            border-color: rgba(0, 255, 255, 0.3);
            box-shadow: 0 8px 32px 0 rgba(0, 255, 255, 0.05);
        }

        h2 {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            border-left: 3px solid var(--accent-cyan);
            padding-left: 10px;
        }

        /* Sessions List */
        .session-list {
            display: flex;
            flex-direction: column;
            gap: 15px;
            max-height: 700px;
            overflow-y: auto;
            padding-right: 5px;
        }

        .session-item {
            padding: 15px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .session-item:hover, .session-item.active {
            background: rgba(0, 255, 255, 0.05);
            border-color: var(--accent-cyan);
        }

        .session-item h3 {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 5px;
            color: var(--text-main);
        }

        .session-item p {
            font-size: 12px;
            color: var(--text-mute);
        }

        /* Session Player Panel */
        .player-grid {
            display: grid;
            grid-template-rows: auto 1fr auto;
            gap: 20px;
        }

        .canvas-container {
            position: relative;
            background: #000;
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 450px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .canvas-container img {
            max-width: 100%;
            max-height: 600px;
            object-fit: contain;
        }

        .coordinate-dot {
            position: absolute;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: rgba(0, 255, 255, 0.4);
            border: 2px solid var(--accent-cyan);
            transform: translate(-50%, -50%);
            pointer-events: none;
            display: none;
            box-shadow: 0 0 15px var(--accent-cyan);
            animation: pulse-glow 1s infinite alternate;
        }

        @keyframes pulse-glow {
            from { transform: translate(-50%, -50%) scale(1); }
            to { transform: translate(-50%, -50%) scale(1.3); }
        }

        /* Player Controls */
        .controls-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(255, 255, 255, 0.02);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .button-group {
            display: flex;
            gap: 10px;
        }

        button {
            padding: 10px 18px;
            border-radius: 8px;
            font-family: var(--font-outfit);
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
        }

        .btn-primary {
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-purple));
            color: #000;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 255, 255, 0.3);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.1);
        }

        .timeline-slider {
            width: 100%;
            margin: 15px 0;
            accent-color: var(--accent-cyan);
        }

        /* Timeline statistics and details */
        .workspace-layout {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
            margin-top: 30px;
        }

        /* Event logs */
        .log-terminal {
            font-family: var(--font-mono);
            background: rgba(5, 5, 10, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            max-height: 350px;
            overflow-y: auto;
            font-size: 12px;
        }

        .log-line {
            padding: 4px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.02);
            color: var(--text-mute);
        }

        .log-line.active {
            color: var(--accent-cyan);
            background: rgba(0, 255, 255, 0.05);
            font-weight: bold;
        }

        /* Forms and Labels */
        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--text-main);
        }

        .form-group input, .form-group textarea {
            width: 100%;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 12px;
            color: var(--text-main);
            font-family: var(--font-outfit);
            transition: border-color 0.2s ease;
        }

        .form-group input:focus, .form-group textarea:focus {
            outline: none;
            border-color: var(--accent-cyan);
        }

        ::-webkit-scrollbar {
            width: 6px;
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <header>
        <h1>🖥️ AI Computer Interaction Logger Dashboard</h1>
    </header>

    <div class="main-container">
        <!-- Sidebar - Session Browser -->
        <div class="glass-panel">
            <h2>Recording Sessions</h2>
            <div class="session-list" id="sessionList">
                <p style="color: var(--text-mute);">Loading sessions...</p>
            </div>
        </div>

        <!-- Main Panel - Player -->
        <div style="display: flex; flex-direction: column; gap: 30px;">
            <div class="glass-panel player-grid">
                <h2 id="currentSessionTitle">Visual Session Player</h2>
                
                <div class="canvas-container">
                    <img id="playerFrame" src="" alt="Session Frame Placeholder" style="display: none;">
                    <div class="coordinate-dot" id="cursorDot"></div>
                    <div id="noFrameText" style="color: var(--text-mute);">Select a session from the sidebar to begin playback</div>
                </div>

                <div>
                    <input type="range" class="timeline-slider" id="timeline" value="0" min="0" max="100" step="1">
                    <div class="controls-row">
                        <div class="button-group">
                            <button class="btn-secondary" id="btnPrev">⏪ Prev</button>
                            <button class="btn-primary" id="btnPlay">▶ Play</button>
                            <button class="btn-secondary" id="btnNext">Next ⏩</button>
                        </div>
                        <div id="timelineTime" style="font-family: var(--font-mono); color: var(--accent-cyan);">0.0s / 0.0s</div>
                    </div>
                </div>
            </div>

            <!-- Double Column Workspace -->
            <div class="workspace-layout">
                <!-- Left Panel - Interactive Annotation & Synthesis -->
                <div class="glass-panel">
                    <h2>AI Annotation & Meta-Labels</h2>
                    <div class="form-group">
                        <label for="taskGoal">Task Goal / Goal Description</label>
                        <input type="text" id="taskGoal" placeholder="Auto-generated high-level goal...">
                    </div>
                    <div class="form-group">
                        <label for="taskMilestones">Subtask Milestones (JSON string array)</label>
                        <textarea id="taskMilestones" rows="4" placeholder='["Step 1...", "Step 2..."]'></textarea>
                    </div>
                    <div class="form-group">
                        <label for="successCriteria">Success Criteria (JSON string array)</label>
                        <textarea id="successCriteria" rows="4" placeholder='["Condition 1...", "Condition 2..."]'></textarea>
                    </div>
                    <div class="button-group" style="margin-top: 20px;">
                        <button class="btn-primary" id="btnSaveMeta">💾 Save Labels</button>
                        <button class="btn-secondary" id="btnSynthesize" style="border-color: var(--accent-cyan);">🪄 Synthesize with LLM</button>
                    </div>
                </div>

                <!-- Right Panel - Streamed Action Events & Exporting -->
                <div style="display: flex; flex-direction: column; gap: 30px;">
                    <div class="glass-panel" style="flex: 1;">
                        <h2>Action Events Stream</h2>
                        <div class="log-terminal" id="logStream">
                            <div class="log-line">No events loaded.</div>
                        </div>
                    </div>

                    <div class="glass-panel">
                        <h2>Standardized Dataset Exporter</h2>
                        <div class="form-group">
                            <label for="exportFormat">Select Target Schema Format</label>
                            <select id="exportFormat" style="width:100%; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); border-radius:8px; padding:12px; color:var(--text-main);">
                                <option value="claude">Claude Computer Use API Schema</option>
                                <option value="osworld">OSWorld Trajectory Format</option>
                                <option value="huggingface">Hugging Face VLM JSONL Format</option>
                            </select>
                        </div>
                        <button class="btn-primary" id="btnExport" style="width: 100%;">📦 Export & Prepare Download ZIP</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let sessions = [];
        let activeSession = null;
        let activeEvents = [];
        let activeScreenshots = [];
        let isPlaying = false;
        let playInterval = null;
        let currentFrameIndex = 0;

        const sessionList = document.getElementById("sessionList");
        const currentSessionTitle = document.getElementById("currentSessionTitle");
        const playerFrame = document.getElementById("playerFrame");
        const cursorDot = document.getElementById("cursorDot");
        const noFrameText = document.getElementById("noFrameText");
        const timeline = document.getElementById("timeline");
        const timelineTime = document.getElementById("timelineTime");
        const logStream = document.getElementById("logStream");

        // Inputs
        const taskGoal = document.getElementById("taskGoal");
        const taskMilestones = document.getElementById("taskMilestones");
        const successCriteria = document.getElementById("successCriteria");

        // Buttons
        const btnPlay = document.getElementById("btnPlay");
        const btnPrev = document.getElementById("btnPrev");
        const btnNext = document.getElementById("btnNext");
        const btnSaveMeta = document.getElementById("btnSaveMeta");
        const btnSynthesize = document.getElementById("btnSynthesize");
        const btnExport = document.getElementById("btnExport");
        const exportFormat = document.getElementById("exportFormat");

        async function loadSessions() {
            try {
                const res = await fetch("/api/sessions");
                sessions = await res.json();
                sessionList.innerHTML = "";
                if (sessions.length === 0) {
                    sessionList.innerHTML = `<p style="color: var(--text-mute);">No recorded sessions found.</p>`;
                    return;
                }
                sessions.forEach(sess => {
                    const item = document.createElement("div");
                    item.className = "session-item";
                    item.innerHTML = `
                        <h3>${sess.id}</h3>
                        <p>Duration: ${sess.duration.toFixed(1)}s | Events: ${sess.event_count}</p>
                    `;
                    item.onclick = () => selectSession(sess.id);
                    sessionList.appendChild(item);
                });
            } catch (err) {
                console.error("Failed to load sessions:", err);
            }
        }

        async function selectSession(id) {
            isPlaying = false;
            clearInterval(playInterval);
            btnPlay.textContent = "▶ Play";

            try {
                const res = await fetch(`/api/session/${id}`);
                const data = await res.json();
                activeSession = id;
                activeEvents = data.events;
                activeScreenshots = data.screenshots;
                currentFrameIndex = 0;

                currentSessionTitle.textContent = `Session: ${id}`;
                noFrameText.style.display = "none";
                playerFrame.style.display = "block";

                // Populate annotations
                taskGoal.value = data.summary.task_goal || "";
                taskMilestones.value = JSON.stringify(data.summary.task_milestones || [], null, 2);
                successCriteria.value = JSON.stringify(data.summary.success_criteria || [], null, 2);

                timeline.max = activeScreenshots.length - 1;
                timeline.value = 0;

                renderEventsList();
                updateFrame();
            } catch (err) {
                console.error("Failed to load session:", err);
            }
        }

        function renderEventsList() {
            logStream.innerHTML = "";
            activeEvents.forEach((ev, idx) => {
                const line = document.createElement("div");
                line.className = "log-line";
                line.id = `log-line-${idx}`;
                line.textContent = `[${ev.timestamp.toFixed(1)}s] ${ev.event_type}: ${ev.raw_data}`;
                logStream.appendChild(line);
            });
        }

        function updateFrame() {
            if (!activeScreenshots.length) return;
            const step = activeScreenshots[currentFrameIndex];
            playerFrame.src = `/screenshots/${activeSession}/${step.filename}`;

            // Highlight corresponding event in the log stream
            document.querySelectorAll(".log-line").forEach(l => l.classList.remove("active"));
            
            // Find closest event
            let closestIdx = 0;
            let minDiff = Infinity;
            activeEvents.forEach((ev, idx) => {
                const diff = Math.abs(ev.timestamp - step.timestamp);
                if (diff < minDiff) {
                    minDiff = diff;
                    closestIdx = idx;
                }
            });

            const activeLine = document.getElementById(`log-line-${closestIdx}`);
            if (activeLine) {
                activeLine.classList.add("active");
                activeLine.scrollIntoView({ block: "nearest", behavior: "smooth" });
            }

            // Draw coordinate dot if mouse event
            const matchingEvent = activeEvents[closestIdx];
            if (matchingEvent && matchingEvent.coords) {
                const rect = playerFrame.getBoundingClientRect();
                // Map logical coordinate based on scale
                const x_perc = matchingEvent.coords[0] / 1920; // assumed max width, logic handles it
                const y_perc = matchingEvent.coords[1] / 1080;
                
                cursorDot.style.left = `${playerFrame.offsetLeft + (playerFrame.clientWidth * x_perc)}px`;
                cursorDot.style.top = `${playerFrame.offsetTop + (playerFrame.clientHeight * y_perc)}px`;
                cursorDot.style.display = "block";
            } else {
                cursorDot.style.display = "none";
            }

            timeline.value = currentFrameIndex;
            const total = activeEvents[activeEvents.length-1].timestamp - activeEvents[0].timestamp;
            const elapsed = total * (currentFrameIndex / (activeScreenshots.length - 1 || 1));
            timelineTime.textContent = `${elapsed.toFixed(1)}s / ${total.toFixed(1)}s`;
        }

        btnPlay.onclick = () => {
            if (isPlaying) {
                isPlaying = false;
                clearInterval(playInterval);
                btnPlay.textContent = "▶ Play";
            } else {
                isPlaying = true;
                btnPlay.textContent = "⏸ Pause";
                playInterval = setInterval(() => {
                    currentFrameIndex = (currentFrameIndex + 1) % activeScreenshots.length;
                    updateFrame();
                }, 500);
            }
        };

        btnPrev.onclick = () => {
            if (currentFrameIndex > 0) {
                currentFrameIndex--;
                updateFrame();
            }
        };

        btnNext.onclick = () => {
            if (currentFrameIndex < activeScreenshots.length - 1) {
                currentFrameIndex++;
                updateFrame();
            }
        };

        timeline.oninput = () => {
            currentFrameIndex = parseInt(timeline.value);
            updateFrame();
        };

        btnSaveMeta.onclick = async () => {
            if (!activeSession) return;
            const payload = {
                task_goal: taskGoal.value,
                task_milestones: JSON.parse(taskMilestones.value || "[]"),
                success_criteria: JSON.parse(successCriteria.value || "[]")
            };

            const res = await fetch(`/api/session/${activeSession}/save`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (data.status === "success") {
                alert("Labels successfully saved!");
            }
        };

        btnSynthesize.onclick = async () => {
            if (!activeSession) return;
            btnSynthesize.textContent = "🪄 Synthesizing...";
            const res = await fetch(`/api/session/${activeSession}/synthesize`, { method: "POST" });
            const data = await res.json();
            btnSynthesize.textContent = "🪄 Synthesize with LLM";
            if (data.status === "success") {
                taskGoal.value = data.summary.task_goal || "";
                taskMilestones.value = JSON.stringify(data.summary.task_milestones || [], null, 2);
                successCriteria.value = JSON.stringify(data.summary.success_criteria || [], null, 2);
                alert("AI synthesis successfully completed!");
            } else {
                alert("AI Synthesis failed. Check console and logger.log.");
            }
        };

        btnExport.onclick = async () => {
            if (!activeSession) return;
            btnExport.textContent = "📦 Exporting...";
            const format = exportFormat.value;
            const res = await fetch(`/api/session/${activeSession}/export?format=${format}`, { method: "POST" });
            const data = await res.json();
            btnExport.textContent = "📦 Export & Prepare Download ZIP";
            if (data.status === "success") {
                window.location.href = `/download/${data.zip_filename}`;
            } else {
                alert("Export failed.");
            }
        };

        window.onload = loadSessions;
    </script>
</body>
</html>
"""


class WebDashboardHandler(BaseHTTPRequestHandler):
    """Handles REST and visualization asset requests for our Web Dashboard."""

    def log_message(self, format, *args):
        # Override to suppress verbose terminal spam of request requests
        pass

    def _set_headers(self, content_type: str = "text/html", status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(status=200)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # 1. Main visual page
        if path == "/" or path == "/index.html":
            self._set_headers("text/html")
            self.wfile.write(INDEX_HTML.encode('utf-8'))
            return

        # 2. API: List all recording sessions
        if path == "/api/sessions":
            sessions_dir = "dataset"
            sessions_list = []
            if os.path.exists(sessions_dir):
                for item in os.listdir(sessions_dir):
                    session_path = os.path.join(sessions_dir, item)
                    events_csv = os.path.join(session_path, "events.csv")
                    if os.path.isdir(session_path) and os.path.exists(events_csv):
                        try:
                            # Count events and determine duration
                            duration = 0.0
                            count = 0
                            with open(events_csv, 'r', encoding='utf-8') as f:
                                reader = csv.DictReader(f)
                                timestamps = []
                                for row in reader:
                                    timestamps.append(float(row["Timestamp"]))
                                    count += 1
                                if timestamps:
                                    duration = max(timestamps) - min(timestamps)
                            
                            sessions_list.append({
                                "id": item,
                                "duration": duration,
                                "event_count": count
                            })
                        except Exception as e:
                            logging.error(f"Failed to read metadata for session {item}: {e}")

            self._set_headers("application/json")
            self.wfile.write(json.dumps(sessions_list).encode('utf-8'))
            return

        # 3. API: Load individual session structured details
        match = re.match(r"^/api/session/([^/]+)$", path)
        if match:
            session_id = match.group(1)
            session_dir = os.path.join("dataset", session_id)
            exporter = DatasetExporter()
            events = exporter.load_session_events(session_dir)

            # Get list of captured screenshots
            screenshots = []
            ss_dir = os.path.join(session_dir, "screenshots")
            if os.path.exists(ss_dir):
                for filename in sorted(os.listdir(ss_dir)):
                    if filename.endswith(".png"):
                        # Extract timestamp from screenshot filename (e.g. screenshot_170000000.png)
                        try:
                            ts = float(filename.replace("screenshot_", "").replace(".png", ""))
                        except:
                            ts = 0.0
                        screenshots.append({
                            "filename": filename,
                            "timestamp": ts
                        })

            # Read existing summaries
            summary_file = os.path.join("summaries", f"{session_id}_summary.json")
            summary_data = {}
            if os.path.exists(summary_file):
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        summary_data = json.load(f)
                except Exception as e:
                    logging.error(f"Error loading summary for session {session_id}: {e}")

            self._set_headers("application/json")
            self.wfile.write(json.dumps({
                "events": events,
                "screenshots": screenshots,
                "summary": summary_data
            }).encode('utf-8'))
            return

        # 4. Static Asset: Serve screenshot PNGs
        ss_match = re.match(r"^/screenshots/([^/]+)/([^/]+)$", path)
        if ss_match:
            session_id, filename = ss_match.group(1), ss_match.group(2)
            img_path = os.path.join("dataset", session_id, "screenshots", filename)
            if os.path.exists(img_path):
                self._set_headers("image/png")
                with open(img_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers("text/plain", 404)
                self.wfile.write(b"Screenshot not found.")
            return

        # 5. Static Asset: Download zipped exports
        dl_match = re.match(r"^/download/([^/]+)$", path)
        if dl_match:
            filename = dl_match.group(1)
            zip_path = os.path.join("exported_datasets", filename)
            if os.path.exists(zip_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f"attachment; filename={filename}")
                self.end_headers()
                with open(zip_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers("text/plain", 404)
                self.wfile.write(b"File not found.")
            return

        self._set_headers("text/plain", 404)
        self.wfile.write(b"Path not found.")

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b""

        # 1. API: Save customized annotations/metadata
        save_match = re.match(r"^/api/session/([^/]+)/save$", path)
        if save_match:
            session_id = save_match.group(1)
            payload = json.loads(post_data.decode('utf-8'))

            # Create summaries folder if not exists
            os.makedirs("summaries", exist_ok=True)
            summary_file = os.path.join("summaries", f"{session_id}_summary.json")

            existing_summary = {}
            if os.path.exists(summary_file):
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        existing_summary = json.load(f)
                except:
                    pass

            # Update fields
            existing_summary["task_goal"] = payload.get("task_goal")
            existing_summary["task_milestones"] = payload.get("task_milestones")
            existing_summary["success_criteria"] = payload.get("success_criteria")

            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(existing_summary, f, indent=2)

            self._set_headers("application/json")
            self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            return

        # 2. API: Trigger AI Goal Synthesis via VLM Summarizer
        synth_match = re.match(r"^/api/session/([^/]+)/synthesize$", path)
        if synth_match:
            session_id = synth_match.group(1)
            session_dir = os.path.join("dataset", session_id)

            # Force summarization triggering
            summarizer = SessionSummarizer()
            # Ensure use_llm is temporarily enabled for this manual web trigger if key exists
            if summarizer.llm_api_key:
                summarizer.use_llm = True
                summarizer.enabled = True

            summary = summarizer.summarize_session(session_dir)

            if summary:
                self._set_headers("application/json")
                self.wfile.write(json.dumps({
                    "status": "success",
                    "summary": {
                        "task_goal": summary.task_goal,
                        "task_milestones": summary.task_milestones,
                        "success_criteria": summary.success_criteria
                    }
                }).encode('utf-8'))
            else:
                self._set_headers("application/json", 500)
                self.wfile.write(json.dumps({"status": "failed", "error": "AI Synthesis failed"}).encode('utf-8'))
            return

        # 3. API: Run target Exporter and package into Downloadable ZIP
        export_match = re.match(r"^/api/session/([^/]+)/export$", path)
        if export_match:
            session_id = export_match.group(1)
            session_dir = os.path.join("dataset", session_id)

            query_params = parse_qs(parsed_url.query)
            target_format = query_params.get("format", ["claude"])[0]

            exporter = DatasetExporter()
            output_dir = os.path.join("exported_datasets", f"{session_id}_{target_format}")

            # Get dynamic goals if synthesized, else generic default
            summary_file = os.path.join("summaries", f"{session_id}_summary.json")
            goal = "Perform computer task"
            if os.path.exists(summary_file):
                try:
                    with open(summary_file, 'r', encoding='utf-8') as f:
                        goal = json.load(f).get("task_goal", goal)
                except:
                    pass

            # Run specific exporter
            if target_format == "claude":
                exporter.export_to_claude_computer_use(session_dir, output_dir)
            elif target_format == "osworld":
                exporter.export_to_osworld(session_dir, output_dir)
            elif target_format == "huggingface":
                exporter.export_to_huggingface_vlm(session_dir, output_dir, goal_instruction=goal)

            # Package output directory into a standard .zip
            zip_filename = f"{session_id}_{target_format}.zip"
            zip_path = os.path.join("exported_datasets", zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_f:
                for root, _, files in os.walk(output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Relative path inside zip
                        rel_path = os.path.relpath(file_path, output_dir)
                        zip_f.write(file_path, rel_path)

            # Cleanup export folder, leaving only the zipped bundle
            shutil.rmtree(output_dir, ignore_errors=True)

            self._set_headers("application/json")
            self.wfile.write(json.dumps({
                "status": "success",
                "zip_filename": zip_filename
            }).encode('utf-8'))
            return

        self._set_headers("text/plain", 404)
        self.wfile.write(b"Endpoint not found.")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """High-performance multi-threaded HTTP server to support visual frame streaming."""
    pass


def start_dashboard_server(port: int = 8080):
    """Start the multi-threaded Web Dashboard server."""
    server_address = ('', port)
    httpd = ThreadedHTTPServer(server_address, WebDashboardHandler)
    logging.info(f"Dashboard server successfully started at: http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Stopping dashboard server...")
        httpd.server_close()


if __name__ == "__main__":
    start_dashboard_server(9090)
