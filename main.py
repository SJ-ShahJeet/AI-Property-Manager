"""
Yutori Matterport Tour Viewer
Watch the AI agent navigate through virtual tours in real-time
"""

import os
import time
import base64
from typing import Optional, List, Dict
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from yutori import YutoriClient

# Load environment variables
load_dotenv()

app = FastAPI(title="Yutori Matterport Viewer")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Yutori client
yutori_client = YutoriClient(api_key=os.getenv("YUTORI_API_KEY"))

# Store active sessions
active_sessions: Dict[str, dict] = {}


class TourRequest(BaseModel):
    url: str
    task: str = "Click the fullscreen button and then stop. Do nothing else."


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the frontend HTML"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yutori Matterport Viewer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        h1 {
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .subtitle {
            color: rgba(255,255,255,0.9);
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.1em;
        }

        .control-panel {
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .input-group {
            margin-bottom: 15px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #333;
        }

        input, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }

        input:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }

        textarea {
            resize: vertical;
            min-height: 80px;
        }

        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }

        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .viewer {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .status {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-weight: 500;
        }

        .status.running {
            background: #e3f2fd;
            color: #1976d2;
            border-left: 4px solid #1976d2;
        }

        .status.success {
            background: #e8f5e9;
            color: #388e3c;
            border-left: 4px solid #388e3c;
        }

        .status.error {
            background: #ffebee;
            color: #d32f2f;
            border-left: 4px solid #d32f2f;
        }

        .screenshot-container {
            position: relative;
            background: #f5f5f5;
            border-radius: 8px;
            overflow: hidden;
            min-height: 400px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .screenshot-container img {
            max-width: 100%;
            height: auto;
            display: block;
        }

        .loading {
            text-align: center;
            color: #666;
            padding: 40px;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .action-log {
            margin-top: 20px;
            max-height: 200px;
            overflow-y: auto;
            background: #f9f9f9;
            border-radius: 8px;
            padding: 15px;
        }

        .action-item {
            padding: 8px;
            margin-bottom: 5px;
            background: white;
            border-radius: 4px;
            font-size: 13px;
            border-left: 3px solid #667eea;
        }

        .timestamp {
            color: #999;
            font-size: 11px;
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Yutori Matterport Viewer</h1>
        <p class="subtitle">Watch the AI agent explore virtual tours in real-time</p>

        <div class="control-panel">
            <div class="input-group">
                <label for="tourUrl">Virtual Tour URL</label>
                <input
                    type="url"
                    id="tourUrl"
                    placeholder="https://discover.matterport.com/space/..."
                    value="https://discover.matterport.com/space/geQebf1HNtN"
                >
            </div>

            <div class="input-group">
                <label for="taskDescription">Task Description</label>
                <textarea
                    id="taskDescription"
                    placeholder="What should the agent do?"
                >Click the fullscreen button and then stop. Do nothing else.</textarea>
            </div>

            <button id="startBtn" onclick="startTour()">
                🚀 Start Tour Exploration
            </button>
        </div>

        <div class="viewer">
            <div id="status" class="status" style="display: none;"></div>

            <div class="screenshot-container" id="screenshotContainer">
                <div class="loading">
                    <p style="font-size: 18px; color: #999;">Click "Start Tour Exploration" to begin</p>
                </div>
            </div>

            <div class="action-log" id="actionLog" style="display: none;">
                <strong>Action Log:</strong>
                <div id="actionList"></div>
            </div>
        </div>
    </div>

    <script>
        let pollInterval = null;
        let currentSessionId = null;

        async function startTour() {
            const url = document.getElementById('tourUrl').value;
            const task = document.getElementById('taskDescription').value;
            const startBtn = document.getElementById('startBtn');
            const statusEl = document.getElementById('status');
            const screenshotContainer = document.getElementById('screenshotContainer');
            const actionLog = document.getElementById('actionLog');

            if (!url) {
                alert('Please enter a tour URL');
                return;
            }

            startBtn.disabled = true;
            startBtn.textContent = '⏳ Starting...';
            statusEl.style.display = 'block';
            statusEl.className = 'status running';
            statusEl.textContent = '🚀 Initializing Yutori agent...';
            actionLog.style.display = 'block';

            screenshotContainer.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Launching virtual browser...</p>
                </div>
            `;

            try {
                const response = await fetch('/start-tour', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ url, task })
                });

                const data = await response.json();

                if (data.session_id) {
                    currentSessionId = data.session_id;
                    addActionLog('Session started: ' + data.session_id);
                    pollProgress(data.session_id);
                } else {
                    throw new Error(data.error || 'Failed to start session');
                }

            } catch (error) {
                statusEl.className = 'status error';
                statusEl.textContent = '❌ Error: ' + error.message;
                startBtn.disabled = false;
                startBtn.textContent = '🚀 Start Tour Exploration';
            }
        }

        async function pollProgress(sessionId) {
            pollInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/session/${sessionId}`);
                    const data = await response.json();

                    updateUI(data);

                    if (data.status === 'succeeded' || data.status === 'failed') {
                        clearInterval(pollInterval);
                        document.getElementById('startBtn').disabled = false;
                        document.getElementById('startBtn').textContent = '🚀 Start Tour Exploration';
                    }
                } catch (error) {
                    console.error('Poll error:', error);
                }
            }, 2000);
        }

        function updateUI(data) {
            const statusEl = document.getElementById('status');
            const screenshotContainer = document.getElementById('screenshotContainer');

            // Update status
            if (data.status === 'running' || data.status === 'queued') {
                statusEl.className = 'status running';
                statusEl.textContent = `🔄 Agent is working... (Status: ${data.status})`;
            } else if (data.status === 'succeeded') {
                statusEl.className = 'status success';
                statusEl.innerHTML = '✅ Tour exploration completed! <a href="' + data.view_url + '" target="_blank" style="color: #1976d2; text-decoration: underline; margin-left: 10px;">📺 Watch Recording on Yutori</a>';
            } else if (data.status === 'failed') {
                statusEl.className = 'status error';
                statusEl.textContent = '❌ Task failed: ' + (data.error || 'Unknown error');
            }

            // Show view URL if available
            if (data.view_url) {
                screenshotContainer.innerHTML = `
                    <div style="text-align: center; padding: 40px;">
                        <h2 style="color: #667eea; margin-bottom: 20px;">🎬 Session Recording</h2>
                        <p style="color: #666; margin-bottom: 20px;">Yutori doesn't provide direct screenshots, but you can watch the full recording!</p>
                        <a href="${data.view_url}" target="_blank" style="
                            display: inline-block;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 15px 30px;
                            border-radius: 8px;
                            text-decoration: none;
                            font-weight: 600;
                            font-size: 16px;
                            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                        ">
                            📺 Watch on Yutori Platform
                        </a>
                        <p style="color: #999; margin-top: 20px; font-size: 14px;">The recording shows everything the agent did</p>
                    </div>
                `;
                addActionLog('View URL available');
            }

            // Update screenshot (if available - though unlikely)
            if (data.screenshot) {
                screenshotContainer.innerHTML = `
                    <img src="data:image/png;base64,${data.screenshot}" alt="Current view">
                `;
                addActionLog('Screenshot updated');
            }

            // Update actions
            if (data.actions && data.actions.length > 0) {
                data.actions.forEach(action => {
                    if (!window.loggedActions) window.loggedActions = new Set();
                    const actionKey = JSON.stringify(action);
                    if (!window.loggedActions.has(actionKey)) {
                        addActionLog(`${action.type}: ${action.description || 'N/A'}`);
                        window.loggedActions.add(actionKey);
                    }
                });
            }
        }

        function addActionLog(message) {
            const actionList = document.getElementById('actionList');
            const timestamp = new Date().toLocaleTimeString();
            const item = document.createElement('div');
            item.className = 'action-item';
            item.innerHTML = `<span class="timestamp">${timestamp}</span>${message}`;
            actionList.insertBefore(item, actionList.firstChild);

            // Keep only last 20 items
            while (actionList.children.length > 20) {
                actionList.removeChild(actionList.lastChild);
            }
        }

        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (pollInterval) {
                clearInterval(pollInterval);
            }
        });
    </script>
