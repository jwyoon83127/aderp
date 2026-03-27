import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseManager:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_ANON_KEY")
        if not url or not key:
             print("Warning: SUPABASE_URL or SUPABASE_ANON_KEY not set in environment.")
        self.client: Client = create_client(url, key)

    # --- Campaigns ---
    def get_campaigns(self):
        res = self.client.table("campaigns").select("*").order("created_at", desc=True).execute()
        return res.data or []

    def create_campaign(self, data: dict):
        new_row = {
            "name": data.get("name", "New Campaign"),
            "channel": data.get("channel", "Meta Ads"),
            "spend": float(data.get("spend", "0").replace("$", "").replace(",", "")),
            "roas": float(data.get("roas", "0.0").replace("x", "")),
            "status": data.get("status", "active")
        }
        res = self.client.table("campaigns").insert(new_row).execute()
        return res.data[0] if res.data else None

    def delete_campaign(self, name: str):
        res = self.client.table("campaigns").delete().eq("name", name).execute()
        return res.data

    # --- Projects & Team ---
    def get_team_data(self):
        # Fetch summary, projects, and team workload
        # For simplicity in this bridge, we'll mimic the team.json structure
        projects_res = self.client.table("projects").select("*").order("created_at", desc=True).execute()
        members_res = self.client.table("team_members").select("*").execute()
        
        projects = projects_res.data or []
        team_members = members_res.data or []
        
        # Calculate summary
        summary = {
            "active_projects": len(projects),
            "on_track": len([p for p in projects if p["status"] == "원활"]),
            "delayed": len([p for p in projects if p["status"] == "지연"]),
            "at_risk": len([p for p in projects if p["status"] == "이슈"]),
            "avg_progress": round(sum(p.get("progress", 0) for p in projects) / len(projects)) if projects else 0
        }
        
        # In this mock-to-real migration, we'll keep the project members as names in the response
        # In a real app, we'd query project_members N:N, but for compatibility with current frontend:
        return {
            "summary": summary,
            "projects": projects,
            "team_workload": team_members
        }

    def create_project(self, data: dict):
        # Get next project code
        res = self.client.table("projects").select("project_code").order("project_code", desc=True).limit(1).execute()
        next_code = "PRJ-001"
        if res.data:
            last_code = res.data[0]["project_code"]
            try:
                num = int(last_code.replace("PRJ-", ""))
                next_code = f"PRJ-{num + 1:03d}"
            except: pass

        new_row = {
            "project_code": next_code,
            "name": data.get("name", "New Project"),
            "client": data.get("client", ""),
            "progress": 0,
            "status": "원활",
            "deadline": data.get("deadline"),
            "priority": data.get("priority", "Medium")
        }
        res = self.client.table("projects").insert(new_row).execute()
        return res.data[0] if res.data else None

    # --- Stats ---
    def get_stats(self):
        res = self.client.table("dashboard_stats").select("*").execute()
        stats_dict = {}
        for row in res.data:
            stats_dict[row["metric_key"]] = {
                "value": row["value"],
                "trend": row["trend"]
            }
        return stats_dict

    # --- Config ---
    def get_config(self, key: str = None):
        if key:
            res = self.client.table("app_config").select("config_value").eq("config_key", key).maybe_single().execute()
            return res.data["config_value"] if res.data else None
        else:
            res = self.client.table("app_config").select("*").execute()
            return {row["config_key"]: row["config_value"] for row in res.data}

    def save_config(self, key: str, value: dict):
        res = self.client.table("app_config").upsert({
            "config_key": key,
            "config_value": value
        }, on_conflict="config_key").execute()
        return res.data

db = SupabaseManager()
