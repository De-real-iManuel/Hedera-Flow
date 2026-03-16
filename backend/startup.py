"""
Railway startup script
This file is used by Railway to start the FastAPI application
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the FastAPI app
from app.core.app import app

# This is what Railway will use to start the application
application = app

if __name__ == "__main__":
    import uvicorn
    # Railway provides PORT environment variable, default to 8000 if not set
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)