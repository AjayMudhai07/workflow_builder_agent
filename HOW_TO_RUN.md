# How to Run the IRA Workflow Builder

This guide will help you get the IRA Workflow Builder up and running on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** (Python 3.11 recommended)
- **Node.js 18+** (for frontend)
- **npm or yarn** (package manager)
- **Git** (for version control)
- **OpenAI API Key** (required for AI agents)

## Quick Start (5 Minutes)

### 1. Clone and Navigate to Project
```bash
cd /Users/ajay/Documents/workflow_builder_v4
```

### 2. Set Up Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
nano .env  # or use your preferred editor
```

**Required in .env:**
```env
OPENAI_API_KEY=your_actual_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 3. Run Backend (Terminal 1)
```bash
# The script will automatically:
# - Create virtual environment if needed
# - Install dependencies
# - Create necessary directories
# - Start the FastAPI server
./start_backend.sh
```

Backend will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### 4. Run Frontend (Terminal 2)
```bash
cd frontend
npm install  # First time only
npm run dev
```

Frontend will be available at:
- **App**: http://localhost:3000

### 5. Access the Application
Open your browser and go to:
```
http://localhost:3000
```

You should see the IRA Workflow Builder interface!

---

## Detailed Setup Instructions

### Backend Setup

#### Option A: Using the Start Script (Recommended)
```bash
# From project root
./start_backend.sh
```

This script automatically:
- Checks for .env file and OpenAI API key
- Creates virtual environment if missing
- Installs Python dependencies
- Creates necessary storage directories
- Starts the FastAPI server with auto-reload

#### Option B: Manual Setup
```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create necessary directories
mkdir -p data/uploads
mkdir -p data/outputs
mkdir -p storage/workflows
mkdir -p storage/generated_code
mkdir -p logs

# 5. Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 6. Start the backend
python -m uvicorn backend.api.app:app --reload --host 0.0.0.0 --port 8000
```

#### Backend with Visible Logs
If you want to see all logs in real-time:
```bash
./start_backend_visible.sh
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Or for production build
npm run build
npm start
```

---

## Running Tests

### AI Component Tests

#### Run All Tests
```bash
cd ai
python -m pytest tests/unit/ -v
```

#### Run Specific Test
```bash
cd ai
python test_orchestrator.py
```

#### Run Integration Tests
```bash
cd ai

# Test orchestrator
python test_orchestrator.py

# Test coder agent
python test_coder_agent.py

# Test code executor
python test_code_executor.py
```

### Backend API Tests
```bash
# From project root
pytest backend/api/tests/ -v
```

---

## Project Structure

After running, here's what each component does:

```
Backend (localhost:8000)
├── /api/v1/workflows - Workflow management endpoints
├── /ws/workflows/{id} - WebSocket for real-time updates
├── /health - Health check
└── /docs - Interactive API documentation

Frontend (localhost:3000)
├── / - Home page
├── /create - Create new workflow
├── /workflows - View all workflows
└── /workflows/{id} - Workflow details
```

---

## Usage Examples

### Example 1: Create a Workflow via API

```bash
# Create a new workflow
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Analysis",
    "description": "Analyze sales data and generate report",
    "csv_files": ["data/uploads/sales.csv"],
    "output_filename": "sales_report.csv"
  }'
```

### Example 2: Using the Frontend

1. Open http://localhost:3000
2. Click "Create Workflow"
3. Upload your CSV file(s)
4. Describe what you want to do
5. Follow the interactive questions from the Planner Agent
6. Review and approve the generated plan
7. Watch as the Coder Agent generates and executes code
8. Download your results

### Example 3: Running a Test Workflow

```bash
# From project root
cd ai
python test_orchestrator.py

# This will:
# 1. Start a sample workflow
# 2. Answer planner questions automatically
# 3. Generate code
# 4. Execute code
# 5. Show results
```

---

## Environment Configuration

### Required Environment Variables

**.env file:**
```env
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-...your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# Model Selection (Optional)
OPENAI_MODEL=gpt-4o  # or gpt-4o-mini for faster/cheaper

# Backend Configuration (Optional)
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Workflow Configuration (Optional)
MAX_PLANNER_QUESTIONS=10
MAX_CODER_ITERATIONS=3
CODE_EXECUTION_TIMEOUT=120
```

