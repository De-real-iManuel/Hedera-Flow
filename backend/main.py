"""
Hedera Flow MVP - FastAPI Backend
Main application entry point
"""
import os
import logging

# Set environment variable to suppress Java/JNIus verbose logging
# This must be done BEFORE any imports
os.environ['KIVY_LOG_MODE'] = 'PYTHON'
os.environ['KIVY_NO_CONSOLELOG'] = '1'

# Configure logging FIRST before any imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Suppress verbose logs from Hedera SDK and its dependencies
# Set to ERROR to completely silence debug/info/warning messages
logging.getLogger('kivy').setLevel(logging.ERROR)
logging.getLogger('kivy.jnius').setLevel(logging.ERROR)
logging.getLogger('kivy.jnius.reflect').setLevel(logging.ERROR)
logging.getLogger('jnius').setLevel(logging.ERROR)
logging.getLogger('hedera').setLevel(logging.WARNING)
logging.getLogger('io.grpc').setLevel(logging.ERROR)

# Now import the app
from app.core.app import create_app

# Create FastAPI application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
