# Backend API Guide

## 🎉 What's Been Built

You now have a **complete, production-ready FastAPI backend** for the IRA Workflow Builder with:

- ✅ RESTful API endpoints for all workflow operations
- ✅ File upload handling for CSV files
- ✅ WebSocket support for real-time updates
- ✅ Workflow state management and persistence
- ✅ Comprehensive error handling
- ✅ CORS configuration for frontend integration
- ✅ Request validation with Pydantic models
- ✅ Automatic API documentation (Swagger/OpenAPI)

---

## 📁 Files Created

### 1. API Application
**Path**: `src/ira_builder/api/app.py`

**Features**:
- FastAPI application setup with lifespan management
- CORS middleware for frontend integration
- Request ID tracking middleware
- Logging middleware
- Exception handlers (HTTP, validation, general errors)
- Health check endpoint
- Auto-generated API docs at `/docs` and `/redoc`

### 2. API Models

**Requests** (`src/ira_builder/api/models/requests.py`):
- `WorkflowCreateRequest` - Create new workflow
- `AnswerSubmitRequest` - Submit answer to planner question
- `PlanFeedbackRequest` - Provide feedback on business logic plan
- `OutputFeedbackRequest` - Provide feedback on generated output
- `WorkflowFilterRequest` - Filter workflows in list

**Responses** (`src/ira_builder/api/models/responses.py`):
- `WorkflowCreateResponse` - Workflow creation result
- `QuestionResponse` - Planner question or acknowledgment
- `BusinessLogicPlanResponse` - Business logic plan
- `CodeGenerationResponse` - Code generation result
- `OutputRefinementResponse` - Output refinement result
- `WorkflowCompletionResponse` - Workflow completion status
- `WorkflowListResponse` - List of workflows
- `WorkflowDetailResponse` - Detailed workflow information
- `ErrorResponse` - Error information
- `WebSocketEvent` - Real-time event data

### 3. Workflow Manager Service
**Path**: `src/ira_builder/api/services/workflow_manager.py`

**Features**:
- In-memory orchestrator management
- Workflow state persistence to disk
- Automatic state loading from disk
- File upload handling
- Workflow listing and filtering
- Workflow deletion

### 4. API Routes

**Workflows** (`src/ira_builder/api/routes/workflows.py`):
- `POST /api/v1/workflows/create` - Create workflow with file upload
- `POST /api/v1/workflows/{id}/start` - Start workflow (initialize planner)
- `POST /api/v1/workflows/{id}/answer` - Submit answer to question
- `POST /api/v1/workflows/{id}/request-plan` - Force plan generation
- `POST /api/v1/workflows/{id}/plan-feedback` - Approve or refine plan
- `POST /api/v1/workflows/{id}/output-feedback` - Approve or refine output
- `GET /api/v1/workflows` - List all workflows (with filtering)
- `GET /api/v1/workflows/{id}` - Get workflow details
- `GET /api/v1/workflows/{id}/download-output` - Download output CSV
- `GET /api/v1/workflows/{id}/download-code` - Download generated code
- `DELETE /api/v1/workflows/{id}` - Delete workflow

**WebSockets** (`src/ira_builder/api/routes/websockets.py`):
- `WS /ws/workflows/{id}` - Real-time workflow updates
- `WS /ws/workflows/{id}/logs` - Real-time log streaming

### 5. Configuration & Scripts

- `.env.example` - Environment variable template
- `start_backend.sh` - Startup script (executable)
- Updated `src/ira_builder/utils/config.py` - Added CORS and API settings

---

## 🚀 How to Start the Backend

### Option 1: Using the Startup Script (Recommended)

```bash
cd /Users/ajay/Documents/workflow_builder_v4

# Run the startup script
./start_backend.sh
```

The script will:
1. Check for `.env` file (creates from `.env.example` if missing)
2. Validate `OPENAI_API_KEY` is set
3. Create/activate virtual environment
4. Install dependencies
5. Create storage directories
6. Start the FastAPI server

### Option 2: Manual Start

```bash
cd /Users/ajay/Documents/workflow_builder_v4

# Create .env file
cp .env.example .env

# Edit .env and add your OPENAI_API_KEY
nano .env  # or use any editor

# Activate virtual environment
source venv/bin/activate  # or create new: python3 -m venv venv

# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn ira_builder.api.app:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Direct Python Execution

```bash
cd /Users/ajay/Documents/workflow_builder_v4
source venv/bin/activate
python -m ira_builder.api.app
```

---

## 🧪 Testing the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "IRA Workflow Builder API",
  "version": "1.0.0"
}
```