</body>
</html>
"""


@app.post("/start-tour")
def start_tour(request: TourRequest):
    """Start a new Yutori browsing session"""

    try:
        # Create browsing task using SDK
        task = yutori_client.browsing.create(
            task=request.task,
            start_url=request.url,
            max_steps=10  # Simple task - just fullscreen and stop
        )

        session_id = task.get("task_id") or task.get("id")
        view_url = task.get("view_url")

        if not session_id:
            raise HTTPException(status_code=500, detail="No session ID returned")

        # Store session info
        active_sessions[session_id] = {
            "id": session_id,
            "url": request.url,
            "task": request.task,
            "status": task.get("status", "queued"),
            "view_url": view_url,
            "created_at": datetime.now().isoformat(),
            "last_screenshot": None,
            "actions": []
        }

        return {
            "session_id": session_id,
            "status": "started",
            "view_url": view_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Yutori API error: {str(e)}")


@app.get("/session/{session_id}")
def get_session_status(session_id: str):
    """Get the current status and screenshot of a browsing session"""

    try:
        # Get task status using SDK
        data = yutori_client.browsing.get(session_id)

        # Extract useful information
        result = {
            "session_id": session_id,
            "status": data.get("status", "unknown"),
            "step": data.get("step", 0),
            "screenshot": None,
            "actions": [],
            "error": data.get("error"),
            "view_url": data.get("view_url")
        }

        # Get the latest screenshot if available
        if "screenshot" in data and data["screenshot"]:
            result["screenshot"] = data["screenshot"]
        elif "screenshots" in data and len(data["screenshots"]) > 0:
            result["screenshot"] = data["screenshots"][-1]

        # Get action history
        if "actions" in data:
            result["actions"] = data["actions"]

        # Update our local session storage
        if session_id in active_sessions:
            active_sessions[session_id].update({
                "status": result["status"],
                "last_screenshot": result["screenshot"],
                "step": result["step"]
            })

        return result

    except Exception as e:
        if session_id in active_sessions:
            # Return cached data if API call fails
            return active_sessions[session_id]
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")


@app.get("/sessions")
async def list_sessions():
    """List all active sessions"""
    return {"sessions": list(active_sessions.values())}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║  🤖 Yutori Matterport Viewer                            ║
    ║                                                          ║
    ║  Server running at: http://localhost:{port}              ║
    ║                                                          ║
    ║  Open the URL above in your browser to watch the        ║
    ║  AI agent explore virtual tours!                        ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=port)
