# Live Phase Implementation Guide

## Overview

This document describes the complete implementation of the "Live" phase for the IRA Workflow Builder. The Live phase allows users to deploy approved workflows to Staging or Production environments via the Data Manager API.

## Architecture

### Flow Diagram

```
1. User completes Analysis Report Review phase
2. User navigates to Live phase page
3. User inputs:
   - Business Process ID (required)
   - Mode: Staging or Production (required)
   - Check ID (optional, auto-generated if not provided)
   - Tags (optional)
4. Backend generates workflow config using LLM
5. Backend calls Production API to deploy workflow
6. Workflow becomes "Live" in the selected environment
```

## Backend Components (✅ COMPLETED)

### 1. Production API Client (`backend/api/services/production_api_client.py`)

- **Purpose**: Client for interacting with IRA Production Data Manager API
- **Key Functions**:
  - `make_workflow_live()`: Deploy workflow to production/staging
  - `update_workflow_check()`: Update existing deployment
  - `get_workflow_check()`: Retrieve deployment info
  - `get_session_queries()`: Fetch session queries

**Usage:**
```python
from backend.api.services.production_api_client import get_production_api_client

client = get_production_api_client(mode="Staging")
status_code = client.make_workflow_live(workflow_config, business_process_id)
```

### 2. Workflow Config Generator (`ai/ira_builder/utils/workflow_config_generator.py`)

- **Purpose**: Uses LLM to generate production-ready workflow configuration
- **Key Functions**:
  - `generate_workflow_config()`: Generate config from workflow state
  - `validate_workflow_config()`: Validate config structure
  - `_extract_required_files_info()`: Extract files & columns used in code

**Generated Config Structure:**
```json
{
  "name": "Workflow Name",
  "description": "Workflow Description",
  "check_id": "CHECK_001",
  "tags": ["TAG1", "TAG2"],
  "data": {
    "plan": "Business Logic Plan",
    "code": "```python\n# Code\n```",
    "analyst_instruction": "Analysis Instructions",
    "statistical_analysis_code": "```python\n# Analysis Code\n```",
    "required_files": {
      "csv_files": [
        {
          "file_name": "Master",
          "description": "File description",
          "required_columns": [
            {
              "name": "Column Name",
              "description": "Column description",
              "data_type": "object"
            }
          ]
        }
      ]
    }
  }
}
```

### 3. Orchestrator Updates (`ai/ira_builder/orchestrator.py`)

**Added:**
- `WorkflowPhase.LIVE` enum value
- Live phase state fields in `WorkflowState`:
  - `workflow_config`: Generated workflow configuration
  - `business_process_id`: Business process ID
  - `deployment_mode`: "Staging" or "Production"
  - `deployment_status`: HTTP status code
  - `check_id`: Unique check ID
  - `is_live`: Boolean flag

### 4. Request/Response Models

**Request Model** (`backend/api/models/requests.py`):
```python
class MakeWorkflowLiveRequest(BaseModel):
    business_process_id: str  # Required
    mode: str  # "Staging" or "Production"
    check_id: Optional[str]  # Auto-generated if None
    tags: Optional[List[str]]  # Optional tags
```

**Response Model** (`backend/api/models/responses.py`):
```python
class MakeWorkflowLiveResponse(BaseModel):
    status: str
    phase: WorkflowPhaseEnum  # "live"
    message: str
    deployment_status: int  # HTTP status code
    check_id: str
    business_process_id: str
    mode: str
    workflow_config: Optional[Dict[str, Any]]
