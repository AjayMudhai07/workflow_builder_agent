"""
Request models for the IRA Workflow Builder API.

These Pydantic models define the structure of incoming API requests.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class WorkflowCreateRequest(BaseModel):
    """Request model for creating a new workflow."""

    name: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Name of the workflow",
        examples=["Sales Analysis Q4 2024"]
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Description of what the workflow should accomplish",
        examples=["Identify expense transactions where document date falls in a different period than posting date"]
    )
    output_filename: Optional[str] = Field(
        default="result.csv",
        max_length=200,
        description="Name for the output CSV file",
        examples=["result.csv", "expense_exceptions.csv"]
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate workflow name."""
        if not v.strip():
            raise ValueError("Workflow name cannot be empty")
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate workflow description."""
        if not v.strip():
            raise ValueError("Workflow description cannot be empty")
        return v.strip()

    @field_validator('output_filename')
    @classmethod
    def validate_output_filename(cls, v: Optional[str]) -> str:
        """Validate output filename."""
        if v is None:
            return "result.csv"
        v = v.strip()
        if not v.endswith('.csv'):
            v += '.csv'
        return v


class AnswerSubmitRequest(BaseModel):
    """Request model for submitting an answer to a planner question."""

    answer: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's answer to the planner's question",
        examples=["Option A", "Yes, flag all cases where document month > posting month"]
    )
    question_number: Optional[int] = Field(
        default=None,
        ge=1,
        description="Question number being answered (optional, for tracking)",
        examples=[1, 2, 3]
    )
    additional_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional additional notes or context",
        examples=["This should also consider quarter-end exceptions"]
    )

    @field_validator('answer')
    @classmethod
    def validate_answer(cls, v: str) -> str:
        """Validate answer is not empty."""
        if not v.strip():
            raise ValueError("Answer cannot be empty")
        return v.strip()


class PlanFeedbackRequest(BaseModel):
    """Request model for providing feedback on a business logic plan."""

    feedback: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Feedback on the business logic plan",
        examples=["Please add handling for quarter-end exceptions where posting happens in next quarter"]
    )
    action: str = Field(
        ...,
        pattern="^(refine|approve)$",
        description="Action to take: 'refine' to request changes, 'approve' to proceed to coding",
        examples=["refine", "approve"]
    )

    @field_validator('feedback')
    @classmethod
    def validate_feedback(cls, v: str) -> str:
        """Validate feedback is not empty."""
        if not v.strip():
            raise ValueError("Feedback cannot be empty")
        return v.strip()


class OutputFeedbackRequest(BaseModel):
    """Request model for providing feedback on generated output."""

    feedback: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Feedback on the generated output",
        examples=["Please add a column showing the number of days difference between dates"]
    )
    action: str = Field(
        ...,
        pattern="^(refine|approve)$",
        description="Action to take: 'refine' to request changes, 'approve' to complete workflow",
        examples=["refine", "approve"]
    )

    @field_validator('feedback')
    @classmethod
    def validate_feedback(cls, v: str) -> str:
        """Validate feedback is not empty."""
        if not v.strip():
            raise ValueError("Feedback cannot be empty")
        return v.strip()


class FeedbackOnlyRequest(BaseModel):
    """Simple request model that only requires feedback (for convenience endpoints)."""

    feedback: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Feedback text",
        examples=["Please add handling for edge cases"]
    )

    @field_validator('feedback')
    @classmethod
    def validate_feedback(cls, v: str) -> str:
        """Validate feedback is not empty."""
        if not v.strip():
            raise ValueError("Feedback cannot be empty")
        return v.strip()


class WorkflowFilterRequest(BaseModel):
    """Request model for filtering workflows."""

    phase: Optional[str] = Field(
        default=None,
        description="Filter by workflow phase",
        examples=["planning", "completed", "failed"]
    )
    status: Optional[str] = Field(
        default=None,
        description="Filter by workflow status",
        examples=["not_started", "planning", "completed"]
    )
    search: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Search query for workflow name or description",
        examples=["sales", "expense"]
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of workflows to return",
        examples=[10, 25, 50]
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of workflows to skip (pagination)",
        examples=[0, 10, 20]
    )


class AnalysisInstructionsApprovalRequest(BaseModel):
    """Request model for approving analysis instructions (optionally edited)."""

    instructions: Optional[str] = Field(
        default=None,
        description="User-edited instructions (if None, uses generated ones)",
        examples=["Include detailed breakdown by company code and plant..."]
    )

    @field_validator('instructions')
    @classmethod
    def validate_instructions(cls, v: Optional[str]) -> Optional[str]:
        """Validate instructions if provided."""
        if v is not None and not v.strip():
            raise ValueError("Instructions cannot be empty if provided")
        return v.strip() if v else None


class MakeWorkflowLiveRequest(BaseModel):
    """Request model for making a workflow live in production/staging."""

    business_process_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="ID of the business process this workflow belongs to",
        examples=["BP_001", "finance-audit-2024", "vendor-validation"]
    )
    mode: str = Field(
        ...,
        pattern="^(Staging|Production)$",
        description="Deployment environment: 'Staging' or 'Production'",
        examples=["Staging", "Production"]
    )
    check_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional custom check ID (if None, will be auto-generated)",
        examples=["MS_001", "FIN_AUDIT_001", "VEN_VAL_001"]
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Optional tags for categorizing the workflow",
        examples=[["VEN"], ["FIN", "AUDIT"], ["VENDOR", "VALIDATION"]]
    )

    @field_validator('business_process_id')
    @classmethod
    def validate_business_process_id(cls, v: str) -> str:
        """Validate business process ID is not empty."""
        if not v.strip():
            raise ValueError("Business process ID cannot be empty")
        return v.strip()

    @field_validator('check_id')
    @classmethod
    def validate_check_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate check ID if provided."""
        if v is not None and not v.strip():
            raise ValueError("Check ID cannot be empty if provided")
        return v.strip() if v else None