### Optional Configuration Files

**config/settings.yaml** - Additional configuration options
**config/logging.yaml** - Logging configuration

---

## Troubleshooting

### Backend Issues

#### Port Already in Use
```bash
# Find process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in start script
python -m uvicorn backend.api.app:app --reload --port 8001
```

#### Missing OpenAI API Key
```bash
# Check if key is set
echo $OPENAI_API_KEY

# Set it temporarily
export OPENAI_API_KEY=your-key-here

# Or add it to .env file permanently
```

#### Import Errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Install project in development mode
pip install -e .
```

#### Dependencies Issues
```bash
# Clear cache and reinstall
pip cache purge
pip install --no-cache-dir -r requirements.txt
```

### Frontend Issues

#### Port 3000 Already in Use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or run on different port
PORT=3001 npm run dev
```

#### Cannot Connect to Backend
- Check if backend is running on http://localhost:8000
- Check CORS settings in backend/.env
- Verify API URL in frontend/src/lib/api.ts

#### Module Not Found
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### AI Component Issues

#### Planner Agent Not Responding
- Verify OpenAI API key is valid
- Check API rate limits
- Review logs in logs/ directory

#### Code Execution Fails
- Check if CSV files exist in data/uploads/
- Verify code execution timeout setting
- Review generated code in storage/generated_code/

---

## Development Tips

### Hot Reload
Both backend and frontend support hot reload:
- Backend: Changes to Python files auto-reload
- Frontend: Changes to React components auto-refresh

### Viewing Logs

**Backend Logs:**
```bash
# Real-time logs
./start_backend_visible.sh

# Or check log files
tail -f logs/app.log
```

**Frontend Logs:**
- Check browser console (F12)
- Terminal where npm run dev is running

### API Documentation

Visit http://localhost:8000/docs for:
- Interactive API testing
- Request/response schemas
- Authentication details
- WebSocket documentation

---

## Production Deployment

### Backend Production

```bash
# Install production dependencies
pip install -r requirements.txt

# Run with production settings
export ENVIRONMENT=production
uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Production

```bash
cd frontend

# Build for production
npm run build

# Start production server
npm start

# Or use a process manager like PM2
pm2 start npm --name "ira-frontend" -- start
```

### Using Docker (Future)

```bash
# Build and run with docker-compose
docker-compose up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 2GB free space
- **OS**: macOS, Linux, or Windows 10+

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 5GB+ free space
- **OS**: macOS or Linux (Ubuntu 20.04+)

---

## Additional Resources

### Documentation
- **API Guide**: See BACKEND_API_GUIDE.md
- **Architecture**: See IRA_WORKFLOW_ARCHITECTURE.md
- **Project Structure**: See PROJECT_REORGANIZATION.md

### Example Workflows
```bash
cd ai/examples
python planner_demo.py
```

### Manual Testing
See MANUAL_TEST_GUIDE.md for step-by-step testing instructions.

---

## Quick Reference Commands

```bash
# Backend
./start_backend.sh                    # Start backend
./start_backend_visible.sh           # Start with visible logs
curl http://localhost:8000/health    # Check health

# Frontend
cd frontend && npm run dev           # Start frontend
cd frontend && npm run build         # Build for production

# Tests
cd ai && python test_orchestrator.py # Run orchestrator test
pytest ai/tests/unit/ -v            # Run unit tests

# Cleanup
rm -rf venv                          # Remove virtual environment
cd frontend && rm -rf node_modules   # Remove node modules
```

---

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs in logs/ directory
3. Check API docs at http://localhost:8000/docs
4. Review error messages carefully
5. Ensure all prerequisites are installed
6. Verify environment variables are set correctly

---

## Success Indicators

You know everything is working when:

✅ Backend starts without errors at http://localhost:8000
✅ Frontend loads at http://localhost:3000
✅ Health check returns `{"status": "healthy"}` at http://localhost:8000/health
✅ API docs are accessible at http://localhost:8000/docs
✅ You can create and run workflows through the UI
✅ Test scripts run successfully from ai/ directory

**You're all set! Happy building! 🚀**
