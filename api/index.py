import os
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime

app = FastAPI(title="AdVantage AI ERP")

# Root directory discovery for Vercel/Local
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = ROOT_DIR / "data"

# Serve static files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
templates = Jinja2Templates(directory=str(FRONTEND_DIR))

def load_json(filename):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

# --- Page Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/agent", response_class=HTMLResponse)
async def read_agent(request: Request):
    return templates.TemplateResponse(request=request, name="agent.html")

@app.get("/team", response_class=HTMLResponse)
async def read_team(request: Request):
    return templates.TemplateResponse(request=request, name="team.html")

@app.get("/settings", response_class=HTMLResponse)
async def read_settings(request: Request):
    return templates.TemplateResponse(request=request, name="settings.html")

@app.get("/camp", response_class=HTMLResponse)
async def read_campaigns(request: Request):
    return templates.TemplateResponse(request=request, name="camp.html")

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

import google.generativeai as genai

@app.post("/api/settings/save_key")
async def save_key(data: dict):
    key = data.get("key")
    if not key:
        return {"error": "Key is required"}, 400
    
    config = load_json("config.json") or {}
    config["GOOGLE_API_KEY"] = key
    
    path = DATA_DIR / "config.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
        
    return {"message": "Key saved successfully"}

@app.post("/api/agent/ask")
async def ask_agent(query: dict):
    text = query.get('text', '')
    
    config = load_json("config.json") or {}
    api_key = config.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        return {
            "response": "Gemini API 키가 설정되지 않았습니다. [설정] 메뉴에서 API 키를 먼저 등록해 주세요.",
            "timestamp": datetime.now().isoformat()
        }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Pull context from ERP data
        stats = load_json("stats.json") or {}
        campaigns = load_json("campaigns.json") or []
        
        prompt = f"""
        당신은 AdVantage AI ERP의 전문 비즈니스 분석가입니다. 
        사용자의 질문에 현재의 비즈니스 데이터를 바탕으로 전문적이고 친절하게 답변해 주세요.
        
        현재 데이터 요약:
        - 매출: {stats.get('revenue', {}).get('value', 'N/A')} ({stats.get('revenue', {}).get('trend', '')})
        - ROAS: {stats.get('avg_roas', {}).get('value', 'N/A')}
        - 활성 캠페인 수: {len(campaigns)}
        
        사용자 질문: {text}
        
        전문적인 금융/마케팅 톤으로 답변해 주세요. 한국어로 답변해 주세요.
        """
        
        response = model.generate_content(prompt)
        return {
            "response": response.text,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "response": f"Gemini 엔진 호출 중 오류가 발생했습니다: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
