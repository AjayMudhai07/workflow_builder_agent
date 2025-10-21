#!/bin/bash

# Script to start backend with visible logs
# This will show all logs in real-time in your terminal

cd /Users/ajay/Documents/workflow_builder_v4

# Activate virtual environment
source venv/bin/activate

# Load environment variables
source .env

# Start the backend (logs will appear in terminal)
echo "=========================================="
echo "Starting IRA Workflow Builder Backend"
echo "=========================================="
echo ""
echo "Backend will start on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

python -m uvicorn ira_builder.api.app:app --reload --host 0.0.0.0 --port 8000
