import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime

app = FastAPI(title="AdVantage AI ERP")

import json

# Root directory discovery for Vercel/Local
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = ROOT_DIR / "data"

def load_json(filename):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# --- Page Routes ---
# ... (omitted for brevity in replacement, but I will keep them)

# --- Dynamic Data API Endpoints ---

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    data = load_json("stats.json")
    if data:
        data["last_updated"] = datetime.now().isoformat()
        return data
    return {"error": "Data not found"}

@app.get("/api/campaigns")
async def get_campaign_list():
    return load_json("campaigns.json") or []

@app.get("/api/team")
async def get_team_data():
    return load_json("team.json") or {"resources": {}, "members": []}

@app.get("/api/status")
async def get_system_status():
    return {"status": "Live", "cpu_usage": "12%", "memory_usage": "45%"}

@app.post("/api/agent/ask")
async def ask_agent(query: dict):
    text = query.get('text', '')
    # Simple semantic response logic
    if "매출" in text or "revenue" in text.lower():
        response = "이번 달 총 매출은 $124,500이며 전월 대비 12.5% 상승했습니다."
    elif "로아스" in text or "roas" in text.lower():
        response = "평균 ROAS는 4.2x로 목표치인 4.0x를 상회하고 있습니다."
    else:
        response = f"질문하신 '{text}'에 대해 분석 중입니다. 캠페인 최적화 제안을 확인하시겠습니까?"
    
    return {
        "response": response,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