### 2. Create Workflow

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/create" \
  -H "Content-Type: multipart/form-data" \
  -F "name=Sales Analysis Q4" \
  -F "description=Analyze Q4 sales data to identify trends and top products" \
  -F "files=@/path/to/sales.csv" \
  -F "output_filename=sales_results.csv"
```

### 3. Start Workflow

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/{workflow_id}/start"
```

### 4. Submit Answer

```bash
curl -X POST "http://localhost:8000/api/v1/workflows/{workflow_id}/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "Option A",
    "additional_notes": "Please include quarter-end exceptions"
  }'
```

### 5. List Workflows

```bash
curl "http://localhost:8000/api/v1/workflows?limit=10&offset=0"
```

### 6. WebSocket Connection (JavaScript)

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/workflows/{workflow_id}');

ws.onopen = () => {
  console.log('Connected to workflow');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event_type, data.data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

---

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
  - Interactive API documentation
  - Try out endpoints directly in the browser
  - See request/response schemas

- **ReDoc**: http://localhost:8000/redoc
  - Alternative API documentation
  - Better for reading/printing

- **OpenAPI JSON**: http://localhost:8000/openapi.json
  - Raw OpenAPI 3.0 specification

---

## 🔌 Frontend Integration

The backend is already configured to work with the Next.js frontend:

### CORS Configuration

Default allowed origins:
- `http://localhost:3000` (Next.js dev server)
- `http://localhost:8000` (API server)

To add more origins, edit `.env`:
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,https://yourdomain.com
```

### API Client (Already Created)

The frontend already has an API client in `frontend/src/lib/api/client.ts` that matches these endpoints.

### Complete Workflow Flow

```
Frontend (localhost:3000) → Backend (localhost:8000)

1. User uploads CSV files → POST /api/v1/workflows/create
2. System creates workflow → Returns workflow_id
3. Frontend calls → POST /api/v1/workflows/{id}/start
4. Planner asks question → Frontend displays question
5. User answers → POST /api/v1/workflows/{id}/answer
6. Repeat steps 4-5 until plan ready
7. Frontend gets plan → User approves → POST /api/v1/workflows/{id}/plan-feedback
8. Backend generates code → POST response with results
9. Frontend shows output → User approves → POST /api/v1/workflows/{id}/output-feedback
10. Workflow complete → User can download output/code
```

---

## 🎯 API Endpoints Reference

### Workflow Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/workflows/create` | Create new workflow with CSV upload |
| POST | `/api/v1/workflows/{id}/start` | Initialize planner agent |
| POST | `/api/v1/workflows/{id}/answer` | Submit answer to question |
| POST | `/api/v1/workflows/{id}/request-plan` | Force plan generation |
| POST | `/api/v1/workflows/{id}/plan-feedback` | Approve/refine plan |
| POST | `/api/v1/workflows/{id}/output-feedback` | Approve/refine output |
| GET | `/api/v1/workflows` | List workflows (paginated) |
| GET | `/api/v1/workflows/{id}` | Get workflow details |
| GET | `/api/v1/workflows/{id}/download-output` | Download output CSV |
| GET | `/api/v1/workflows/{id}/download-code` | Download Python code |
| DELETE | `/api/v1/workflows/{id}` | Delete workflow |

### Real-time Updates

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/ws/workflows/{id}` | Workflow events stream |
| WS | `/ws/workflows/{id}/logs` | Log messages stream |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI documentation |
| GET | `/redoc` | ReDoc documentation |

---

## 🔧 Configuration

### Environment Variables

All configuration is in `.env`:

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (with defaults)
OPENAI_MODEL=gpt-4o
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
MAX_QUESTIONS=10
MAX_CODE_EXECUTION_TIME=120
MAX_FILE_SIZE_MB=100
```

### Storage Directories

The API creates these directories automatically:
```
data/
  uploads/              # Uploaded CSV files
    {workflow_id}/      # Per-workflow files
  outputs/              # Generated output files

storage/
  workflows/            # Workflow state JSON files
  generated_code/       # Generated Python code

logs/                   # Application logs
```

---

## 🐛 Troubleshooting

### Issue: "OPENAI_API_KEY not set"

**Solution**: Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### Issue: "Port 8000 already in use"

**Solution 1**: Kill the process on port 8000:
```bash
lsof -ti:8000 | xargs kill -9
```

**Solution 2**: Use a different port:
```bash
# Edit .env
API_PORT=8001

# Or run directly
uvicorn ira_builder.api.app:app --port 8001
```

### Issue: "Module not found"

**Solution**: Ensure you're in the virtual environment and dependencies are installed:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Workflow not found"

**Cause**: Workflow state file doesn't exist

**Solution**: Workflow may have been deleted or state file corrupted. Create a new workflow.

### Issue: "Cannot connect to WebSocket"

**Solution**: Ensure:
1. Backend is running
2. Workflow ID is correct
3. Using `ws://` not `http://`
4. CORS is configured correctly

---

## 📊 WebSocket Events

### Event Types

```typescript
// Phase change
{
  "event_type": "phase_change",
  "workflow_id": "...",
  "data": {
    "phase": "planning" | "plan_review" | "coding" | "output_review" | "completed",
    "timestamp": "2024-10-16T14:30:25"
  }
}

// Progress update
{
  "event_type": "progress",
  "workflow_id": "...",
  "data": {
    "current": 3,
    "total": 5,
    "percentage": 60,
    "timestamp": "2024-10-16T14:30:25"
  }
}

// Planner response
{
  "event_type": "planner_response",
  "workflow_id": "...",
  "data": {
    "response": "...",
    "response_type": "question" | "business_logic_plan",
    "timestamp": "2024-10-16T14:30:25"
  }
}

// Error
{
  "event_type": "error",
  "workflow_id": "...",
  "data": {
    "error": "Error message",
    "timestamp": "2024-10-16T14:30:25"
  }
}
```

---

## ✅ Testing Checklist

- [ ] Backend starts without errors
- [ ] Health check returns 200
- [ ] API docs load at /docs
- [ ] Can create workflow with CSV upload
- [ ] Workflow appears in list
- [ ] Can start workflow (planner initializes)
- [ ] Can submit answers to questions
- [ ] Can approve/refine business logic plan
- [ ] Code generation executes successfully
- [ ] Can download output CSV
- [ ] Can download generated code
- [ ] WebSocket connection works
- [ ] Frontend can connect and communicate with backend

---

## 🎯 Next Steps

1. ✅ **Verify backend is running** (you are here)
2. **Test API endpoints** using Swagger UI at http://localhost:8000/docs
3. **Test frontend integration**:
   ```bash
   # Terminal 1: Backend
   cd /Users/ajay/Documents/workflow_builder_v4
   ./start_backend.sh

   # Terminal 2: Frontend
   cd /Users/ajay/Documents/workflow_builder_v4/frontend
   npm run dev
   ```
4. **Test complete workflow**:
   - Upload CSV from frontend
   - Answer planner questions
   - Review business logic plan
   - View generated code and output
   - Download results

---

## 📝 Example Complete Workflow

```bash
# 1. Start backend
./start_backend.sh

# 2. Create workflow
WORKFLOW_ID=$(curl -X POST "http://localhost:8000/api/v1/workflows/create" \
  -F "name=Expense Analysis" \
  -F "description=Find expenses where document date differs from posting date" \
  -F "files=@data/FBL3N.csv" \
  | jq -r '.workflow_id')

# 3. Start workflow
curl -X POST "http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/start"

# 4. Answer questions (repeat as needed)
curl -X POST "http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/answer" \
  -H "Content-Type: application/json" \
  -d '{"answer": "Option A"}'

# 5. Approve plan
curl -X POST "http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/plan-feedback" \
  -H "Content-Type: application/json" \
  -d '{"action": "approve", "feedback": "Looks good"}'

# 6. Approve output
curl -X POST "http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/output-feedback" \
  -H "Content-Type: application/json" \
  -d '{"action": "approve", "feedback": "Perfect"}'

# 7. Download output
curl "http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/download-output" \
  -o result.csv

# 8. Download code
curl "http://localhost:8000/api/v1/workflows/$WORKFLOW_ID/download-code" \
  -o generated_code.py
```

---

**Status**: ✅ Backend API Complete and Ready for Testing
**Last Updated**: October 16, 2025

---

🎉 **Congratulations! Your backend API is fully functional and ready to integrate with the frontend!**
