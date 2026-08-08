import json
import asyncio
import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route
from starlette.requests import Request
import uvicorn
from apex.config import Config, detect_hardware
from apex.core.orchestrator import AgentOrchestrator

logger = logging.getLogger("apex.web")

GLOBAL_AUTH_TOKEN: Optional[str] = None

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚡ APEX Assistant</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --accent-purple: #8b5cf6;
            --accent-blue: #3b82f6;
            --accent-red: #ef4444;
            --text-color: #f8fafc;
            --subtext: #94a3b8;
        }
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        header {
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .logo {
            font-size: 1.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .telemetry {
            font-size: 0.9rem;
            color: var(--subtext);
        }
        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
            padding: 1.5rem;
            box-sizing: border-box;
        }
        .chat-box {
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            padding-right: 0.5rem;
        }
        .msg {
            padding: 1rem 1.25rem;
            border-radius: 12px;
            max-width: 85%;
            line-height: 1.6;
        }
        .msg.user {
            background: var(--accent-blue);
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }
        .msg.apex {
            background: var(--card-bg);
            border: 1px solid rgba(255,255,255,0.08);
            align-self: flex-start;
            border-bottom-left-radius: 2px;
        }
        .msg.error {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid var(--accent-red);
            color: #fca5a5;
        }
        .controls {
            display: flex;
            gap: 0.75rem;
            margin-top: 1rem;
            background: var(--card-bg);
            padding: 0.75rem;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        input, button {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(255,255,255,0.15);
            color: var(--text-color);
            padding: 0.75rem 1rem;
            border-radius: 10px;
            font-size: 1rem;
            outline: none;
        }
        input {
            flex: 1;
        }
        button {
            background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue));
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: opacity 0.2s;
        }
        button:hover {
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">⚡ APEX Assistant</div>
        <div class="telemetry" id="telemetry">Detecting hardware...</div>
    </header>
    <main>
        <div class="chat-box" id="chat">
            <div class="msg apex">
                👋 Hello! I am APEX. Ask me anything—whether you need a document analyzed, research synthesized, datasets processed, or complex software built.
            </div>
        </div>
        <form class="controls" id="ask-form">
            <input type="text" id="prompt" placeholder="Ask APEX anything..." required autocomplete="off">
            <button type="submit">Send ✨</button>
        </form>
    </main>
    <script>
        const chat = document.getElementById('chat');
        const form = document.getElementById('ask-form');
        const promptInput = document.getElementById('prompt');

        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token') || '';
        const headers = {'Content-Type': 'application/json'};
        if (token) headers['Authorization'] = `Bearer ${token}`;

        fetch('/api/hardware', { headers }).then(r => r.json()).then(data => {
            if (data.error) {
                document.getElementById('telemetry').innerText = `Error: ${data.error}`;
            } else {
                document.getElementById('telemetry').innerText = `🎮 GPU: ${data.gpu_name} | CPU Cores: ${data.cpu_cores}`;
            }
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = promptInput.value.trim();
            if (!text) return;

            const userDiv = document.createElement('div');
            userDiv.className = 'msg user';
            userDiv.innerText = text;
            chat.appendChild(userDiv);
            promptInput.value = '';
            chat.scrollTop = chat.scrollHeight;

            const apexDiv = document.createElement('div');
            apexDiv.className = 'msg apex';
            apexDiv.innerText = 'Thinking... ⚡';
            chat.appendChild(apexDiv);
            chat.scrollTop = chat.scrollHeight;

            try {
                const res = await fetch('/api/ask', {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify({prompt: text})
                });
                const data = await res.json();
                if (data.status === 'error' || data.has_denial) {
                    apexDiv.className = 'msg apex error';
                }
                apexDiv.innerText = data.answer;
            } catch (err) {
                apexDiv.className = 'msg apex error';
                apexDiv.innerText = "Execution Error: " + err;
            }
            chat.scrollTop = chat.scrollHeight;
        });
    </script>
</body>
</html>
"""

def verify_token(request: Request) -> bool:
    if not GLOBAL_AUTH_TOKEN:
        return True
    auth_header = request.headers.get("Authorization", "")
    query_token = request.query_params.get("token", "")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token == GLOBAL_AUTH_TOKEN:
            return True
    if query_token == GLOBAL_AUTH_TOKEN:
        return True
    return False

async def homepage(request: Request):
    return HTMLResponse(HTML_TEMPLATE)

async def api_hardware(request: Request):
    if not verify_token(request):
        return JSONResponse({"error": "Unauthorized. Invalid or missing authentication token."}, status_code=401)
    specs = detect_hardware()
    return JSONResponse(specs.model_dump())

async def api_ask(request: Request):
    if not verify_token(request):
        return JSONResponse({"error": "Unauthorized. Invalid or missing authentication token."}, status_code=401)
    data = await request.json()
    prompt = data.get("prompt", "")
    
    config = Config.load()
    orchestrator = AgentOrchestrator(config)
    
    denial_reasons = []
    answer = ""
    status = "success"
    
    try:
        # Web requests run in unattended mode (is_interactive=False)
        async for event in orchestrator.run(prompt, is_interactive=False):
            ev_type = event.get("type")
            if ev_type == "governance_denial":
                denial_reasons.append(event.get("reason"))
                status = "governance_denied"
            elif ev_type == "thought":
                answer += event.get("text", "") + "\n"
            elif ev_type == "final":
                answer = event.get("content", answer)
                
        if denial_reasons:
            answer = "⚠️ Action Denied by Governance Policy:\n" + "\n".join(denial_reasons)
            
        return JSONResponse({"answer": answer, "status": status, "has_denial": len(denial_reasons) > 0})
    except Exception as e:
        return JSONResponse({"answer": f"Provider / System Error: {str(e)}", "status": "error", "has_denial": False}, status_code=500)

app = Starlette(routes=[
    Route('/', homepage),
    Route('/api/hardware', api_hardware),
    Route('/api/ask', api_ask, methods=['POST'])
])

def start_web_server(host: str = "127.0.0.1", port: int = 7860, auth_token: Optional[str] = None):
    global GLOBAL_AUTH_TOKEN
    GLOBAL_AUTH_TOKEN = auth_token or os.getenv("APEX_WEB_TOKEN")
    
    if host not in ["127.0.0.1", "localhost"]:
        if not GLOBAL_AUTH_TOKEN:
            raise ValueError(f"SECURITY WARNING: Non-loopback binding to '{host}' requires an authentication token. Provide via --token or APEX_WEB_TOKEN env var.")
        print(f"⚠️ SECURITY NOTICE: APEX Web Server bound to public host '{host}' with authentication token enforcement.")
        
    print(f"⚡ APEX Web Interface launching at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="error")
