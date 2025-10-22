"""
Response models for the IRA Workflow Builder API.

These Pydantic models define the structure of outgoing API responses.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class WorkflowPhaseEnum(str, Enum):
    """Workflow execution phases."""
    NOT_STARTED = "not_started"
    PLANNING = "planning"
    PLAN_REVIEW = "plan_review"
    CODING = "coding"
    OUTPUT_REVIEW = "output_review"
    COMPLETED = "completed"
    FAILED = "failed"


class ResponseTypeEnum(str, Enum):
    """Types of responses from the planner agent."""
    QUESTION = "question"
    BUSINESS_LOGIC_PLAN = "business_logic_plan"
    ACKNOWLEDGMENT = "acknowledgment"
    ERROR = "error"


class WorkflowCreateResponse(BaseModel):
    """Response model for workflow creation."""

    workflow_id: str = Field(
        ...,
        description="Unique identifier for the workflow",
        examples=["sales_analysis_q4_20241016_143025"]
    )
    status: str = Field(
        ...,
        description="Status of the creation operation",
        examples=["success", "error"]
    )
    phase: WorkflowPhaseEnum = Field(
        ...,
        description="Current phase of the workflow",
        examples=["not_started", "planning"]
    )
    message: Optional[str] = Field(
        default=None,
        description="Additional message about the operation",
        examples=["Workflow created successfully"]
    )
    csv_files_count: int = Field(
        ...,
        description="Number of CSV files uploaded",
        examples=[1, 2, 3]
    )


class QuestionResponse(BaseModel):
    """Response model for planner questions."""

    status: str = Field(
        ...,
        description="Status of the operation",
        examples=["success", "error"]
    )
    phase: WorkflowPhaseEnum = Field(
        ...,
        description="Current workflow phase",
        examples=["planning", "plan_review"]
    )
    response: str = Field(
        ...,
        description="The planner's response (question or acknowledgment)",
        examples=["What threshold should we use for flagging exceptions?\n\nPlease select one option:\nA) Flag all cases\nB) Only cases with >30 days difference"]
    )
    response_type: ResponseTypeEnum = Field(
        ...,
        description="Type of response",
        examples=["question", "acknowledgment"]
    )
    question_number: Optional[int] = Field(
        default=None,
        description="Current question number (if applicable)",
        examples=[1, 2, 3]
    )
    total_questions: Optional[int] = Field(
        default=None,
        description="Maximum number of questions",
        examples=[10]
    )


class BusinessLogicPlanResponse(BaseModel):
    """Response model for business logic plan."""

    status: str = Field(
        ...,
        description="Status of the operation",
        examples=["success", "error"]
    )
    phase: WorkflowPhaseEnum = Field(
        ...,
        description="Current workflow phase",
        examples=["plan_review"]
    )
    business_logic_plan: str = Field(
        ...,
        description="The generated business logic plan in markdown format"
    )
    plan_approved: bool = Field(
        default=False,
        description="Whether the plan has been approved by the user"
    )


class CodeGenerationResponse(BaseModel):
    """Response model for code generation."""

    status: str = Field(
        ...,
        description="Status of the operation",
        examples=["success", "error", "generating"]
    )
    phase: WorkflowPhaseEnum = Field(
        ...,
        description="Current workflow phase",
        examples=["coding", "output_review"]
    )
    code: Optional[str] = Field(
        default=None,
        description="Generated Python code"
    )
    code_filepath: Optional[str] = Field(
        default=None,
        description="Path to saved code file",
        examples=["./storage/generated_code/sales_analysis_20241016_143025.py"]
    )
    output_path: Optional[str] = Field(
        default=None,
        description="Path to generated output CSV",
        examples=["./data/output/sales_analysis/result.csv"]
    )
    output_preview: Optional[str] = Field(
        default=None,
        description="Preview of the output data (first 10 rows)"
    )
    output_summary: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Summary statistics of the output"
    )
    iterations: Optional[int] = Field(
        default=None,
        description="Number of code generation iterations",
        examples=[1, 2, 3]
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if code generation failed"
    )


class OutputRefinementResponse(BaseModel):
    """Response model for output refinement."""

    status: str = Field(
        ...,
        description="Status of the operation",
        examples=["success", "error"]
    )
    phase: WorkflowPhaseEnum = Field(
        ...,
        description="Current workflow phase",
        examples=["plan_review", "output_review"]
    )
    updated_plan: Optional[str] = Field(
        default=None,
        description="Updated Business Logic Plan (if phase is plan_review)"
    )
    message: Optional[str] = Field(
        default=None,
        description="Message describing next steps"
    )
    code: Optional[str] = Field(
        default=None,
        description="Refined Python code (if code was regenerated)"
    )
    code_filepath: Optional[str] = Field(
        default=None,
        description="Path to saved refined code file"
    )
    output_path: Optional[str] = Field(
        default=None,
        description="Path to refined output CSV"
    )
    output_preview: Optional[str] = Field(
        default=None,
        description="Preview of the refined output data"
    )
    output_summary: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Summary statistics of the refined output"
    )
    refinement_iteration: int = Field(
        ...,
        description="Current refinement iteration number",
        examples=[1, 2, 3]
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if refinement failed"
    )


class WorkflowCompletionResponse(BaseModel):
    """Response model for workflow completion."""

    status: str = Field(
        ...,
        description="Status of the operation",
        examples=["success"]
    )
    phase: WorkflowPhaseEnum = Field(
        ...,
        description="Final workflow phase",
        examples=["completed"]
    )
    output_path: str = Field(
        ...,
        description="Path to final output CSV file"
    )
    execution_time: float = Field(
        ...,
        description="Total workflow execution time in seconds",
        examples=[125.5, 300.2]
    )
    is_successful: bool = Field(
        ...,
        description="Whether the workflow completed successfully"
    )


class WorkflowListItem(BaseModel):
    """Model for workflow list item."""

    workflow_id: str = Field(
        ...,
        description="Unique workflow identifier"
    )
    name: str = Field(
        ...,
        description="Workflow name"
    )
    description: str = Field(
        ...,
        description="Workflow description"
    )
    phase: WorkflowPhaseEnum = Field(
        ...,
        description="Current workflow phase"
    )
    created_at: datetime = Field(
        ...,
        description="When the workflow was created"
    )
    updated_at: datetime = Field(
        ...,
        description="When the workflow was last updated"
    )
    csv_files_count: int = Field(
        ...,
        description="Number of CSV files in this workflow"
    )
    is_successful: bool = Field(
        default=False,
        description="Whether the workflow completed successfully"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if workflow failed"
    )


class WorkflowListResponse(BaseModel):
    """Response model for workflow list."""

    status: str = Field(
        ...,
        description="Status of the operation",
        examples=["success"]
    )
    workflows: List[WorkflowListItem] = Field(
        ...,
        description="List of workflows"
    )
    total: int = Field(
        ...,
        description="Total number of workflows matching filters",
        examples=[5, 10, 25]
    )
    limit: int = Field(
        ...,
        description="Maximum workflows returned",
        examples=[50]
    )
    offset: int = Field(
        ...,
        description="Number of workflows skipped",
        examples=[0, 10]
    )


class WorkflowDetailResponse(BaseModel):
    """Response model for detailed workflow information."""

    workflow_id: str = Field(..., description="Unique workflow identifier")
    workflow_name: str = Field(..., description="Workflow name")
    workflow_description: str = Field(..., description="Workflow description")
    phase: WorkflowPhaseEnum = Field(..., description="Current workflow phase")
    started_at: Optional[datetime] = Field(None, description="When workflow started")
    completed_at: Optional[datetime] = Field(None, description="When workflow completed")
    csv_filepaths: List[str] = Field(..., description="Paths to CSV files")
    planner_questions_asked: int = Field(..., description="Number of questions asked by planner")
    current_question: Optional[str] = Field(None, description="Current question from planner")
    business_logic_plan: Optional[str] = Field(None, description="Business logic plan")
    plan_approved: bool = Field(..., description="Whether plan is approved")
    generated_code: Optional[str] = Field(None, description="Generated code")
    code_execution_iterations: int = Field(..., description="Code execution iterations")
    output_file_path: Optional[str] = Field(None, description="Path to output file")
    output_approved: bool = Field(..., description="Whether output is approved")
    output_refinement_iterations: int = Field(..., description="Output refinement iterations")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    is_successful: bool = Field(..., description="Whether workflow is successful")


class ErrorResponse(BaseModel):
    """Response model for API errors."""

    status: str = Field(
        default="error",
        description="Status of the response"
    )
    error: str = Field(
        ...,
        description="Error message",
        examples=["Workflow not found", "Invalid input"]
    )
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information"
    )
    code: Optional[str] = Field(
        default=None,
        description="Error code",
        examples=["WORKFLOW_NOT_FOUND", "INVALID_PHASE"]
    )


class WebSocketEvent(BaseModel):
    """Model for WebSocket events."""

    event_type: str = Field(
        ...,
        description="Type of event",
        examples=["phase_change", "progress", "log", "error", "completed"]
    )
    workflow_id: str = Field(
        ...,
        description="Workflow identifier"
    )
    data: Dict[str, Any] = Field(
        ...,
        description="Event data"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Event timestamp"
    )
