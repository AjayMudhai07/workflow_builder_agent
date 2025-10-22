#!/bin/bash
# Stop script for IRA Workflow Builder backend

echo "========================================"
echo "Stopping IRA Workflow Builder Backend"
echo "========================================"
echo ""

# Find process using port 8000
EXISTING_PID=$(lsof -ti:8000)

if [ ! -z "$EXISTING_PID" ]; then
    echo "Found backend server running on port 8000 (PID: $EXISTING_PID)"
    echo "Stopping server..."
    kill -15 $EXISTING_PID 2>/dev/null

    # Wait for graceful shutdown
    sleep 2

    # Check if process is still running
    if ps -p $EXISTING_PID > /dev/null 2>&1; then
        echo "Process still running, forcing shutdown..."
        kill -9 $EXISTING_PID 2>/dev/null
    fi

    echo "✅ Backend server stopped"
else
    echo "No backend server found running on port 8000"
fi

echo ""
