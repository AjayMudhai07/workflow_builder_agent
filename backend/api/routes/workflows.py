"""
Workflow API routes.

This module defines all the API endpoints for workflow management.
"""

from typing import List
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse

from backend.api.models.requests import (
    AnswerSubmitRequest,
    PlanFeedbackRequest,
    OutputFeedbackRequest,
    FeedbackOnlyRequest,
    WorkflowFilterRequest,
    AnalysisInstructionsApprovalRequest,
    MakeWorkflowLiveRequest,
)
from backend.api.models.responses import (
    WorkflowCreateResponse,
    QuestionResponse,
    BusinessLogicPlanResponse,
    CodeGenerationResponse,
    OutputRefinementResponse,
    WorkflowCompletionResponse,
    AnalysisInstructionsResponse,
    AnalysisReportResponse,
    WorkflowListResponse,
    WorkflowDetailResponse,
    ErrorResponse,
    WorkflowPhaseEnum,
    ResponseTypeEnum,
    WorkflowListItem,
    MakeWorkflowLiveResponse,
)
from backend.api.services.workflow_manager import get_workflow_manager
from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.orchestrator import WorkflowPhase

logger = get_logger(__name__)

router = APIRouter()


@router.post("/workflows/create", response_model=WorkflowCreateResponse)
async def create_workflow(
    name: str = Form(..., min_length=3, max_length=200),
    description: str = Form(..., min_length=10, max_length=5000),
    files: List[UploadFile] = File(..., description="CSV files to upload"),
    output_filename: str = Form(default="result.csv", max_length=200),
):
    """
    Create a new workflow with uploaded CSV files.

    This endpoint:
    1. Validates and saves uploaded CSV files
    2. Creates a new workflow instance
    3. Returns the workflow ID and status

    Note: The workflow is created but not started. Call /workflows/{id}/start to begin.
    """
    try:
        # Validate files
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="At least one CSV file is required")

        # Validate file types
        for file in files:
            if not file.filename.endswith(('.csv', '.xlsx')):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file.filename}. Only .csv and .xlsx files are accepted"
                )

        # Save uploaded files temporarily with unique names to avoid collisions
        import uuid
        temp_files = []
        for file in files:
            # Add unique identifier to prevent filename collisions
            unique_id = str(uuid.uuid4())[:8]
            safe_filename = f"{unique_id}_{file.filename}"
            temp_path = Path(f"/tmp/{safe_filename}")
            with open(temp_path, "wb") as f:
                content = await file.read()
                f.write(content)
            temp_files.append(temp_path)

        logger.info(f"Received {len(files)} files for workflow: {name}")

        # Create workflow
        manager = get_workflow_manager()
        workflow_id, orchestrator = await manager.create_workflow(
            workflow_name=name,
            workflow_description=description,
            csv_files=temp_files,
            output_filename=output_filename
        )

        # Clean up temp files
        for temp_file in temp_files:
            temp_file.unlink()

        logger.info(f"Created workflow: {workflow_id}")

        return WorkflowCreateResponse(
            workflow_id=workflow_id,
            status="success",
            phase=WorkflowPhaseEnum(orchestrator.state.phase.value),
            message="Workflow created successfully",
            csv_files_count=len(files)
        )

    except HTTPException:
        # Clean up temp files on HTTP exceptions
        for temp_file in temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {cleanup_error}")
        raise
    except Exception as e:
        # Clean up temp files on any exception
        for temp_file in temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {cleanup_error}")
        logger.error(f"Error creating workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.post("/workflows/{workflow_id}/start", response_model=QuestionResponse)
async def start_workflow(workflow_id: str):
    """
    Start a workflow by initializing the planner agent.

    This endpoint:
    1. Initializes the planner agent
    2. Analyzes uploaded CSV files
    3. Returns the first question to the user
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        # Start the workflow
        result = await orchestrator.start()

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to start workflow"))

        return QuestionResponse(
            status="success",
            phase=WorkflowPhaseEnum(result["phase"]),
            response=result["response"],
            response_type=ResponseTypeEnum(result["response_type"]),
            question_number=1,
            total_questions=orchestrator.max_planner_questions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@router.post("/workflows/{workflow_id}/start-raa")
async def start_workflow_with_raa(workflow_id: str):
    """
    Start a workflow using RAA (Requirements Analysis Agent) flow - V2.

    This endpoint:
    1. Analyzes CSV files with DatasetAnalyzer (LLM-powered)
    2. Runs RAA for 3-dimensional requirements analysis
    3. If needed, routes to Intent Agent for question drafting
    4. Returns first question with understanding scores

    Returns:
        - question: User-friendly multiple-choice question (if next_agent == "intent_agent")
        - scores: Intent, Data, Business Logic understanding scores
        - next_agent: Which agent should handle next step
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        # Start with RAA flow
        result = await orchestrator.start_with_raa()

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to start workflow with RAA"))

        return {
            "status": "success",
            "phase": result["phase"],
            "next_agent": result.get("next_agent"),
            "question": result.get("question"),
            "scores": result.get("scores"),
            "message": result.get("message"),
            "next_action": result.get("next_action")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting workflow with RAA: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start workflow with RAA: {str(e)}")


@router.post("/workflows/{workflow_id}/answer-raa")
async def submit_answer_with_raa(workflow_id: str, request: AnswerSubmitRequest):
    """
    Submit an answer when using RAA flow - V2.

    This endpoint:
    1. Passes user's answer to RAA for processing
    2. RAA updates understanding and re-analyzes
    3. If more clarification needed, routes to Intent Agent
    4. Returns next question OR plan completion

    Returns:
        - question: Next question (if more clarification needed)
        - scores: Updated understanding scores
        - plan: Business logic plan (if requirements complete)
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        # Combine answer with additional notes if provided
        user_input = request.answer
        if request.additional_notes:
            user_input += f"\n\nAdditional notes: {request.additional_notes}"

        # Process with RAA flow
        result = await orchestrator.process_user_input_with_raa(user_input)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to process answer"))

        return {
            "status": "success",
            "phase": result["phase"],
            "next_agent": result.get("next_agent"),
            "next_action": result.get("next_action"),
            "question": result.get("question"),
            "plan": result.get("plan"),
            "scores": result.get("scores"),
            "message": result.get("message")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing answer with RAA: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process answer: {str(e)}")


@router.post("/workflows/{workflow_id}/answer", response_model=QuestionResponse)
async def submit_answer(workflow_id: str, request: AnswerSubmitRequest):
    """
    Submit an answer to a planner question.

    This endpoint:
    1. Processes the user's answer
    2. Returns the next question OR the business logic plan
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        # Combine answer with additional notes if provided
        user_input = request.answer
        if request.additional_notes:
            user_input += f"\n\nAdditional notes: {request.additional_notes}"

        # Process the answer
        result = await orchestrator.process_user_input(user_input)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to process answer"))

        return QuestionResponse(
            status="success",
            phase=WorkflowPhaseEnum(result["phase"]),
            response=result["response"],
            response_type=ResponseTypeEnum(result["response_type"]),
            question_number=result.get("questions_asked"),
            total_questions=orchestrator.max_planner_questions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting answer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@router.post("/workflows/{workflow_id}/request-plan", response_model=BusinessLogicPlanResponse)
async def request_plan(workflow_id: str):
    """
    Request the planner to generate the business logic plan.

    This endpoint can be called to force plan generation even if not all questions have been asked.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        # Request plan generation
        result = await orchestrator.request_plan_generation(force=True)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate plan"))

        return BusinessLogicPlanResponse(
            status="success",
            phase=WorkflowPhaseEnum(result["phase"]),
            business_logic_plan=result["business_logic_plan"],
            plan_approved=False
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting plan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to request plan: {str(e)}")


@router.post("/workflows/{workflow_id}/plan-feedback", response_model=BusinessLogicPlanResponse | CodeGenerationResponse)
async def submit_plan_feedback(workflow_id: str, request: PlanFeedbackRequest):
    """
    Submit feedback on the business logic plan.

    Actions:
    - 'refine': Request changes to the plan
    - 'approve': Approve the plan and proceed to code generation
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if orchestrator.state.phase != WorkflowPhase.PLAN_REVIEW:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase for plan feedback: {orchestrator.state.phase.value}"
            )

        if request.action == "refine":
            # Refine the plan based on feedback
            result = await orchestrator.refine_plan(request.feedback)

            if result["status"] == "error":
                raise HTTPException(status_code=500, detail=result.get("error", "Failed to refine plan"))

            return BusinessLogicPlanResponse(
                status="success",
                phase=WorkflowPhaseEnum.PLAN_REVIEW,
                business_logic_plan=result["business_logic_plan"],
                plan_approved=False
            )

        elif request.action == "approve":
            # Approve plan and start code generation
            result = await orchestrator.approve_plan_and_generate_code()

            if result["status"] == "error":
                raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate code"))

            return CodeGenerationResponse(
                status="success",
                phase=WorkflowPhaseEnum(result["phase"]),
                code=result.get("code"),
                code_filepath=result.get("code_filepath"),
                output_path=result.get("output_path"),
                output_preview=result.get("output_preview"),
                output_summary=result.get("output_summary"),
                iterations=result.get("iterations")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting plan feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit plan feedback: {str(e)}")


@router.post("/workflows/{workflow_id}/refine-plan", response_model=BusinessLogicPlanResponse)
async def refine_plan(workflow_id: str, request: FeedbackOnlyRequest):
    """
    Request changes to the business logic plan.

    This is a convenience endpoint that wraps plan-feedback with action='refine'.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if orchestrator.state.phase != WorkflowPhase.PLAN_REVIEW:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase for plan refinement: {orchestrator.state.phase.value}"
            )

        # Refine the plan based on feedback
        result = await orchestrator.refine_plan(request.feedback)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to refine plan"))

        return BusinessLogicPlanResponse(
            status="success",
            phase=WorkflowPhaseEnum.PLAN_REVIEW,
            business_logic_plan=result["business_logic_plan"],
            plan_approved=False
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refining plan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to refine plan: {str(e)}")


@router.post("/workflows/{workflow_id}/approve-plan", response_model=CodeGenerationResponse)
async def approve_plan(workflow_id: str):
    """
    Approve the business logic plan and proceed to code generation.

    This endpoint works for both:
    1. Initial plan approval (after planning phase)
    2. Updated plan approval (during output refinement)

    It intelligently determines whether to use the initial code generation flow
    or the code regeneration flow based on whether a Coder agent exists.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if orchestrator.state.phase != WorkflowPhase.PLAN_REVIEW:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase for plan approval: {orchestrator.state.phase.value}"
            )

        # Determine if this is a refinement (coder exists) or initial approval
        if orchestrator.coder and orchestrator.state.output_refinement_iterations > 0:
            # This is an updated plan approval during refinement - regenerate code
            result = await orchestrator.regenerate_code_from_updated_plan()
        else:
            # This is initial plan approval - generate code for the first time
            result = await orchestrator.approve_plan_and_generate_code()

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate code"))

        return CodeGenerationResponse(
            status="success",
            phase=WorkflowPhaseEnum(result["phase"]),
            code=result.get("code"),
            code_filepath=result.get("code_filepath"),
            output_path=result.get("output_path"),
            output_preview=result.get("output_preview"),
            output_summary=result.get("output_summary"),
            iterations=result.get("iterations")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving plan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve plan: {str(e)}")


@router.post("/workflows/{workflow_id}/output-feedback", response_model=OutputRefinementResponse | AnalysisInstructionsResponse)
async def submit_output_feedback(workflow_id: str, request: OutputFeedbackRequest):
    """
    Submit feedback on the generated output.

    Actions:
    - 'refine': Request changes to the output (updates plan, transitions to PLAN_REVIEW)
    - 'approve': Approve the output and proceed to analysis report generation
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if orchestrator.state.phase != WorkflowPhase.OUTPUT_REVIEW:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase for output feedback: {orchestrator.state.phase.value}"
            )

        if request.action == "refine":
            # Refine the output based on feedback (new plan-first approach)
            result = await orchestrator.refine_output(request.feedback)

            if result["status"] == "error":
                raise HTTPException(status_code=500, detail=result.get("error", "Failed to refine output"))

            return OutputRefinementResponse(
                status="success",
                phase=WorkflowPhaseEnum(result["phase"]),
                updated_plan=result.get("updated_plan"),
                message=result.get("message"),
                refinement_iteration=result["refinement_iteration"]
            )

        elif request.action == "approve":
            # Approve output and generate analysis instructions
            result = await orchestrator.approve_output_and_continue()

            if result["status"] == "error":
                raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate analysis instructions"))

            return AnalysisInstructionsResponse(
                status="success",
                phase=WorkflowPhaseEnum(result["phase"]),
                instructions=result["instructions"]
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting output feedback: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit output feedback: {str(e)}")


@router.post("/workflows/{workflow_id}/refine-output", response_model=OutputRefinementResponse)
async def refine_output(workflow_id: str, request: FeedbackOnlyRequest):
    """
    Request changes to the generated output using the new plan-first approach.

    This endpoint:
    1. Updates the Business Logic Plan based on user feedback
    2. Transitions to PLAN_REVIEW phase
    3. Returns the updated plan for user review

    After reviewing, the user must approve the updated plan to regenerate code.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if orchestrator.state.phase != WorkflowPhase.OUTPUT_REVIEW:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase for output refinement: {orchestrator.state.phase.value}"
            )

        # Refine the output based on feedback (updates plan and transitions to PLAN_REVIEW)
        result = await orchestrator.refine_output(request.feedback)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to refine output"))

        return OutputRefinementResponse(
            status="success",
            phase=WorkflowPhaseEnum(result["phase"]),
            updated_plan=result.get("updated_plan"),
            message=result.get("message"),
            refinement_iteration=result["refinement_iteration"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refining output: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to refine output: {str(e)}")


@router.post("/workflows/{workflow_id}/approve-output", response_model=AnalysisInstructionsResponse)
async def approve_output(workflow_id: str):
    """
    Approve the generated output and proceed to analysis report generation.

    This automatically generates analysis instructions for the user to review/edit.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if orchestrator.state.phase != WorkflowPhase.OUTPUT_REVIEW:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase for output approval: {orchestrator.state.phase.value}"
            )

        # Approve output and generate analysis instructions
        result = await orchestrator.approve_output_and_continue()

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate analysis instructions"))

        return AnalysisInstructionsResponse(
            status="success",
            phase=WorkflowPhaseEnum(result["phase"]),
            instructions=result["instructions"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving output: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve output: {str(e)}")


# =============================================================================
# ANALYSIS REPORT GENERATION ENDPOINTS
# =============================================================================

@router.post("/workflows/{workflow_id}/approve-analysis-instructions", response_model=AnalysisReportResponse)
async def approve_analysis_instructions(workflow_id: str, request: AnalysisInstructionsApprovalRequest):
    """
    Approve analysis instructions (optionally edited by user) and generate analysis report.

    This generates the analysis plan, code, and .txt report file.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if orchestrator.state.phase != WorkflowPhase.ANALYSIS_REPORT_GENERATION:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase for approving analysis instructions: {orchestrator.state.phase.value}"
            )

        # Approve instructions and generate report
        result = await orchestrator.approve_analysis_instructions(
            edited_instructions=request.instructions
        )

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate analysis report"))

        return AnalysisReportResponse(
            status="success",
            phase=WorkflowPhaseEnum(result["phase"]),
            analysis_plan=result.get("analysis_plan"),
            code=result.get("code"),
            report_file_path=result.get("report_file_path"),
            report_content=result["report_content"],
            iterations=result.get("iterations")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving analysis instructions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve analysis instructions: {str(e)}")


@router.post("/workflows/{workflow_id}/approve-analysis-report", response_model=WorkflowCompletionResponse)
async def approve_analysis_report(workflow_id: str):
    """
    Approve the analysis report and complete the workflow.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if orchestrator.state.phase != WorkflowPhase.ANALYSIS_REPORT_REVIEW:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase for approving analysis report: {orchestrator.state.phase.value}"
            )

        # Approve report and complete workflow
        result = await orchestrator.approve_analysis_report()

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to complete workflow"))

        return WorkflowCompletionResponse(
            status="success",
            phase=WorkflowPhaseEnum.COMPLETED,
            output_path=result["output_path"],
            execution_time=result["execution_time"],
            is_successful=result["is_successful"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving analysis report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to approve analysis report: {str(e)}")


@router.post("/workflows/{workflow_id}/refine-analysis-report", response_model=AnalysisReportResponse)
async def refine_analysis_report(workflow_id: str, request: FeedbackOnlyRequest):
    """
    Refine the analysis report based on user feedback.

    Regenerates the analysis code and creates a new report incorporating the feedback.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if orchestrator.state.phase != WorkflowPhase.ANALYSIS_REPORT_REVIEW:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid phase for refining analysis report: {orchestrator.state.phase.value}"
            )

        # Refine the analysis report
        result = await orchestrator.refine_analysis_report(request.feedback)

        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to refine analysis report"))

        return AnalysisReportResponse(
            status="success",
            phase=WorkflowPhaseEnum(result["phase"]),
            code=result.get("code"),
            report_file_path=result.get("report_file_path"),
            report_content=result["report_content"],
            refinement_iteration=result.get("refinement_iteration")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refining analysis report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to refine analysis report: {str(e)}")


@router.get("/workflows/{workflow_id}/analysis-report")
async def get_analysis_report(workflow_id: str):
    """
    Get the current analysis report content.

    Returns the .txt report file content if available.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if not orchestrator.state.analysis_report_content:
            raise HTTPException(status_code=404, detail="Analysis report not yet generated")

        return {
            "status": "success",
            "report_content": orchestrator.state.analysis_report_content,
            "report_file_path": orchestrator.state.analysis_report_file_path,
            "phase": orchestrator.state.phase.value
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis report: {str(e)}")


@router.get("/workflows/{workflow_id}/download-analysis-report")
async def download_analysis_report(workflow_id: str):
    """
    Download the analysis report as a .txt file.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if not orchestrator.state.analysis_report_file_path:
            raise HTTPException(status_code=404, detail="Analysis report file not found")

        report_file = Path(orchestrator.state.analysis_report_file_path)

        if not report_file.exists():
            raise HTTPException(status_code=404, detail="Analysis report file not found on disk")

        return FileResponse(
            path=str(report_file),
            media_type="text/plain",
            filename=report_file.name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading analysis report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download analysis report: {str(e)}")


@router.get("/workflows", response_model=WorkflowListResponse)
async def list_workflows(
    phase: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List all workflows with optional filtering.

    Query Parameters:
    - phase: Filter by workflow phase (optional)
    - limit: Maximum number of workflows to return (default: 50, max: 100)
    - offset: Number of workflows to skip for pagination (default: 0)
    """
    try:
        if limit > 100:
            limit = 100

        manager = get_workflow_manager()
        workflows_data = await manager.list_workflows(phase=phase, limit=limit, offset=offset)

        # Convert to WorkflowListItem models
        workflows = [
            WorkflowListItem(
                workflow_id=w["workflow_id"],
                name=w["name"],
                description=w["description"],
                phase=WorkflowPhaseEnum(w["phase"]),
                created_at=w["created_at"],
                updated_at=w["updated_at"],
                csv_files_count=w["csv_files_count"],
                is_successful=w.get("is_successful", False),
                error_message=w.get("error_message")
            )
            for w in workflows_data
        ]

        return WorkflowListResponse(
            status="success",
            workflows=workflows,
            total=len(workflows),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")


@router.get("/workflows/{workflow_id}", response_model=WorkflowDetailResponse)
async def get_workflow_detail(workflow_id: str):
    """
    Get detailed information about a specific workflow.
    """
    try:
        manager = get_workflow_manager()
        detail = await manager.get_workflow_detail(workflow_id)

        if not detail:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        # Get understanding scores from orchestrator if available
        orchestrator = await manager.get_orchestrator(workflow_id)
        understanding_scores = None
        if orchestrator and detail["phase"] == "planning":
            understanding_scores = {
                "intent_understanding": orchestrator.state.intent_understanding_score,
                "data_understanding": orchestrator.state.data_understanding_score,
                "business_logic_understanding": orchestrator.state.business_logic_understanding_score,
                "overall_completeness": orchestrator.state.overall_completeness
            }

        return WorkflowDetailResponse(
            workflow_id=workflow_id,
            workflow_name=detail["workflow_name"],
            workflow_description=detail["workflow_description"],
            phase=WorkflowPhaseEnum(detail["phase"]),
            started_at=detail.get("started_at"),
            completed_at=detail.get("completed_at"),
            csv_filepaths=detail.get("planner_summary", {}).get("csv_files", []),
            planner_questions_asked=detail.get("planner_summary", {}).get("questions_asked", 0),
            current_question=detail.get("current_question"),
            understanding_scores=understanding_scores,
            business_logic_plan=detail.get("planner_summary", {}).get("business_logic_plan"),
            plan_approved=detail.get("planner_summary", {}).get("plan_approved", False),
            generated_code=detail.get("coder_summary", {}).get("generated_code"),
            code_execution_iterations=detail.get("coder_summary", {}).get("iterations", 0),
            output_file_path=detail.get("coder_summary", {}).get("output_path"),
            output_approved=detail.get("output_review_summary", {}).get("output_approved", False),
            output_refinement_iterations=detail.get("output_review_summary", {}).get("refinement_iterations", 0),
            analysis_instructions=detail.get("analysis_instructions"),
            analysis_instructions_approved=detail.get("analysis_instructions_approved", False),
            analysis_plan=detail.get("analysis_plan"),
            analysis_code=detail.get("analysis_code"),
            analysis_report_file_path=detail.get("analysis_report_file_path"),
            analysis_report_content=detail.get("analysis_report_content"),
            analysis_report_approved=detail.get("analysis_report_approved", False),
            analysis_refinement_iterations=detail.get("analysis_refinement_iterations", 0),
            error_message=detail.get("error_message"),
            is_successful=detail.get("is_successful", False)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get workflow detail: {str(e)}")


@router.get("/workflows/{workflow_id}/plan", response_model=BusinessLogicPlanResponse)
async def get_plan(workflow_id: str):
    """
    Get the business logic plan for a workflow.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        # Check if plan exists
        plan = orchestrator.state.business_logic_plan

        if not plan:
            raise HTTPException(status_code=404, detail="Business logic plan not generated yet")

        return BusinessLogicPlanResponse(
            status="success",
            phase=WorkflowPhaseEnum(orchestrator.state.phase.value),
            business_logic_plan=plan,
            plan_approved=orchestrator.state.plan_approved
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plan: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get plan: {str(e)}")


@router.get("/workflows/{workflow_id}/output/preview")
async def get_output_preview(workflow_id: str, rows: int = 10):
    """
    Get a preview of the generated output CSV.
    """
    try:
        import pandas as pd
        import numpy as np

        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if not orchestrator.state.output_file_path:
            raise HTTPException(status_code=404, detail="Output file not generated yet")

        output_path = Path(orchestrator.state.output_file_path)

        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Output file not found")

        # Read the CSV file
        df = pd.read_csv(output_path, nrows=rows)

        # Replace NaN values with None (which becomes null in JSON)
        df = df.replace({np.nan: None})

        # Get total row count
        total_rows = sum(1 for _ in open(output_path)) - 1  # Subtract header

        # Convert to response format
        preview_data = {
            "columns": df.columns.tolist(),
            "rows": df.to_dict(orient="records"),
            "total_rows": total_rows
        }

        return preview_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting output preview: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get output preview: {str(e)}")


@router.get("/workflows/{workflow_id}/download-output")
async def download_output(workflow_id: str):
    """
    Download the generated output CSV file.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if not orchestrator.state.output_file_path:
            raise HTTPException(status_code=404, detail="Output file not generated yet")

        output_path = Path(orchestrator.state.output_file_path)

        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Output file not found")

        return FileResponse(
            path=str(output_path),
            media_type="text/csv",
            filename=output_path.name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading output: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download output: {str(e)}")


@router.get("/workflows/{workflow_id}/download-code")
async def download_code(workflow_id: str):
    """
    Download the generated Python code.
    """
    try:
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        if not orchestrator.state.generated_code:
            raise HTTPException(status_code=404, detail="Code not generated yet")

        # Find the most recent code file for this workflow
        from ai.ira_builder.orchestrator import sanitize_filename
        safe_name = sanitize_filename(orchestrator.workflow_name)
        code_dir = Path("./storage/generated_code")
        code_files = list(code_dir.glob(f"{safe_name}_*.py"))

        if not code_files:
            raise HTTPException(status_code=404, detail="Code file not found")

        # Get the most recent file
        code_file = max(code_files, key=lambda p: p.stat().st_mtime)

        return FileResponse(
            path=str(code_file),
            media_type="text/x-python",
            filename=code_file.name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading code: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to download code: {str(e)}")


@router.post("/workflows/{workflow_id}/make-live", response_model=MakeWorkflowLiveResponse)
async def make_workflow_live(workflow_id: str, request: MakeWorkflowLiveRequest):
    """
    Make a workflow live in production/staging environment.

    This endpoint:
    1. Validates workflow is in correct phase (analysis_report_review)
    2. Generates workflow configuration using LLM
    3. Deploys to specified environment (Staging/Production)
    4. Updates workflow state to LIVE phase
    """
    try:
        from backend.api.services.production_api_client import get_production_api_client
        from ai.ira_builder.utils.workflow_config_generator import (
            generate_workflow_config,
            validate_workflow_config
        )
        from ai.ira_builder.orchestrator import sanitize_filename
        from datetime import datetime

        # Get workflow manager and orchestrator
        manager = get_workflow_manager()
        orchestrator = await manager.get_orchestrator(workflow_id)

        if not orchestrator:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Validate workflow is in correct phase
        # Allow both analysis_report_review and completed phases (in case user already approved without going live)
        valid_phases = [WorkflowPhase.ANALYSIS_REPORT_REVIEW, WorkflowPhase.COMPLETED]
        if orchestrator.state.phase not in valid_phases:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow must be in analysis_report_review or completed phase to make it live. Current phase: {orchestrator.state.phase.value}"
            )

        # Auto-approve analysis report if not already approved
        # This allows users to go directly from analysis report review to Live phase
        if not orchestrator.state.analysis_report_approved:
            logger.info("Analysis report not yet approved - auto-approving for Live deployment")
            orchestrator.state.analysis_report_approved = True

        logger.info(f"================================================================================")
        logger.info(f"MAKING WORKFLOW LIVE")
        logger.info(f"================================================================================")
        logger.info(f"Workflow: {orchestrator.workflow_name}")
        logger.info(f"Mode: {request.mode}")
        logger.info(f"Business Process ID: {request.business_process_id}")

        # Generate check_id if not provided
        check_id = request.check_id
        if not check_id:
            # Auto-generate check_id from workflow name
            check_id = sanitize_filename(orchestrator.workflow_name)[:20].upper()
            check_id = f"{check_id}_{datetime.now().strftime('%Y%m%d')}"
            logger.info(f"Auto-generated Check ID: {check_id}")

        # Generate workflow config using LLM
        logger.info(f"🔧 Generating workflow configuration...")

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
            logger.info(f"Added tags: {request.tags}")

        # Validate config
        logger.info("✓ Validating workflow configuration...")
        await validate_workflow_config(workflow_config)
        logger.info("✓ Workflow configuration validated")

        # Deploy to production/staging
        logger.info(f"🚀 Deploying workflow to {request.mode}...")

        prod_client = get_production_api_client(mode=request.mode)
        deployment_status = prod_client.make_workflow_live(
            workflow_config=workflow_config,
            business_process_id=request.business_process_id
        )

        if deployment_status != 200:
            logger.error(f"❌ Deployment failed with status code: {deployment_status}")
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

        logger.info(f"✅ WORKFLOW SUCCESSFULLY DEPLOYED TO {request.mode}")
        logger.info(f"   - Check ID: {check_id}")
        logger.info(f"   - Business Process ID: {request.business_process_id}")
        logger.info(f"   - Status Code: {deployment_status}")
        logger.info(f"================================================================================")

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


@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """
    Delete a workflow and all associated files.
    """
    try:
        manager = get_workflow_manager()
        success = await manager.delete_workflow(workflow_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")

        return {"status": "success", "message": f"Workflow {workflow_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")
