import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime

app = FastAPI(title="AdVantage AI ERP")

# Get the absolute path of the current directory (backend/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

# Serve static files (HTML, CSS, images if any)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

templates = Jinja2Templates(directory=FRONTEND_DIR)

# --- Page Routes ---

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    """CEO Dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/agent", response_class=HTMLResponse)
async def read_agent(request: Request):
    """AI Agent Interface"""
    return templates.TemplateResponse("agent.html", {"request": request})

@app.get("/team", response_class=HTMLResponse)
async def read_team(request: Request):
    """Team & Resources"""
    return templates.TemplateResponse("team.html", {"request": request})

@app.get("/camp", response_class=HTMLResponse)
async def read_campaigns(request: Request):
    """Campaign Performance Monitoring"""
    return templates.TemplateResponse("camp.html", {"request": request})

# --- Dynamic Data API Endpoints ---

@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """CEO Dashboard KPIs"""
    return {
        "revenue": {"value": "$124,500", "trend": "+12.5%", "status": "up"},
        "active_clients": {"value": "42", "trend": "+3 신규", "status": "up"},
        "avg_roas": {"value": "4.2x", "trend": "-0.3x", "status": "down"},
        "ai_efficiency": {"value": "94%", "trend": "최적화 활성", "status": "active"},
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/campaigns")
async def get_campaign_list():
    """Active Campaign List"""
    return [
        {"id": 1, "name": "Lumina Tech - 글로벌 확장", "channel": "FB 광고", "spend": "$12,400", "roas": "3.8x", "status": "active"},
        {"id": 2, "name": "Nexus 브랜드 인지도 강화", "channel": "구글 검색", "spend": "$8,200", "roas": "5.1x", "status": "active"},
        {"id": 3, "name": "Vantage 리테일 - 봄 세일", "channel": "인스타그램", "spend": "$15,600", "roas": "1.2x", "status": "warning"},
        {"id": 4, "name": "AdVantage New Season Launch", "channel": "유튜브", "spend": "$25,000", "roas": "4.5x", "status": "active"}
    ]

@app.get("/api/team")
async def get_team_data():
    """Team & Resource Utilization"""
    return {
        "resources": {
            "compute": {"value": 72, "trend": "+12%"},
            "bandwidth": {"value": 88, "status": "high"},
            "roi": {"value": "$4.2", "growth": "optimized"}
        },
        "members": [
            {"name": "홍길동", "role": "시니어 미디어 바이어", "clients": 12, "score": 98, "status": "Full-time", "tag": "FB 광고 전문가"},
            {"name": "김지수", "role": "크리에이티브 전략가", "projects": 8, "score": 92, "status": "Full-time", "tag": "영상 제작 총괄"}
        ]
    }

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
