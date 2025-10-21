#!/bin/bash
# Startup script for IRA Workflow Builder backend

set -e

echo "========================================"
echo "IRA Workflow Builder - Backend Server"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your OPENAI_API_KEY"
    echo ""
    read -p "Press Enter to continue after setting your API key..."
fi

# Check if OPENAI_API_KEY is set
source .env
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "❌ Error: OPENAI_API_KEY not set in .env file"
    echo "Please edit .env and add your OpenAI API key"
    exit 1
fi

echo "✅ Environment configuration loaded"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"
echo ""

# Create necessary directories
echo "Creating storage directories..."
mkdir -p data/uploads
mkdir -p data/outputs
mkdir -p storage/workflows
mkdir -p storage/generated_code
mkdir -p logs
echo "✅ Storage directories created"
echo ""

# Start the server
echo "========================================"
echo "Starting FastAPI server..."
echo "========================================"
echo ""
echo "📍 API:     http://localhost:8000"
echo "📚 Docs:    http://localhost:8000/docs"
echo "🔍 Redoc:   http://localhost:8000/redoc"
echo "💚 Health:  http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run with uvicorn
python -m uvicorn ira_builder.api.app:app --reload --host 0.0.0.0 --port 8000
