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
    echo "⚠️  IMPORTANT: Edit .env and configure your LLM provider"
    echo ""
    echo "Options:"
    echo "  1. For OpenAI: Set LLM_PROVIDER=openai and OPENAI_API_KEY"
    echo "  2. For Groq: Set LLM_PROVIDER=groq and GROQ_API_KEY"
    echo ""
    read -p "Press Enter to continue after configuring .env..."
fi

# Read LLM provider configuration from .env file
if [ -f .env ]; then
    # Source the .env file to get provider settings
    export $(grep -v '^#' .env | grep -E '(LLM_PROVIDER|PLANNER_PROVIDER|CODER_PROVIDER)=' | xargs)
fi

# Default to openai if not set
LLM_PROVIDER=${LLM_PROVIDER:-openai}
PLANNER_PROVIDER=${PLANNER_PROVIDER:-openai}
CODER_PROVIDER=${CODER_PROVIDER:-groq}

# Display configuration
echo "LLM Configuration:"
echo "  📋 Planning Phase: ${PLANNER_PROVIDER}"
echo "  💻 Coding Phase:   ${CODER_PROVIDER}"
echo ""

# Determine which providers we need to validate
NEED_OPENAI=false
NEED_GROQ=false

if [ "$PLANNER_PROVIDER" = "openai" ] || [ "$CODER_PROVIDER" = "openai" ]; then
    NEED_OPENAI=true
fi

if [ "$PLANNER_PROVIDER" = "groq" ] || [ "$CODER_PROVIDER" = "groq" ]; then
    NEED_GROQ=true
fi

# Validate OpenAI if needed
if [ "$NEED_OPENAI" = true ]; then
    echo "Validating OpenAI configuration..."
    if grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        OPENAI_MODEL=$(grep -E '^OPENAI_MODEL=' .env | cut -d '=' -f2)
        echo "✅ OpenAI API key configured"
        echo "   Model: ${OPENAI_MODEL:-gpt-4o}"
    else
        echo "❌ Error: OPENAI_API_KEY not set in .env file"
        echo ""
        echo "To use OpenAI:"
        echo "  1. Get API key from: https://platform.openai.com/api-keys"
        echo "  2. Edit .env and set:"
        echo "     OPENAI_API_KEY=sk-your_key_here"
        echo "     OPENAI_MODEL=gpt-4o"
        echo ""
        exit 1
    fi
    echo ""
fi

# Validate Groq if needed
if [ "$NEED_GROQ" = true ]; then
    echo "Validating Groq configuration..."
    if grep -q "GROQ_API_KEY=gsk_" .env 2>/dev/null; then
        GROQ_MODEL=$(grep -E '^GROQ_MODEL=' .env | cut -d '=' -f2)
        echo "✅ Groq API key configured"
        echo "   Model: ${GROQ_MODEL:-llama-3.3-70b-versatile}"
    else
        echo "❌ Error: GROQ_API_KEY not set in .env file"
        echo ""
        echo "To use Groq:"
        echo "  1. Get API key from: https://console.groq.com/keys"
        echo "  2. Edit .env and set:"
        echo "     GROQ_API_KEY=gsk_your_key_here"
        echo "     GROQ_MODEL=llama-3.3-70b-versatile"
        echo ""
        exit 1
    fi
    echo ""
fi

# Show hybrid mode message if using different providers
if [ "$PLANNER_PROVIDER" != "$CODER_PROVIDER" ]; then
    echo "🔄 Hybrid Mode Enabled:"
    echo "   Using ${PLANNER_PROVIDER} for planning (better reasoning)"
    echo "   Using ${CODER_PROVIDER} for coding (faster execution)"
    echo ""
fi

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

# Kill any existing process using port 8000
echo "Checking for existing server on port 8000..."
EXISTING_PID=$(lsof -ti:8000 2>/dev/null || true)
if [ ! -z "$EXISTING_PID" ]; then
    echo "⚠️  Found existing process on port 8000 (PID: $EXISTING_PID)"
    echo "Stopping existing server..."
    kill -9 $EXISTING_PID 2>/dev/null
    sleep 1
    echo "✅ Existing server stopped"
else
    echo "✅ Port 8000 is available"
fi
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

# Run with uvicorn (exclude data and storage directories from auto-reload to prevent restarts during code generation)
python -m uvicorn backend.api.app:app --reload --reload-exclude='*.py' --reload-include='backend/**/*.py' --reload-include='ai/**/*.py' --host 0.0.0.0 --port 8000