```

## Frontend Components (❌ TODO)

### 1. Live Phase Page (`frontend/src/app/workflow/[id]/live/page.tsx`)

**Location**: Create new file at `frontend/src/app/workflow/[id]/live/page.tsx`

**Component Structure**:
```typescript
'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function LivePage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;

  const [businessProcessId, setBusinessProcessId] = useState('');
  const [mode, setMode] = useState<'Staging' | 'Production'>('Staging');
  const [checkId, setCheckId] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [isDeploying, setIsDeploying] = useState(false);
  const [deploymentResult, setDeploymentResult] = useState<any>(null);

  const handleDeploy = async () => {
    setIsDeploying(true);

    try {
      const response = await fetch(`/api/v1/workflows/${workflowId}/make-live`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          business_process_id: businessProcessId,
          mode,
          check_id: checkId || undefined,
          tags: tags.length > 0 ? tags : undefined
        })
      });

      const result = await response.json();
      setDeploymentResult(result);

      if (result.status === 'success') {
        // Show success message
        // Optionally redirect to completion page
      }
    } catch (error) {
      console.error('Deployment error:', error);
    } finally {
      setIsDeploying(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Make Workflow Live</h1>

      {/* Business Process ID Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Business Process ID *
        </label>
        <input
          type="text"
          value={businessProcessId}
          onChange={(e) => setBusinessProcessId(e.target.value)}
          className="w-full border rounded px-3 py-2"
          placeholder="e.g., BP_001, finance-audit-2024"
          required
        />
      </div>

      {/* Mode Selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Deployment Environment *
        </label>
        <div className="flex gap-4">
          <label className="flex items-center">
            <input
              type="radio"
              value="Staging"
              checked={mode === 'Staging'}
              onChange={(e) => setMode(e.target.value as 'Staging')}
            />
            <span className="ml-2">Staging</span>
          </label>
          <label className="flex items-center">
            <input
              type="radio"
              value="Production"
              checked={mode === 'Production'}
              onChange={(e) => setMode(e.target.value as 'Production')}
            />
            <span className="ml-2">Production</span>
          </label>
        </div>
      </div>

      {/* Check ID (Optional) */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Check ID (Optional)
        </label>
        <input
          type="text"
          value={checkId}
          onChange={(e) => setCheckId(e.target.value)}
          className="w-full border rounded px-3 py-2"
          placeholder="e.g., MS_001, FIN_AUDIT_001 (auto-generated if not provided)"
        />
      </div>

      {/* Tags (Optional) */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">
          Tags (Optional)
        </label>
        <input
          type="text"
          placeholder="Enter tags separated by commas"
          className="w-full border rounded px-3 py-2"
          onChange={(e) => setTags(e.target.value.split(',').map(t => t.trim()).filter(t => t))}
        />
      </div>

      {/* Deploy Button */}
      <button
        onClick={handleDeploy}
        disabled={!businessProcessId || isDeploying}
        className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
      >
        {isDeploying ? 'Deploying...' : `Deploy to ${mode}`}
      </button>

      {/* Deployment Result */}
      {deploymentResult && (
        <div className={`mt-6 p-4 rounded ${
          deploymentResult.status === 'success' ? 'bg-green-100' : 'bg-red-100'
        }`}>
          <h3 className="font-bold mb-2">
            {deploymentResult.status === 'success' ? 'Success!' : 'Error'}
          </h3>
          <p>{deploymentResult.message}</p>
          {deploymentResult.check_id && (
            <p className="mt-2">Check ID: <strong>{deploymentResult.check_id}</strong></p>
          )}
        </div>
      )}
    </div>
  );
}
```

### 2. Update Workflow Status Display

**File**: `frontend/src/components/WorkflowStatus.tsx` (or similar)

Add "Live" status to the workflow phase display at the top of the page. The status progression should be:

```
Planning → Plan Review → Coding → Output Review → Analysis Report → Live → Completed
```

### 3. Add Navigation

**File**: `frontend/src/app/workflow/[id]/analysis-report-review/page.tsx`

After analysis report is approved, add button to navigate to Live phase:

```typescript
<button
  onClick={() => router.push(`/workflow/${workflowId}/live`)}
  className="bg-green-500 text-white px-6 py-2 rounded"
>
  Make Workflow Live
</button>
```

## API Endpoints (❌ TODO - Need to implement in workflows.py)

### POST `/api/v1/workflows/{workflow_id}/make-live`

**Purpose**: Generate workflow config and deploy to production/staging

**Request Body**:
```json
{
  "business_process_id": "BP_001",
  "mode": "Staging",
  "check_id": "MS_001",  // Optional
  "tags": ["VEN", "FIN"]  // Optional
}
```

**Response** (Success - 200):
```json
{
  "status": "success",
  "phase": "live",
  "message": "Workflow successfully deployed to Staging",
  "deployment_status": 200,
  "check_id": "MS_001",
  "business_process_id": "BP_001",
  "mode": "Staging",
  "workflow_config": { ... }
}
```

**Implementation**:
```python
# In backend/api/routes/workflows.py

from backend.api.services.production_api_client import get_production_api_client
from ai.ira_builder.utils.workflow_config_generator import (
    generate_workflow_config,
    validate_workflow_config
)
from backend.api.models.requests import MakeWorkflowLiveRequest
from backend.api.models.responses import MakeWorkflowLiveResponse

@router.post("/workflows/{workflow_id}/make-live", response_model=MakeWorkflowLiveResponse)
async def make_workflow_live(workflow_id: str, request: MakeWorkflowLiveRequest):
    """Make a workflow live in production/staging environment."""

    try:
        # Get workflow manager and orchestrator
        manager = get_workflow_manager()
        orchestrator = manager.get_workflow(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Validate workflow is in correct phase
        if orchestrator.state.phase != WorkflowPhase.ANALYSIS_REPORT_REVIEW:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow must be in analysis_report_review phase. Current phase: {orchestrator.state.phase}"
            )

        # Validate analysis report is approved
        if not orchestrator.state.analysis_report_approved:
            raise HTTPException(
                status_code=400,
                detail="Analysis report must be approved before making workflow live"
            )

        # Generate check_id if not provided
        check_id = request.check_id
        if not check_id:
            # Auto-generate check_id from workflow name
            check_id = sanitize_filename(orchestrator.workflow_name)[:20].upper()
            check_id = f"{check_id}_{datetime.now().strftime('%Y%m%d')}"

        # Generate workflow config using LLM
        logger.info(f"🔧 Generating workflow config for: {workflow_id}")

        workflow_config = await generate_workflow_config(
            workflow_name=orchestrator.workflow_name,
            workflow_description=orchestrator.workflow_description,
            business_logic_plan=orchestrator.state.business_logic_plan,
            generated_code=orchestrator.state.generated_code,
            analysis_instructions=orchestrator.state.analysis_instructions,
            analysis_code=orchestrator.state.analysis_code,
            file_analysis_results=orchestrator.state.file_analysis_results,
            check_id=check_id
        )

        # Add tags if provided
        if request.tags:
            workflow_config["tags"] = request.tags

        # Validate config
        await validate_workflow_config(workflow_config)

        # Deploy to production/staging
        logger.info(f"🚀 Deploying workflow to {request.mode}...")

        prod_client = get_production_api_client(mode=request.mode)
        deployment_status = prod_client.make_workflow_live(
            workflow_config=workflow_config,
            business_process_id=request.business_process_id
        )

        if deployment_status != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Deployment failed with status code: {deployment_status}"
            )

        # Update orchestrator state
        orchestrator.state.workflow_config = workflow_config
        orchestrator.state.business_process_id = request.business_process_id
        orchestrator.state.deployment_mode = request.mode
        orchestrator.state.deployment_status = deployment_status
        orchestrator.state.check_id = check_id
        orchestrator.state.is_live = True
        orchestrator.state.phase = WorkflowPhase.LIVE

        # Persist state
        orchestrator._persist_state()

        logger.info(f"✅ Workflow successfully deployed to {request.mode}")

        return MakeWorkflowLiveResponse(
            status="success",
            phase=WorkflowPhaseEnum.LIVE,
            message=f"Workflow successfully deployed to {request.mode}",
            deployment_status=deployment_status,
            check_id=check_id,
            business_process_id=request.business_process_id,
            mode=request.mode,
            workflow_config=workflow_config
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error making workflow live: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## Environment Variables

Add to `.env` file:

```bash
# Production API Configuration
STAGING_API_TOKEN=d321e9dd-265b-4a16-b690-3c1708b47a10
PRODUCTION_API_TOKEN=65e704ad-83be-40b1-a597-8c4e70a30596
```

## Testing

### 1. Backend Testing

```bash
# Test workflow config generation
python -c "
import asyncio
from ai.ira_builder.utils.workflow_config_generator import generate_workflow_config

# ... test with sample data
"

# Test production API client
python -c "
from backend.api.services.production_api_client import get_production_api_client

client = get_production_api_client(mode='Staging')
print(client.get_workflow_check('test_check_id'))
"
```

### 2. Frontend Testing

1. Complete a workflow through Analysis Report Review phase
2. Navigate to Live phase page
3. Enter Business Process ID
4. Select Staging mode
5. Click "Deploy to Staging"
6. Verify success message and check_id
7. Verify workflow config is generated correctly

### 3. Integration Testing

1. Create end-to-end workflow
2. Deploy to Staging
3. Verify deployment in Data Manager API
4. Update and redeploy
5. Verify updates are reflected

## Next Steps

1. ✅ Implement `/make-live` API endpoint in `backend/api/routes/workflows.py`
2. ✅ Create Live phase frontend page
3. ✅ Update workflow status navigation
4. ✅ Test end-to-end flow
5. ✅ Add error handling for deployment failures
6. ✅ Add loading states and progress indicators
7. ✅ Add deployment history/logs (optional enhancement)

## Files Modified/Created

### Created:
- ✅ `backend/api/services/production_api_client.py`
- ✅ `ai/ira_builder/utils/workflow_config_generator.py`
- ❌ `frontend/src/app/workflow/[id]/live/page.tsx` (TODO)

### Modified:
- ✅ `ai/ira_builder/orchestrator.py` (WorkflowPhase enum, WorkflowState)
- ✅ `backend/api/models/requests.py` (MakeWorkflowLiveRequest)
- ✅ `backend/api/models/responses.py` (MakeWorkflowLiveResponse, WorkflowPhaseEnum)
- ❌ `backend/api/routes/workflows.py` (TODO: add make_live endpoint)
- ❌ `frontend/src/components/*` (TODO: update status display)

## Notes

- The workflow config generator uses LLM to ensure proper formatting of code blocks and extraction of required files/columns
- Check IDs are auto-generated if not provided, using sanitized workflow name + timestamp
- Deployment status is saved in workflow state for audit trail
- Both Staging and Production environments are supported
- The system validates that analysis report is approved before allowing deployment
