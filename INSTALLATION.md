# IRA Workflow Builder - Installation Guide

Complete installation guide for setting up the IRA Workflow Builder on any server.

## Table of Contents
- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Manual Installation](#manual-installation)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **OS**: macOS 10.15+, Ubuntu 20.04+, or CentOS 8+
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 2GB free space
- **Internet**: Active connection for package downloads

### Software Requirements
- **Python**: 3.11 or 3.12 (3.12 recommended)
- **Node.js**: v18 LTS or higher
- **npm**: v9+ (comes with Node.js)
- **Git**: For cloning the repository

### API Keys Required
- **OpenAI API Key** OR **Groq API Key** (at least one)
- **IRA Production API Token** (for deployment features)

---

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd workflow_builder_v4
```

### 2. Run Automated Setup
```bash
./setup.sh
```

This single command will:
- ✅ Check system prerequisites
- ✅ Install Python dependencies in virtual environment
- ✅ Install Node.js frontend dependencies
- ✅ Create necessary directories
- ✅ Generate `.env` configuration file
- ✅ Verify installation

### 3. Configure API Keys
```bash
nano .env
```

**Required Configuration:**
```bash
# At minimum, set ONE of these:
GROQ_API_KEY=your_groq_api_key_here
# OR
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Start the Application

**Terminal 1 - Backend:**
```bash
./start_backend.sh
```

**Terminal 2 - Frontend:**
```bash
cd frontend && npm run dev
```

### 5. Access the Application
Open your browser: **http://localhost:3000**

---

## Manual Installation

If the automated setup fails, follow these manual steps:

### Step 1: Install Python 3.11/3.12

**macOS (using Homebrew):**
```bash
brew install python@3.12
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3.12 python3.12-venv python3-pip
```

**CentOS/RHEL:**
```bash
sudo yum install python3.12 python3-pip
```

### Step 2: Install Node.js 18 LTS

**macOS (using Homebrew):**
```bash
brew install node@18
```

**Ubuntu/Debian:**
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**CentOS/RHEL:**
```bash
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs
```

### Step 3: Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 4: Install Python Dependencies
```bash
pip install --upgrade pip setuptools wheel
pip install -e .
```

### Step 5: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 6: Create Directories
```bash
mkdir -p storage/workflows
mkdir -p storage/generated_code
mkdir -p data/outputs
mkdir -p logs
```

### Step 7: Setup Environment Variables
```bash
cp .env.example .env
# Edit .env and add your API keys
nano .env
```

---

## Configuration

### Environment Variables (`.env`)

#### Required Settings

```bash
# LLM Provider (choose one)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile

# OR use OpenAI
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api.openai.com/v1

# Provider Selection
PLANNER_PROVIDER=groq  # or "openai"
CODER_PROVIDER=groq    # or "openai"
```

#### Optional Settings

```bash
# Server Ports (default values)
BACKEND_PORT=8000
FRONTEND_PORT=3000

# CORS (for development)
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# File Upload Limits
MAX_FILE_SIZE=104857600  # 100MB
ALLOWED_FILE_TYPES=[".csv",".xlsx",".xls"]

# Production API (for Live deployment feature)
STAGING_API_TOKEN=your_staging_token
PRODUCTION_API_TOKEN=your_production_token

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Recommended Model Settings

**For Groq (Fast, Free Tier Available):**
```bash
GROQ_MODEL=llama-3.3-70b-versatile  # Best for complex workflows
# OR
GROQ_MODEL=llama-3.1-70b-versatile  # Alternative
```

**For OpenAI (Most Capable):**
```bash
OPENAI_MODEL=gpt-4-turbo-preview  # Most capable
# OR
OPENAI_MODEL=gpt-3.5-turbo  # Faster, cheaper
```

---

## Verification

### 1. Verify Python Installation
```bash
source venv/bin/activate
python --version  # Should show Python 3.11 or 3.12
pip list | grep fastapi  # Should show fastapi installed
```

### 2. Verify Frontend Installation
```bash
cd frontend
npm list react  # Should show react installed
cd ..
```

### 3. Test Backend
```bash
./start_backend.sh
# In another terminal:
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### 4. Test Frontend
```bash
cd frontend
npm run dev
# Visit http://localhost:3000 in browser
```

---

## Troubleshooting

### Common Issues

#### 1. Python Version Issues

**Error:** `Python 3.11+ required`

**Solution:**
```bash
# Check Python version
python3 --version

# If wrong version, install Python 3.12
# macOS:
brew install python@3.12
# Linux:
sudo apt-get install python3.12
```

#### 2. Virtual Environment Issues

**Error:** `No module named 'fastapi'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# Check prompt shows (venv)

# Reinstall dependencies
pip install -e .
```

#### 3. Node.js/npm Issues

**Error:** `npm install fails` or `node: command not found`

**Solution:**
```bash
# Check Node.js version
node --version  # Should be v18+

# If wrong version, reinstall:
# macOS:
brew uninstall node
brew install node@18
# Linux:
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### 4. Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using the port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Kill the process
kill -9 <PID>

# Or change port in .env:
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

#### 5. API Key Issues

**Error:** `Invalid API key` or `401 Unauthorized`

**Solution:**
```bash
# Check .env file has correct keys
cat .env | grep API_KEY

# Ensure no extra spaces or quotes
# Correct:
GROQ_API_KEY=gsk_xxxx
# Wrong:
GROQ_API_KEY= "gsk_xxxx"  # Extra space and quotes
```

#### 6. Module Import Errors

**Error:** `ModuleNotFoundError: No module named 'ai.ira_builder'`

**Solution:**
```bash
# Ensure you installed in development mode
pip install -e .

# Check PYTHONPATH
echo $PYTHONPATH
# Should include current directory

# If not, add to .env:
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 7. Frontend Build Errors

**Error:** `npm ERR! peer dependencies` or build failures

**Solution:**
```bash
cd frontend

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

cd ..
```

### Getting Help

If you encounter issues not covered here:

1. **Check Logs:**
   ```bash
   # Backend logs
   tail -f logs/app.log

   # Or check console output from ./start_backend.sh
   ```

2. **Check API Documentation:**
   - Start backend: `./start_backend.sh`
   - Visit: http://localhost:8000/docs

3. **Environment Debug:**
   ```bash
   # List all environment variables
   cat .env

   # Test imports
   source venv/bin/activate
   python -c "import ai.ira_builder; print('OK')"
   ```

---

## Development Tips

### Running in Development Mode

**Backend with Auto-Reload:**
```bash
./start_backend.sh
# Uses --reload flag automatically
```

**Frontend with Hot Reload:**
```bash
cd frontend && npm run dev
# Changes auto-refresh in browser
```

### Testing

**Backend Tests:**
```bash
source venv/bin/activate
pytest tests/
```

**Frontend Tests:**
```bash
cd frontend
npm test
```

### Code Formatting

**Python:**
```bash
source venv/bin/activate
black .
ruff check .
```

**Frontend:**
```bash
cd frontend
npm run lint
npm run format
```

---

## Production Deployment

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Using production WSGI servers (Gunicorn)
- Nginx reverse proxy configuration
- SSL certificate setup
- Process management (systemd)
- Docker deployment options

---

## Next Steps

After successful installation:

1. ✅ **Read HOW_TO_RUN.md** - Learn how to use the application
2. ✅ **Explore API Docs** - http://localhost:8000/docs
3. ✅ **Try Example Workflows** - Use sample CSV files in `data/`
4. ✅ **Configure Production API** - For Live deployment features

---

## Support

For issues, questions, or contributions:
- Check existing documentation in `/docs`
- Review code comments in source files
- Check API documentation at http://localhost:8000/docs

---

**Last Updated:** 2025-10-22
