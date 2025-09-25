"""
Vercel Serverless Function - Fixed Handler
"""
from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Set response headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Route handling
        if self.path == '/api' or self.path == '/api/':
            response = {
                "message": "SICETAC API is running",
                "status": "ok"
            }
        elif self.path == '/api/health':
            response = {
                "status": "ok",
                "message": "API is working",
                "mode": "serverless"
            }
        elif self.path == '/api/config':
            import os
            response = {
                "supabase_url": os.environ.get("SUPABASE_PROJECT_URL", ""),
                "supabase_anon_key": os.environ.get("SUPABASE_ANON_KEY", "")
            }
        else:
            response = {
                "error": "Not found",
                "path": self.path
            }

        # Write response
        self.wfile.write(json.dumps(response).encode())
        return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return