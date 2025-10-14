# IRA Workflow Builder - Agentic System Architecture
## Using Microsoft Agent Framework

**Version**: 1.0
**Date**: 2025-10-15
**System**: Interactive Requirements Analyzer (IRA)

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Design](#architecture-design)
3. [Agent Specifications](#agent-specifications)
4. [Workflow Pattern](#workflow-pattern)
5. [State Management](#state-management)
6. [Human-in-the-Loop Integration](#human-in-the-loop-integration)
7. [Implementation Guide](#implementation-guide)
8. [Error Handling & Checkpointing](#error-handling--checkpointing)
9. [Deployment Considerations](#deployment-considerations)

---

## System Overview

### Problem Statement
Build an interactive workflow builder where users can:
1. Upload CSV files to the platform
2. Provide workflow name and description
3. Interact with AI agents to generate analysis code
4. Review and approve business logic
5. Receive and validate analysis results
6. Iterate until satisfied with the output

### Key Actors
- **User**: Business analyst providing requirements
- **Planner Agent (IRA-Planner)**: Requirements gathering and business logic documentation
- **Coder Agent (IRA-Coder)**: Python code generation and execution
- **Orchestrator**: Workflow management and state coordination

### Success Criteria
- ✅ Interactive requirements gathering (5-10 questions)
- ✅ Business logic document generation and approval
- ✅ Python code generation for CSV analysis
- ✅ Iterative refinement until user satisfaction
- ✅ Complete conversation history and checkpointing
- ✅ Error recovery and state persistence

---

## Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     IRA Workflow Builder                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Workflow Orchestrator                         │
│              (Graph-Based Workflow Pattern)                      │
└─────────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐
│  Planner Agent   │  │ Coder Agent  │  │ HITL Executors  │
│   (IRA-Planner)  │  │ (IRA-Coder)  │  │  (User Input)   │
└──────────────────┘  └──────────────┘  └─────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Shared State                               │
│  • CSV Metadata • Questions • Business Logic • Code • Results   │
└─────────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌──────────────────┐  ┌──────────────┐  ┌─────────────────┐
│   CSV Storage    │  │  Checkpoint  │  │   DevUI / API   │
│     (Files)      │  │   Storage    │  │   (Interface)   │
└──────────────────┘  └──────────────┘  └─────────────────┘
```

### Workflow Pattern Selection

**Pattern**: **Sequential + Conditional Loops with HITL**

**Rationale**:
- Sequential flow for planning → coding phases
- Conditional loops for iterative refinement
- Multiple HITL checkpoints for user approvals
- Checkpointing for state persistence

---

## Agent Specifications

### 1. Planner Agent (IRA-Planner)

**Role**: Requirements gathering and business logic documentation

**Responsibilities**:
1. Analyze uploaded CSV files (columns, data types, sample data)
2. Understand workflow name and description
3. Ask clarifying questions (5-10 questions)
4. Generate comprehensive business logic document
5. Iterate based on user feedback

**Tools**:
- `analyze_csv_structure()` - Parse CSV and extract schema
- `analyze_csv_statistics()` - Get statistical summaries
- `validate_business_logic()` - Validate logic completeness
- `generate_business_logic_document()` - Create structured document

**Instructions**:
```
You are IRA-Planner, an expert business analyst specializing in data analysis requirements.

Your goal is to understand the user's business analysis needs by:
1. Analyzing the uploaded CSV files to understand available data
2. Reading the workflow name and description provided by the user
3. Asking 5-10 targeted questions to clarify:
   - Specific metrics or KPIs needed
   - Filtering or grouping requirements
   - Calculations or transformations
   - Output format preferences
   - Business rules or constraints

After gathering requirements, create a comprehensive Business Logic Document containing:
- Summary of data sources
- Detailed business requirements
- Step-by-step analysis logic
- Expected output format
- Assumptions and constraints

Be conversational, professional, and thorough. Ask one question at a time.
Ensure complete understanding before generating the business logic document.
```

---

### 2. Coder Agent (IRA-Coder)

**Role**: Python code generation and execution

**Responsibilities**:
1. Read business logic document
2. Access CSV file metadata
3. Generate production-ready Python code
4. Execute code and handle errors
5. Generate answer dataframe
6. Iterate based on user feedback

**Tools**:
- `read_csv_file()` - Load CSV data
- `execute_python_code()` - Run analysis code in sandbox
- `save_dataframe()` - Save result to CSV
- `validate_code_syntax()` - Pre-execution validation
- `debug_code()` - Error analysis and fixing

**Instructions**:
```
You are IRA-Coder, an expert Python developer specializing in data analysis with pandas.

Your goal is to generate clean, efficient, and well-documented Python code based on:
1. The approved Business Logic Document
2. CSV file structures and metadata
3. Any specific user requirements

Your code should:
- Use pandas for data manipulation
- Include comprehensive error handling
- Add clear comments explaining each step
- Follow PEP 8 style guidelines
- Generate a clean answer dataframe
- Save results to CSV format

If execution fails:
- Analyze the error
- Explain the issue to the user
- Propose and implement a fix

Always prioritize code clarity and maintainability.
```

---

## Workflow Pattern

### Workflow States

```python
class WorkflowState(Enum):
    INIT = "init"                           # Initial state
    CSV_ANALYSIS = "csv_analysis"           # Analyzing uploaded files
    REQUIREMENTS_GATHERING = "requirements" # Asking questions
    AWAITING_USER_RESPONSE = "awaiting_response"
    BUSINESS_LOGIC_GENERATION = "logic_gen"
    BUSINESS_LOGIC_REVIEW = "logic_review"  # User reviewing logic
    CODE_GENERATION = "code_gen"
    CODE_EXECUTION = "code_exec"
    RESULT_REVIEW = "result_review"         # User reviewing results
    REFINEMENT = "refinement"               # User requested changes
    COMPLETED = "completed"
    ERROR = "error"
```

### Workflow Graph Structure

```
                    ┌──────────┐
                    │   INIT   │
                    └────┬─────┘
                         │
                         ▼
                 ┌───────────────┐
                 │ CSV_ANALYSIS  │
                 │  (Planner)    │
                 └───────┬───────┘
                         │
                         ▼
            ┌────────────────────────┐
            │ REQUIREMENTS_GATHERING │
            │     (Planner)          │
            └────────┬───────────────┘
                     │
                     ▼
          ┌─────────────────────┐
          │ AWAITING_USER_      │◄──────┐
          │    RESPONSE (HITL)  │       │
          └──────┬──────────────┘       │
                 │                      │
                 ▼                      │
       ┌─────────────────┐             │
       │ Process Answer  │             │
       └────┬────────────┘             │
            │                          │
       ┌────▼─────────────────┐        │
       │ More Questions?      │────Yes─┘
       └────┬─────────────────┘
            │ No
            ▼
    ┌────────────────────────┐
    │ BUSINESS_LOGIC_GEN     │
    │    (Planner)           │
    └────────┬───────────────┘
             │
             ▼
    ┌────────────────────────┐
    │ BUSINESS_LOGIC_REVIEW  │
    │      (HITL)            │
    └────┬──────────┬────────┘
         │          │
    Approve │   Changes │
         │          │
         │          ▼
         │    ┌──────────────┐
         │    │  Refinement  │
         │    │  (Planner)   │
         │    └──────┬───────┘
         │           │
         │◄──────────┘
         │
         ▼
    ┌────────────────┐
    │  CODE_GEN      │
    │  (Coder)       │
    └────┬───────────┘
         │
         ▼
    ┌────────────────┐
    │  CODE_EXEC     │
    │  (Coder)       │
    └────┬───────────┘
         │
         ▼
    ┌────────────────────┐
    │  RESULT_REVIEW     │
    │     (HITL)         │
    └────┬──────┬────────┘
         │      │
    Approve│  Changes│
         │      │
         │      ▼
         │  ┌──────────────┐
         │  │  Refinement  │
         │  │  (Coder)     │
         │  └──────┬───────┘
         │         │
         │◄────────┘
         │
         ▼
    ┌───────────┐
    │ COMPLETED │
    └───────────┘
```

---

## State Management

### Shared State Schema

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class CSVMetadata(BaseModel):
    """Metadata for uploaded CSV files"""
    filename: str
    path: str
    columns: List[str]
    dtypes: Dict[str, str]
    row_count: int
    sample_data: List[Dict[str, Any]]  # First 5 rows
    statistics: Optional[Dict[str, Any]] = None

class Question(BaseModel):
    """Question asked by planner"""
    question_id: int
    question_text: str
    asked_at: datetime
    answer: Optional[str] = None
    answered_at: Optional[datetime] = None

class BusinessLogic(BaseModel):
    """Business logic document"""
    version: int = 1
    summary: str
    data_sources: List[str]
    requirements: List[str]
    analysis_steps: List[str]
    expected_output: str
    assumptions: List[str]
    constraints: List[str]
    user_approved: bool = False
    feedback: Optional[str] = None

class CodeArtifact(BaseModel):
    """Generated code and execution results"""
    version: int = 1
    code: str
    execution_status: str  # "pending", "success", "error"
    output_dataframe_path: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    user_approved: bool = False
    feedback: Optional[str] = None

class WorkflowSharedState(BaseModel):
    """Complete workflow state"""
    # Metadata
    workflow_id: str
    workflow_name: str
    workflow_description: str
    created_at: datetime
    updated_at: datetime

    # Current state
    current_state: str  # WorkflowState enum value

    # CSV Data
    csv_files: List[CSVMetadata]

    # Planning Phase
    questions_asked: List[Question] = []
    max_questions: int = 10

    # Business Logic
    business_logic_versions: List[BusinessLogic] = []
    current_business_logic: Optional[BusinessLogic] = None

    # Coding Phase
    code_versions: List[CodeArtifact] = []
    current_code: Optional[CodeArtifact] = None

    # Conversation History
    conversation_history: List[Dict[str, Any]] = []

    # Checkpoints
    checkpoint_ids: List[str] = []
```

---

## Human-in-the-Loop Integration

### HITL Points

1. **Requirements Gathering Loop**
   - User answers each question
   - RequestInfoExecutor pauses workflow
   - User input appended to conversation

2. **Business Logic Review**
   - Display formatted business logic document
   - User options: "Approve" or "Request Changes"
   - If changes: capture feedback and loop back to Planner

3. **Result Review**
   - Display answer dataframe (preview + download)
   - User options: "Approve" or "Request Changes"
   - If changes: capture feedback and loop back to Coder

### HITL Implementation Pattern

```python
from agent_framework.workflows import RequestInfoExecutor, RequestInfoMessage

class UserQuestionRequest(RequestInfoMessage):
    """Request for user to answer a question"""
    question: str
    question_id: int

class BusinessLogicApprovalRequest(RequestInfoMessage):
    """Request for business logic approval"""
    business_logic: BusinessLogic
    options: List[str] = ["approve", "request_changes"]

class ResultApprovalRequest(RequestInfoMessage):
    """Request for result approval"""
    result_dataframe_path: str
    result_preview: str  # First 20 rows as markdown table
    options: List[str] = ["approve", "request_changes"]

# Handler functions
async def handle_user_question(request: UserQuestionRequest) -> str:
    """Called when planner asks a question"""
    # Implementation will interface with frontend
    return user_input

async def handle_business_logic_approval(
    request: BusinessLogicApprovalRequest
) -> Dict[str, Any]:
    """Called when business logic needs approval"""
    return {
        "decision": "approve" | "request_changes",
        "feedback": "..." if changes requested
    }

async def handle_result_approval(
    request: ResultApprovalRequest
) -> Dict[str, Any]:
    """Called when results need approval"""
    return {
        "decision": "approve" | "request_changes",
        "feedback": "..." if changes requested
    }
```

---

## Implementation Guide

### Phase 1: Project Setup

```bash
# Create project structure
mkdir ira_workflow_builder
cd ira_workflow_builder

# Install dependencies
pip install agent-framework --pre
pip install pandas numpy openpyxl

# Create directory structure
mkdir -p {agents,workflows,tools,storage,tests}
touch agents/{planner.py,coder.py}
touch workflows/ira_workflow.py
touch tools/{csv_tools.py,code_tools.py}
```

### Phase 2: Tool Implementation

**File**: `tools/csv_tools.py`

```python
"""CSV analysis tools for Planner Agent"""
import pandas as pd
from typing import Dict, Any, List
from pathlib import Path

def analyze_csv_structure(filepath: str) -> Dict[str, Any]:
    """
    Analyze CSV file structure and return metadata.

    Args:
        filepath: Path to CSV file

    Returns:
        Dictionary with columns, dtypes, row count, and sample data
    """
    df = pd.read_csv(filepath)

    return {
        "filename": Path(filepath).name,
        "columns": df.columns.tolist(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "row_count": len(df),
        "sample_data": df.head(5).to_dict(orient="records"),
        "statistics": {
            col: df[col].describe().to_dict()
            for col in df.select_dtypes(include=['number']).columns
        }
    }

def get_csv_summary(filepaths: List[str]) -> str:
    """
    Get human-readable summary of CSV files.

    Args:
        filepaths: List of CSV file paths

    Returns:
        Formatted string summary
    """
    summaries = []
    for filepath in filepaths:
        meta = analyze_csv_structure(filepath)
        summary = f"""
File: {meta['filename']}
Rows: {meta['row_count']}
Columns: {', '.join(meta['columns'])}
Types: {', '.join(f"{k}:{v}" for k, v in meta['dtypes'].items())}
        """
        summaries.append(summary.strip())

    return "\n\n".join(summaries)

def validate_column_references(
    column_names: List[str],
    available_columns: List[str]
) -> Dict[str, Any]:
    """
    Validate that referenced columns exist.

    Args:
        column_names: Columns referenced in business logic
        available_columns: Available columns in CSV

    Returns:
        Validation result
    """
    missing = [c for c in column_names if c not in available_columns]
    return {
        "valid": len(missing) == 0,
        "missing_columns": missing
    }
```

**File**: `tools/code_tools.py`

```python
"""Code execution tools for Coder Agent"""
import subprocess
import tempfile
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple

def execute_python_code(
    code: str,
    csv_filepaths: List[str],
    output_path: str,
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Execute Python code in a sandboxed environment.

    Args:
        code: Python code to execute
        csv_filepaths: Paths to input CSV files
        output_path: Path to save output dataframe
        timeout: Execution timeout in seconds

    Returns:
        Execution result with status, output path, or error
    """
    try:
        # Create temporary script
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:
            # Inject CSV paths and output path
            setup_code = f"""
import pandas as pd
import numpy as np
from pathlib import Path

# Input CSV files
csv_files = {csv_filepaths}
output_path = "{output_path}"

"""
            f.write(setup_code + code)
            script_path = f.name

        # Execute with timeout
        result = subprocess.run(
            ["python", script_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Clean up
        Path(script_path).unlink()

        if result.returncode == 0:
            # Verify output file exists
            if Path(output_path).exists():
                return {
                    "status": "success",
                    "output_path": output_path,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                return {
                    "status": "error",
                    "error_message": "Code executed but output file not created",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
        else:
            return {
                "status": "error",
                "error_message": result.stderr,
                "stdout": result.stdout
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error_message": f"Execution timeout after {timeout} seconds"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }

def validate_code_syntax(code: str) -> Dict[str, Any]:
    """
    Validate Python code syntax without execution.

    Args:
        code: Python code to validate

    Returns:
        Validation result
    """
    try:
        compile(code, '<string>', 'exec')
        return {"valid": True}
    except SyntaxError as e:
        return {
            "valid": False,
            "error": str(e),
            "line": e.lineno
        }

def preview_dataframe(filepath: str, rows: int = 20) -> str:
    """
    Generate preview of dataframe as markdown table.

    Args:
        filepath: Path to CSV file
        rows: Number of rows to preview

    Returns:
        Markdown formatted table
    """
    df = pd.read_csv(filepath)
    return df.head(rows).to_markdown(index=False)
```

### Phase 3: Agent Implementation

**File**: `agents/planner.py`

```python
"""Planner Agent (IRA-Planner) implementation"""
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
from typing import List
import sys
sys.path.append('..')
from tools.csv_tools import (
    analyze_csv_structure,
    get_csv_summary,
    validate_column_references
)

PLANNER_INSTRUCTIONS = """
You are IRA-Planner, an expert business analyst specializing in data analysis requirements.

Your goal is to understand the user's business analysis needs by:
1. Analyzing the uploaded CSV files to understand available data
2. Reading the workflow name and description provided by the user
3. Asking 5-10 targeted questions to clarify:
   - Specific metrics or KPIs needed
   - Filtering or grouping requirements
   - Calculations or transformations needed
   - Output format preferences
   - Business rules or constraints
   - Edge cases to handle

After gathering requirements through questions, create a comprehensive Business Logic Document containing:

**Structure:**
# Business Logic Document - [Workflow Name]

## 1. Executive Summary
- Brief overview of the analysis objective

## 2. Data Sources
- List of CSV files and their purposes
- Key columns from each file

## 3. Detailed Requirements
- Specific metrics/KPIs to calculate
- Filtering criteria
- Grouping/aggregation rules
- Joins or merges needed

## 4. Analysis Steps
- Step-by-step logic flow
- Order of operations
- Transformations needed

## 5. Expected Output
- Output dataframe structure
- Column names and types
- Sort order
- Any formatting requirements

## 6. Assumptions & Constraints
- Data quality assumptions
- Business rules
- Edge case handling

**Guidelines:**
- Ask one question at a time for better user experience
- Be conversational and professional
- Confirm understanding before moving to the next question
- Once you have enough information (5-10 Q&A pairs), generate the business logic document
- Make the document clear enough for a Python developer to implement
"""

def create_planner_agent() -> ChatAgent:
    """Create and configure the Planner Agent"""

    agent = ChatAgent(
        name="IRA-Planner",
        chat_client=OpenAIChatClient(
            model="gpt-4o",
            temperature=0.7
        ),
        instructions=PLANNER_INSTRUCTIONS,
        tools=[
            analyze_csv_structure,
            get_csv_summary,
            validate_column_references
        ]
    )

    return agent
```

**File**: `agents/coder.py`

```python
"""Coder Agent (IRA-Coder) implementation"""
from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient
import sys
sys.path.append('..')
from tools.code_tools import (
    execute_python_code,
    validate_code_syntax,
    preview_dataframe
)

CODER_INSTRUCTIONS = """
You are IRA-Coder, an expert Python developer specializing in data analysis with pandas.

Your goal is to generate clean, efficient, and well-documented Python code based on:
1. The approved Business Logic Document
2. CSV file structures and metadata
3. Any specific user requirements or feedback

**Code Requirements:**
- Use pandas for all data manipulation
- Include comprehensive error handling
- Add clear comments explaining each step
- Follow PEP 8 style guidelines
- Handle missing values appropriately
- Validate data types and ranges
- Generate a clean answer dataframe
- Save final result to the specified output path

**Code Structure:**
```python
import pandas as pd
import numpy as np
from pathlib import Path

# 1. Load CSV files
# [Your code with comments]

# 2. Data validation and cleaning
# [Your code with comments]

# 3. Apply business logic
# [Your code with comments]

# 4. Generate answer dataframe
# [Your code with comments]

# 5. Save result
answer_df.to_csv(output_path, index=False)
print(f"Analysis complete. Output saved to {output_path}")
print(f"Result shape: {answer_df.shape}")
```

**Error Handling:**
If execution fails:
1. Analyze the error carefully
2. Explain the issue in simple terms
3. Propose a fix
4. Implement the corrected code

**Iteration:**
If user requests changes:
1. Understand the requested modification
2. Update the code accordingly
3. Maintain code quality and comments
4. Re-test thoroughly

Always prioritize code clarity, correctness, and maintainability.
"""

def create_coder_agent() -> ChatAgent:
    """Create and configure the Coder Agent"""

    agent = ChatAgent(
        name="IRA-Coder",
        chat_client=OpenAIChatClient(
            model="gpt-4o",
            temperature=0.3  # Lower temperature for more deterministic code
        ),
        instructions=CODER_INSTRUCTIONS,
        tools=[
            execute_python_code,
            validate_code_syntax,
            preview_dataframe
        ]
    )

    return agent
```

### Phase 4: Workflow Implementation

**File**: `workflows/ira_workflow.py`

```python
"""
IRA Workflow Builder - Main workflow implementation
"""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from agent_framework import ChatMessage, Role
from agent_framework.workflows import (
    WorkflowBuilder,
    RequestInfoExecutor,
    RequestInfoMessage,
    FunctionExecutor
)
from agent_framework.workflows.checkpointing import CheckpointManager

import sys
sys.path.append('..')
from agents.planner import create_planner_agent
from agents.coder import create_coder_agent
from tools.csv_tools import analyze_csv_structure
from tools.code_tools import preview_dataframe


# ============================================================================
# Custom Request Message Types (for HITL)
# ============================================================================

class UserQuestionRequest(RequestInfoMessage):
    """Request for user to answer planner's question"""
    question: str
    question_number: int
    total_questions_so_far: int


class BusinessLogicApprovalRequest(RequestInfoMessage):
    """Request for user to approve business logic"""
    business_logic_document: str
    options: List[str] = ["approve", "request_changes"]


class ResultApprovalRequest(RequestInfoMessage):
    """Request for user to approve analysis results"""
    result_path: str
    result_preview: str
    options: List[str] = ["approve", "request_changes"]


# ============================================================================
# Workflow State Manager
# ============================================================================

class IRAWorkflowState:
    """Manages shared state across the workflow"""

    def __init__(
        self,
        workflow_id: str,
        workflow_name: str,
        workflow_description: str,
        csv_filepaths: List[str]
    ):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.workflow_description = workflow_description
        self.csv_filepaths = csv_filepaths
        self.created_at = datetime.now()

        # CSV metadata
        self.csv_metadata = [
            analyze_csv_structure(fp) for fp in csv_filepaths
        ]

        # Planning phase
        self.questions: List[Dict[str, Any]] = []
        self.max_questions = 10

        # Business logic
        self.business_logic_document: Optional[str] = None
        self.business_logic_approved = False

        # Coding phase
        self.generated_code: Optional[str] = None
        self.execution_result: Optional[Dict[str, Any]] = None
        self.result_approved = False

        # Conversation history
        self.conversation: List[ChatMessage] = []

    def add_question(self, question: str) -> int:
        """Add a question to the list"""
        q_id = len(self.questions) + 1
        self.questions.append({
            "id": q_id,
            "question": question,
            "answer": None,
            "asked_at": datetime.now()
        })
        return q_id

    def answer_question(self, q_id: int, answer: str):
        """Record answer to a question"""
        for q in self.questions:
            if q["id"] == q_id:
                q["answer"] = answer
                q["answered_at"] = datetime.now()
                break

    def should_continue_asking(self) -> bool:
        """Determine if planner should ask more questions"""
        answered = sum(1 for q in self.questions if q["answer"])
        return answered < self.max_questions

    def get_qa_summary(self) -> str:
        """Get formatted Q&A summary"""
        lines = []
        for q in self.questions:
            if q["answer"]:
                lines.append(f"Q{q['id']}: {q['question']}")
                lines.append(f"A{q['id']}: {q['answer']}")
                lines.append("")
        return "\n".join(lines)


# ============================================================================
# Executor Functions
# ============================================================================

async def initialize_workflow(state: IRAWorkflowState) -> ChatMessage:
    """Initialize workflow with CSV analysis"""
    csv_summary = "\n\n".join([
        f"**{meta['filename']}**\n"
        f"- Rows: {meta['row_count']}\n"
        f"- Columns: {', '.join(meta['columns'])}"
        for meta in state.csv_metadata
    ])

    context = f"""
# Workflow Initialization

**Workflow Name:** {state.workflow_name}

**Workflow Description:** {state.workflow_description}

**Uploaded CSV Files:**
{csv_summary}

You are starting the requirements gathering phase. Analyze the above information
and begin asking clarifying questions to understand the user's analysis needs.
"""

    return ChatMessage(
        role=Role.SYSTEM,
        text=context
    )


async def check_if_ready_for_logic_gen(state: IRAWorkflowState) -> str:
    """Determine if enough information gathered"""
    answered = sum(1 for q in state.questions if q["answer"])

    if answered >= 5:  # Minimum 5 questions answered
        return "generate_logic"
    elif answered >= state.max_questions:
        return "generate_logic"
    else:
        return "ask_more"


async def prepare_business_logic_context(state: IRAWorkflowState) -> ChatMessage:
    """Prepare context for business logic generation"""
    qa_summary = state.get_qa_summary()

    prompt = f"""
Based on the requirements gathering phase, generate a comprehensive Business Logic Document.

**Q&A Summary:**
{qa_summary}

**CSV Files Available:**
{[meta['filename'] for meta in state.csv_metadata]}

Generate the document following the structure in your instructions.
"""

    return ChatMessage(role=Role.USER, text=prompt)


async def extract_business_logic(response: ChatMessage, state: IRAWorkflowState):
    """Extract and store business logic document"""
    state.business_logic_document = response.text
    state.business_logic_approved = False


async def prepare_coding_context(state: IRAWorkflowState) -> ChatMessage:
    """Prepare context for code generation"""
    output_path = f"output/{state.workflow_id}_result.csv"

    prompt = f"""
Generate Python code to implement the following business logic.

**Business Logic Document:**
{state.business_logic_document}

**CSV File Paths:**
{state.csv_filepaths}

**Output Path:**
{output_path}

Generate complete, executable Python code following your instructions.
"""

    return ChatMessage(role=Role.USER, text=prompt)


async def extract_and_execute_code(
    response: ChatMessage,
    state: IRAWorkflowState
) -> Dict[str, Any]:
    """Extract code and execute it"""
    from tools.code_tools import execute_python_code

    # Extract code from markdown if present
    code = response.text
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()

    state.generated_code = code

    # Execute code
    output_path = f"output/{state.workflow_id}_result.csv"
    Path("output").mkdir(exist_ok=True)

    result = execute_python_code(
        code=code,
        csv_filepaths=state.csv_filepaths,
        output_path=output_path
    )

    state.execution_result = result
    return result


# ============================================================================
# HITL Handler Functions
# ============================================================================

async def handle_user_question(request: UserQuestionRequest) -> str:
    """
    Handle user question request.
    In production, this would interface with your frontend.
    """
    print(f"\n{'='*60}")
    print(f"Question {request.question_number}:")
    print(f"{request.question}")
    print(f"{'='*60}")

    # In production: send to frontend and await response
    # For now: simulate with input
    answer = input("Your answer: ")
    return answer


async def handle_business_logic_approval(
    request: BusinessLogicApprovalRequest
) -> Dict[str, Any]:
    """
    Handle business logic approval request.
    In production, this would interface with your frontend.
    """
    print(f"\n{'='*60}")
    print("BUSINESS LOGIC DOCUMENT FOR REVIEW")
    print(f"{'='*60}")
    print(request.business_logic_document)
    print(f"{'='*60}")

    # In production: send to frontend and await response
    decision = input("\nApprove or Request Changes? (approve/changes): ").lower()

    result = {"decision": decision}
    if decision == "changes":
        feedback = input("Please describe the changes you want: ")
        result["feedback"] = feedback

    return result


async def handle_result_approval(
    request: ResultApprovalRequest
) -> Dict[str, Any]:
    """
    Handle result approval request.
    In production, this would interface with your frontend.
    """
    print(f"\n{'='*60}")
    print("ANALYSIS RESULTS FOR REVIEW")
    print(f"{'='*60}")
    print(f"Result file: {request.result_path}")
    print(f"\nPreview (first 20 rows):")
    print(request.result_preview)
    print(f"{'='*60}")

    # In production: send to frontend and await response
    decision = input("\nApprove or Request Changes? (approve/changes): ").lower()

    result = {"decision": decision}
    if decision == "changes":
        feedback = input("Please describe the changes you want: ")
        result["feedback"] = feedback

    return result


# ============================================================================
# Main Workflow Builder
# ============================================================================

def build_ira_workflow(
    workflow_id: str,
    workflow_name: str,
    workflow_description: str,
    csv_filepaths: List[str]
) -> WorkflowBuilder:
    """
    Build the complete IRA workflow with all agents and HITL points.
    """

    # Initialize state
    state = IRAWorkflowState(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        workflow_description=workflow_description,
        csv_filepaths=csv_filepaths
    )

    # Create agents
    planner = create_planner_agent()
    coder = create_coder_agent()

    # Build workflow
    workflow = (
        WorkflowBuilder()

        # 1. Initialize
        .add_executor(
            "init",
            FunctionExecutor(lambda: initialize_workflow(state))
        )

        # 2. Planner agent for requirements gathering
        .add_agent("planner_gathering", planner)
        .add_edge("init", "planner_gathering")

        # 3. HITL: Ask user questions (loop)
        .add_executor(
            "ask_question",
            RequestInfoExecutor(
                handler=handle_user_question,
                request_class=UserQuestionRequest
            )
        )
        .add_edge("planner_gathering", "ask_question")

        # 4. Check if ready for logic generation
        .add_executor(
            "check_ready",
            FunctionExecutor(lambda: check_if_ready_for_logic_gen(state))
        )
        .add_edge("ask_question", "check_ready")

        # 5. Conditional: ask more or generate logic
        .add_edge(
            "check_ready",
            "planner_gathering",
            condition=lambda result: result == "ask_more"
        )

        # 6. Generate business logic
        .add_executor(
            "prepare_logic_context",
            FunctionExecutor(lambda: prepare_business_logic_context(state))
        )
        .add_edge(
            "check_ready",
            "prepare_logic_context",
            condition=lambda result: result == "generate_logic"
        )

        .add_agent("planner_logic_gen", planner)
        .add_edge("prepare_logic_context", "planner_logic_gen")

        # 7. Extract business logic
        .add_executor(
            "extract_logic",
            FunctionExecutor(
                lambda msg: extract_business_logic(msg, state)
            )
        )
        .add_edge("planner_logic_gen", "extract_logic")

        # 8. HITL: Business logic approval
        .add_executor(
            "approve_logic",
            RequestInfoExecutor(
                handler=handle_business_logic_approval,
                request_class=BusinessLogicApprovalRequest
            )
        )
        .add_edge("extract_logic", "approve_logic")

        # 9. Conditional: approved or needs changes
        .add_edge(
            "approve_logic",
            "prepare_logic_context",
            condition=lambda result: result["decision"] == "changes"
        )

        # 10. Prepare coding context
        .add_executor(
            "prepare_code_context",
            FunctionExecutor(lambda: prepare_coding_context(state))
        )
        .add_edge(
            "approve_logic",
            "prepare_code_context",
            condition=lambda result: result["decision"] == "approve"
        )

        # 11. Coder agent generates code
        .add_agent("coder_gen", coder)
        .add_edge("prepare_code_context", "coder_gen")

        # 12. Execute code
        .add_executor(
            "execute_code",
            FunctionExecutor(
                lambda msg: extract_and_execute_code(msg, state)
            )
        )
        .add_edge("coder_gen", "execute_code")

        # 13. HITL: Result approval
        .add_executor(
            "approve_result",
            RequestInfoExecutor(
                handler=handle_result_approval,
                request_class=ResultApprovalRequest
            )
        )
        .add_edge("execute_code", "approve_result")

        # 14. Conditional: approved or needs changes
        .add_edge(
            "approve_result",
            "prepare_code_context",
            condition=lambda result: result["decision"] == "changes"
        )

        # 15. Complete
        .add_executor(
            "complete",
            FunctionExecutor(lambda: "Workflow completed successfully!")
        )
        .add_edge(
            "approve_result",
            "complete",
            condition=lambda result: result["decision"] == "approve"
        )

        .build()
    )

    return workflow, state


# ============================================================================
# Main Execution
# ============================================================================

async def main():
    """Example execution"""

    # Example inputs
    workflow_id = "wf_001"
    workflow_name = "Sales Analysis Q4"
    workflow_description = "Analyze Q4 sales data to identify top performers"
    csv_filepaths = [
        "data/sales_q4.csv",
        "data/products.csv"
    ]

    # Build workflow
    workflow, state = build_ira_workflow(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        workflow_description=workflow_description,
        csv_filepaths=csv_filepaths
    )

    # Execute workflow with streaming
    print("Starting IRA Workflow Builder...")

    async for event in workflow.run_stream():
        # Handle different event types
        if event.type == "executor_started":
            print(f"\n▶ Starting: {event.executor_name}")
        elif event.type == "executor_completed":
            print(f"✓ Completed: {event.executor_name}")
        # Add more event handling as needed

    print("\n✓ Workflow execution complete!")
    print(f"Final result saved to: output/{workflow_id}_result.csv")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Error Handling & Checkpointing

### Checkpoint Strategy

```python
from agent_framework.workflows.checkpointing import CheckpointManager

# Enable checkpointing
checkpoint_manager = CheckpointManager(storage_path="checkpoints/")

# Save checkpoint after each major phase
checkpoint_id = await workflow.save_checkpoint(
    checkpoint_name=f"{workflow_id}_phase_{phase_name}"
)

# Resume from checkpoint
workflow = await workflow.resume_from_checkpoint(checkpoint_id)
```

### Error Recovery

```python
# Wrap workflow execution with error handling
try:
    result = await workflow.run()
except WorkflowExecutionError as e:
    # Log error
    logger.error(f"Workflow failed: {e}")

    # Save checkpoint for recovery
    checkpoint_id = await workflow.save_checkpoint("error_recovery")

    # Notify user
    await notify_user(f"Workflow paused. Checkpoint: {checkpoint_id}")
```

---

## Deployment Considerations

### 1. Frontend Integration

```python
# FastAPI endpoint example
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.websocket("/ws/workflow/{workflow_id}")
async def workflow_websocket(websocket: WebSocket, workflow_id: str):
    await websocket.accept()

    # Build workflow
    workflow, state = build_ira_workflow(...)

    # Stream events to frontend
    async for event in workflow.run_stream():
        await websocket.send_json({
            "type": event.type,
            "data": event.model_dump()
        })
```

### 2. Storage Backend

- **CSV Storage**: S3, Azure Blob, or local filesystem
- **Checkpoint Storage**: Redis, PostgreSQL, or filesystem
- **Conversation History**: MongoDB, PostgreSQL

### 3. DevUI Integration

```bash
# Launch DevUI for testing
devui ./workflows --port 8080 --tracing framework
```

### 4. Production Deployment

- Use Azure Container Apps or Kubernetes
- Enable OpenTelemetry for monitoring
- Set up proper authentication/authorization
- Implement rate limiting
- Add queue system for long-running workflows (Celery, Azure Service Bus)

---

## Next Steps

### Immediate (Phase 1)
1. ✅ Implement basic agents (Planner, Coder)
2. ✅ Implement tool functions
3. ✅ Build sequential workflow with HITL
4. ✅ Test with sample CSV files

### Short-term (Phase 2)
1. Add checkpointing and recovery
2. Implement frontend integration (FastAPI + React)
3. Add conversation history persistence
4. Implement proper error handling

### Medium-term (Phase 3)
1. Add multi-user support
2. Implement workflow templates
3. Add code validation and security sandboxing
4. Build workflow analytics dashboard

### Long-term (Phase 4)
1. Add workflow versioning
2. Implement A/B testing for agents
3. Add reinforcement learning from user feedback
4. Build workflow marketplace

---

## Conclusion

This architecture leverages Microsoft Agent Framework's strengths:
- **Graph-based workflows** for complex orchestration
- **HITL integration** for user approvals and feedback
- **Checkpointing** for long-running processes
- **Streaming** for real-time updates
- **State management** for conversation context

The design is:
- ✅ **Scalable**: Can handle multiple concurrent workflows
- ✅ **Maintainable**: Clear separation of concerns
- ✅ **Testable**: Each component can be tested independently
- ✅ **User-friendly**: Clear interaction points with iterative refinement
- ✅ **Production-ready**: Error handling, checkpointing, and monitoring

---

**End of Architecture Document**
