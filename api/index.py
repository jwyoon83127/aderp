import os
import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AdVantage AI ERP")

# Root directory discovery for Vercel/Local
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = ROOT_DIR / "data"

# Serve static files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
templates = Jinja2Templates(directory=str(FRONTEND_DIR))

# --- Supabase Database Connection ---
try:
    from api.database import db
except ImportError:
    from database import db

# Fallback: load from local JSON if Supabase is unavailable
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

# --- Dynamic Data API Endpoints (Supabase) ---

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    try:
        stats = db.get_stats()
        if stats:
            stats["last_updated"] = datetime.now().isoformat()
            return stats
    except Exception as e:
        print(f"Supabase stats error: {e}")
    # Fallback to JSON
    data = load_json("stats.json")
    if data:
        data["last_updated"] = datetime.now().isoformat()
        return data
    return {"error": "Data not found"}

@app.get("/api/campaigns")
async def get_campaign_list():
    try:
        return db.get_campaigns()
    except Exception as e:
        print(f"Supabase campaigns error: {e}")
        return load_json("campaigns.json") or []

@app.post("/api/campaigns")
async def create_campaign(data: dict):
    try:
        result = db.create_campaign(data)
        return {"message": "Campaign created successfully", "campaign": result}
    except Exception as e:
        print(f"Supabase create campaign error: {e}")
        return {"error": str(e)}, 500

@app.delete("/api/campaigns")
async def delete_campaign(data: dict):
    try:
        name_to_delete = data.get("name", "")
        db.delete_campaign(name_to_delete)
        return {"message": "Campaign deleted successfully"}
    except Exception as e:
        print(f"Supabase delete campaign error: {e}")
        return {"error": str(e)}, 500

@app.get("/api/team")
async def get_team_data():
    try:
        return db.get_team_data()
    except Exception as e:
        print(f"Supabase team error: {e}")
        return load_json("team.json") or {"resources": {}, "members": []}

@app.post("/api/team/projects")
async def create_project(data: dict):
    try:
        result = db.create_project(data)
        return {"message": "Project created successfully", "project": result}
    except Exception as e:
        print(f"Supabase create project error: {e}")
        return {"error": str(e)}, 500

@app.post("/api/settings/save_profile")
async def save_profile(data: dict):
    try:
        profile = {
            "name": data.get("name", ""),
            "email": data.get("email", "")
        }
        db.save_config("PROFILE", profile)
        return {"message": "Profile saved successfully"}
    except Exception as e:
        print(f"Supabase save profile error: {e}")
        return {"error": str(e)}, 500

@app.get("/api/settings/config")
async def get_settings_config():
    try:
        all_config = db.get_config()
        profile = all_config.get("PROFILE", {})
        has_gemini = bool(all_config.get("GOOGLE_API_KEY"))

        ad_channels = all_config.get("AD_CHANNELS", {})
        masked_channels = {}
        if isinstance(ad_channels, dict):
            for channel, creds in ad_channels.items():
                if isinstance(creds, dict):
                    masked_channels[channel] = {
                        k: ("****" + v[-4:] if v and isinstance(v, str) and len(v) > 4 else bool(v))
                        for k, v in creds.items()
                    }

        return {
            "profile": profile,
            "has_gemini_key": has_gemini,
            "ad_channels": masked_channels
        }
    except Exception as e:
        print(f"Supabase config error: {e}")
        return {"profile": {}, "has_gemini_key": False, "ad_channels": {}}

@app.get("/api/status")
async def get_system_status():
    return {"status": "Live", "cpu_usage": "12%", "memory_usage": "45%"}

import google.generativeai as genai

@app.post("/api/settings/save_key")
async def save_key(data: dict):
    key = data.get("key")
    if not key:
        return {"error": "Key is required"}, 400
    try:
        db.save_config("GOOGLE_API_KEY", {"key": key})
        return {"message": "Key saved successfully"}
    except Exception as e:
        print(f"Supabase save key error: {e}")
        return {"error": str(e)}, 500

@app.post("/api/settings/save_ad_keys")
async def save_ad_keys(data: dict):
    ad_channels = {
        "meta": {
            "token": data.get("meta_token"),
            "account_id": data.get("meta_account")
        },
        "google": {
            "dev_token": data.get("google_token"),
            "customer_id": data.get("google_id")
        },
        "kakao": {
            "api_key": data.get("kakao_key"),
            "channel_id": data.get("kakao_channel")
        }
    }
    try:
        db.save_config("AD_CHANNELS", ad_channels)
        return {"message": "Credentials saved. Initializing data sync..."}
    except Exception as e:
        print(f"Supabase save ad keys error: {e}")
        return {"error": str(e)}, 500

@app.post("/api/kakao/ask")
async def kakao_ask(request: Request):
    try:
        payload = await request.json()
        utterance = payload.get("userRequest", {}).get("utterance", "")
        response_data = await get_ai_response(utterance)
        ai_text = response_data.get("response")
        return {
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": ai_text}}]
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
    # Try Supabase config first, then env
    api_key = None
    try:
        key_config = db.get_config("GOOGLE_API_KEY")
        if key_config and isinstance(key_config, dict):
            api_key = key_config.get("key")
    except:
        pass
    
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        return {"response": "Gemini API 키가 설정되지 않았습니다. ERP 설정에서 키를 등록해 주세요."}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')

        # Get data from Supabase for context
        stats = db.get_stats()
        campaigns = db.get_campaigns()

        revenue = stats.get("total_revenue", {}).get("value", "N/A") if stats else "N/A"
        camp_count = len(campaigns) if campaigns else 0

        prompt = f"""
        AdVantage AI ERP 비즈니스 분석가로서 답변해 주세요.
        현재 데이터: 매출 {revenue}, {camp_count}개 캠페인 운영 중.
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
