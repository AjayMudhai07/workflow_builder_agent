# IRA Workflow Builder - API Documentation

**Version**: 0.1.0

Base URL: `http://localhost:8000/api/v1`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Endpoints](#endpoints)
   - [Files](#files)
   - [Workflows](#workflows)
   - [WebSocket](#websocket)
3. [Models](#models)
4. [Error Handling](#error-handling)

---

## Authentication

Currently, the API uses simple token-based authentication. In production, use proper OAuth2 or JWT.

```http
Authorization: Bearer {your-token}
```

---

## Endpoints

### Files

#### Upload CSV File

Upload a CSV file for analysis.

**Endpoint**: `POST /api/v1/files/upload`

**Request**:
```http
POST /api/v1/files/upload
Content-Type: multipart/form-data

file: [binary data]
```

**Response**:
```json
{
  "file_id": "file_12345",
  "filename": "sales_data.csv",
  "size_bytes": 102400,
  "rows": 1000,
  "columns": ["date", "product", "amount"],
  "uploaded_at": "2025-10-15T10:30:00Z"
}
```

#### List Files

Get list of uploaded files.

**Endpoint**: `GET /api/v1/files`

**Response**:
```json
{
  "files": [
    {
      "file_id": "file_12345",
      "filename": "sales_data.csv",
      "uploaded_at": "2025-10-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

### Workflows

#### Create Workflow

Create a new workflow.

**Endpoint**: `POST /api/v1/workflows`

**Request**:
```json
{
  "name": "Sales Analysis Q4",
  "description": "Analyze Q4 sales to identify top performers",
  "csv_file_ids": ["file_12345"]
}
```

**Response**:
```json
{
  "workflow_id": "wf_abc123",
  "name": "Sales Analysis Q4",
  "status": "initialized",
  "created_at": "2025-10-15T10:30:00Z"
}
```

#### Get Workflow Status

Get current workflow status.

**Endpoint**: `GET /api/v1/workflows/{workflow_id}`

**Response**:
```json
{
  "workflow_id": "wf_abc123",
  "name": "Sales Analysis Q4",
  "status": "awaiting_user_response",
  "current_state": "requirements_gathering",
  "questions_asked": 3,
  "updated_at": "2025-10-15T10:35:00Z"
}
```

#### Answer Question

Submit answer to planner's question.

**Endpoint**: `POST /api/v1/workflows/{workflow_id}/answer`

**Request**:
```json
{
  "question_id": 3,
  "answer": "I need to group by product category and calculate total revenue"
}
```

**Response**:
```json
{
  "workflow_id": "wf_abc123",
  "question_id": 3,
  "status": "answer_received",
  "next_question": {
    "question_id": 4,
    "question": "Should the results be sorted in any specific order?"
  }
}
```

#### Approve Business Logic

Approve or request changes to business logic.

**Endpoint**: `POST /api/v1/workflows/{workflow_id}/approve-logic`

**Request**:
```json
{
  "decision": "approve",
  "feedback": ""
}
```

Or request changes:
```json
{
  "decision": "request_changes",
  "feedback": "Please add handling for missing values"
}
```

**Response**:
```json
{
  "workflow_id": "wf_abc123",
  "status": "logic_approved",
  "next_state": "code_generation"
}
```

#### Approve Results

Approve or request changes to analysis results.

**Endpoint**: `POST /api/v1/workflows/{workflow_id}/approve-result`

**Request**:
```json
{
  "decision": "approve"
}
```

**Response**:
```json
{
  "workflow_id": "wf_abc123",
  "status": "completed",
  "result_file_id": "result_xyz789",
  "download_url": "/api/v1/files/result_xyz789/download"
}
```

#### Download Result

Download the generated result CSV.

**Endpoint**: `GET /api/v1/files/{file_id}/download`

**Response**: Binary CSV file

---

### WebSocket

#### Workflow Stream

Real-time workflow events via WebSocket.

**Endpoint**: `WS /ws/workflow/{workflow_id}`

**Messages**:

```json
{
  "type": "executor_started",
  "executor_name": "planner_gathering",
  "timestamp": "2025-10-15T10:30:00Z"
}
```

```json
{
  "type": "question_asked",
  "question_id": 1,
  "question": "What is the primary metric you want to analyze?",
  "timestamp": "2025-10-15T10:30:05Z"
}
```

```json
{
  "type": "business_logic_generated",
  "document": "# Business Logic Document...",
  "timestamp": "2025-10-15T10:35:00Z"
}
```

```json
{
  "type": "code_executing",
  "status": "running",
  "timestamp": "2025-10-15T10:40:00Z"
}
```

```json
{
  "type": "workflow_completed",
  "result_file_id": "result_xyz789",
  "timestamp": "2025-10-15T10:42:00Z"
}
```

---

## Models

### WorkflowCreateRequest

```python
{
  "name": str,                    # Workflow name
  "description": str,             # Workflow description
  "csv_file_ids": List[str]       # List of uploaded file IDs
}
```

### WorkflowStatusResponse

```python
{
  "workflow_id": str,
  "name": str,
  "status": str,                  # Status enum
  "current_state": str,           # Current workflow state
  "questions_asked": int,
  "business_logic_approved": bool,
  "result_approved": bool,
  "created_at": datetime,
  "updated_at": datetime
}
```

### Status Values

- `initialized`: Workflow created
- `csv_analysis`: Analyzing CSV files
- `requirements_gathering`: Asking questions
- `awaiting_user_response`: Waiting for user input
- `business_logic_generation`: Generating business logic
- `business_logic_review`: Awaiting approval
- `code_generation`: Generating code
- `code_execution`: Executing code
- `result_review`: Awaiting result approval
- `completed`: Workflow finished
- `error`: Error occurred

---

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid workflow configuration",
    "details": {
      "field": "csv_file_ids",
      "reason": "At least one CSV file is required"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `NOT_FOUND` | 404 | Resource not found |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `WORKFLOW_ERROR` | 500 | Workflow execution error |
| `AGENT_ERROR` | 500 | Agent execution error |
| `STORAGE_ERROR` | 500 | Storage operation error |

---

## Rate Limiting

- **Per minute**: 60 requests
- **Per hour**: 1000 requests

Rate limit headers:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1697373000
```

---

## Examples

### Complete Workflow Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 1. Upload CSV
with open("sales_data.csv", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/files/upload",
        files={"file": f}
    )
file_id = response.json()["file_id"]

# 2. Create workflow
response = requests.post(
    f"{BASE_URL}/workflows",
    json={
        "name": "Sales Analysis",
        "description": "Analyze quarterly sales",
        "csv_file_ids": [file_id]
    }
)
workflow_id = response.json()["workflow_id"]

# 3. Answer questions (repeat as needed)
response = requests.post(
    f"{BASE_URL}/workflows/{workflow_id}/answer",
    json={
        "question_id": 1,
        "answer": "Total revenue by product category"
    }
)

# 4. Approve business logic
response = requests.post(
    f"{BASE_URL}/workflows/{workflow_id}/approve-logic",
    json={"decision": "approve"}
)

# 5. Approve results
response = requests.post(
    f"{BASE_URL}/workflows/{workflow_id}/approve-result",
    json={"decision": "approve"}
)

# 6. Download result
result_file_id = response.json()["result_file_id"]
response = requests.get(
    f"{BASE_URL}/files/{result_file_id}/download"
)
with open("result.csv", "wb") as f:
    f.write(response.content)
```

---

**API Version**: 0.1.0
**Last Updated**: 2025-10-15
