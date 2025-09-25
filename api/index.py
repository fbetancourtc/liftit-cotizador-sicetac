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

        # Debug: Show what path we're receiving
        import os

        # Always return success with debug info
        response = {
            "status": "ok",
            "message": "API is working",
            "debug": {
                "path": self.path,
                "method": "GET",
                "headers": dict(self.headers),
                "env_base_path": os.environ.get('BASE_PATH', 'not set')
            }
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