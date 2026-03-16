#!/usr/bin/env python3
import os
import subprocess
import sys

# Get the port from environment variable, default to 8000
port = os.environ.get('PORT', '8000')
print(f"PORT environment variable: {os.environ.get('PORT', 'Not set')}")
print(f"Starting server on port {port}")

# Start uvicorn with the correct port
cmd = [
    'uvicorn', 
    'app.core.app:app', 
    '--host', '0.0.0.0', 
    '--port', port
]

print(f"Running command: {' '.join(cmd)}")
subprocess.run(cmd)