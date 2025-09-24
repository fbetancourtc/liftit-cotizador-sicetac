"""
Vercel serverless function handler for FastAPI application.
This file serves as the entry point for Vercel's Python runtime.
"""
import sys
from pathlib import Path

# Add the parent directory to the Python path so we can import the app module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the FastAPI app
from app.main import create_app

# Create the FastAPI application instance
app = create_app()

# Handler for Vercel
handler = app