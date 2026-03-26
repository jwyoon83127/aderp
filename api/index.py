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

@app.post("/api/kakao/ask")
async def kakao_ask(request: Request):
    try:
        payload = await request.json()
        utterance = payload.get("userRequest", {}).get("utterance", "")
        
        # Call the existing AI logic (refactored into a helper for reuse)
        response_data = await get_ai_response(utterance)
        ai_text = response_data.get("response")

        return {
            "version": "2.0",
            "template": {
                "outputs": [
                    {
                        "simpleText": {
                            "text": ai_text
                        }
                    }
                ]
            }
        }
    except Exception as e:
        return {
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": f"에러가 발생했습니다: {str(e)}"}}]
            }
        }

async def get_ai_response(text: str):
    config = load_json("config.json") or {}
    api_key = config.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        return {"response": "Gemini API 키가 설정되지 않았습니다. ERP 설정에서 키를 등록해 주세요."}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        stats = load_json("stats.json") or {}
        campaigns = load_json("campaigns.json") or []
        
        prompt = f"""
        AdVantage AI ERP 비즈니스 분석가로서 답변해 주세요.
        현재 데이터: 매출 {stats.get('revenue', {}).get('value')}, {len(campaigns)}개 캠페인 운영 중.
        사용자 질문: {text}
        비즈니스 톤으로 한국어로 답변해 주세요.
        """
        
        response = model.generate_content(prompt)
        return {"response": response.text}
    except Exception as e:
        return {"response": f"AI 분석 중 오류가 발생했습니다: {str(e)}"}

@app.post("/api/agent/ask")
async def ask_agent(query: dict):
    text = query.get('text', '')
    res = await get_ai_response(text)
    return {
        "response": res["response"],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
