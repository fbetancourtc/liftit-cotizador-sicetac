"""
Vercel serverless function handler - Minimal Debug Version
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="SICETAC Debug",
    root_path="/sicetac"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "message": "Minimal API is working",
        "mode": "debug",
        "root_path": app.root_path,
        "env": {
            "BASE_PATH": os.environ.get('BASE_PATH', 'not set'),
            "SUPABASE_PROJECT_URL": "configured" if os.environ.get('SUPABASE_PROJECT_URL') else "missing"
        }
    }

@app.get("/api/config")
async def get_config():
    return {
        "supabase_url": os.environ.get("SUPABASE_PROJECT_URL", ""),
        "supabase_anon_key": os.environ.get("SUPABASE_ANON_KEY", "")
    }

@app.get("/")
async def root():
    return {"message": "SICETAC API", "status": "debug mode"}

# Handler for Vercel
handler = app