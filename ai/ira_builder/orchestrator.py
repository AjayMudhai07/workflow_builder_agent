"""
IRA Workflow Builder Orchestrator

This module orchestrates the complete workflow from planning to code generation:
1. Planner Agent: Gathers requirements through interview
2. Coder Agent: Generates and executes production code
3. State Management: Persists workflow state and results
"""

import json
import asyncio
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from datetime import datetime

from ai.ira_builder.agents.planner import (
    create_planner_agent,
    PlannerAgent,
    PlannerResponseType
)
from ai.ira_builder.agents.coder import create_coder_agent, CoderAgent
from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.utils.config import get_config
from ai.ira_builder.utils.file_analyzer import analyze_dataset

logger = get_logger(__name__)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.

    Removes or replaces characters that are invalid in file paths.

    Args:
        name: The original name string

    Returns:
        Sanitized filename-safe string
    """
    import re
    # Replace invalid characters with underscores
    # Invalid characters: / \ : * ? " < > |
    sanitized = re.sub(r'[/\\:*?"<>|]', '_', name)
    # Replace multiple underscores with single underscore
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Limit length to 200 characters
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized


# =============================================================================
# WORKFLOW STATES
# =============================================================================

class WorkflowPhase(str, Enum):
    """Workflow execution phases."""
    NOT_STARTED = "not_started"
    PLANNING = "planning"
    PLAN_REVIEW = "plan_review"
    CODING = "coding"
    OUTPUT_REVIEW = "output_review"
    ANALYSIS_REPORT_GENERATION = "analysis_report_generation"
    ANALYSIS_REPORT_REVIEW = "analysis_report_review"
    LIVE = "live"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowState:
    """
    Maintains the complete state of a workflow execution.

    This class tracks:
    - Current execution phase
    - Planner agent conversation history
    - Generated business logic plan
    - Coder agent execution results
    - Generated code and output files
    """

    def __init__(self, workflow_name: str, workflow_description: str, csv_filepaths: List[str]):
        """Initialize workflow state."""
        self.workflow_name = workflow_name
        self.workflow_description = workflow_description
        self.csv_filepaths = csv_filepaths

        # Phase tracking
        self.phase = WorkflowPhase.NOT_STARTED
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        # Planner phase
        self.planner_questions_asked = 0
        self.planner_conversation_history: List[Dict[str, str]] = []
        self.current_question: Optional[str] = None
        self.business_logic_plan: Optional[str] = None
        self.plan_approved = False

        # Coder phase
        self.generated_code: Optional[str] = None
        self.code_execution_iterations = 0
        self.code_execution_result: Optional[Dict[str, Any]] = None
        self.output_file_path: Optional[str] = None

        # Output review phase
        self.output_approved = False
        self.output_feedback_history: List[Dict[str, str]] = []
        self.output_refinement_iterations = 0
        self.cumulative_refinement_requirements: List[str] = []  # Track all refinement requirements

        # Analysis report generation phase
        self.analysis_instructions: Optional[str] = None
        self.analysis_instructions_approved = False
        self.analysis_plan: Optional[str] = None
        self.analysis_code: Optional[str] = None
        self.analysis_report_file_path: Optional[str] = None
        self.analysis_report_content: Optional[str] = None
        self.analysis_report_approved = False
        self.analysis_refinement_iterations = 0
        self.analysis_feedback_history: List[Dict[str, str]] = []

        # File analysis (populated before planning)
        self.file_analysis_results: Optional[Dict[str, Any]] = None
        self.dataset_description: Optional[str] = None

        # Live phase (deployment to production/staging)
        self.workflow_config: Optional[Dict[str, Any]] = None
        self.business_process_id: Optional[str] = None
        self.deployment_mode: Optional[str] = None  # "Staging" or "Production"
        self.deployment_status: Optional[int] = None  # HTTP status code from deployment
        self.check_id: Optional[str] = None  # Unique check ID generated for this workflow
        self.is_live = False

        # Status
        self.error_message: Optional[str] = None
        self.is_successful = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "workflow_name": self.workflow_name,
            "workflow_description": self.workflow_description,
            "csv_filepaths": self.csv_filepaths,
            "phase": self.phase.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "planner_questions_asked": self.planner_questions_asked,
            "current_question": self.current_question,
            "business_logic_plan": self.business_logic_plan,
            "plan_approved": self.plan_approved,
            "generated_code": self.generated_code,
            "code_execution_iterations": self.code_execution_iterations,
            "output_file_path": self.output_file_path,
            "output_approved": self.output_approved,
            "output_refinement_iterations": self.output_refinement_iterations,
            "cumulative_refinement_requirements": self.cumulative_refinement_requirements,
            "analysis_instructions": self.analysis_instructions,
            "analysis_instructions_approved": self.analysis_instructions_approved,
            "analysis_plan": self.analysis_plan,
            "analysis_code": self.analysis_code,
            "analysis_report_file_path": self.analysis_report_file_path,
            "analysis_report_content": self.analysis_report_content,
            "analysis_report_approved": self.analysis_report_approved,
            "analysis_refinement_iterations": self.analysis_refinement_iterations,
            "file_analysis_results": self.file_analysis_results,
            "dataset_description": self.dataset_description,
            "workflow_config": self.workflow_config,
            "business_process_id": self.business_process_id,
            "deployment_mode": self.deployment_mode,
            "deployment_status": self.deployment_status,
            "check_id": self.check_id,
            "is_live": self.is_live,
            "error_message": self.error_message,
            "is_successful": self.is_successful,
        }

    def save_to_file(self, filepath: str):
        """Save state to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved workflow state to {filepath}")

    @classmethod
    def load_from_file(cls, filepath: str) -> 'WorkflowState':
        """Load state from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        state = cls(
            workflow_name=data["workflow_name"],
            workflow_description=data["workflow_description"],
            csv_filepaths=data["csv_filepaths"]
        )

        state.phase = WorkflowPhase(data["phase"])
        state.started_at = datetime.fromisoformat(data["started_at"]) if data["started_at"] else None
        state.completed_at = datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None
        state.planner_questions_asked = data["planner_questions_asked"]
        state.current_question = data.get("current_question")
        state.business_logic_plan = data.get("business_logic_plan")
        state.plan_approved = data.get("plan_approved", False)
        state.generated_code = data.get("generated_code")
        state.code_execution_iterations = data.get("code_execution_iterations", 0)
        state.output_file_path = data.get("output_file_path")
        state.output_approved = data.get("output_approved", False)
        state.output_refinement_iterations = data.get("output_refinement_iterations", 0)
        state.cumulative_refinement_requirements = data.get("cumulative_refinement_requirements", [])
        state.analysis_instructions = data.get("analysis_instructions")
        state.analysis_instructions_approved = data.get("analysis_instructions_approved", False)
        state.analysis_plan = data.get("analysis_plan")
        state.analysis_code = data.get("analysis_code")
        state.analysis_report_file_path = data.get("analysis_report_file_path")
        state.analysis_report_content = data.get("analysis_report_content")
        state.analysis_report_approved = data.get("analysis_report_approved", False)
        state.analysis_refinement_iterations = data.get("analysis_refinement_iterations", 0)
        state.file_analysis_results = data.get("file_analysis_results")
        state.dataset_description = data.get("dataset_description")
        state.error_message = data.get("error_message")
        state.is_successful = data.get("is_successful", False)

        logger.info(f"Loaded workflow state from {filepath}")
        return state


# =============================================================================
# ORCHESTRATOR
# =============================================================================

class IRAOrchestrator:
    """
    Orchestrates the complete IRA Workflow Builder pipeline.

    This class:
    1. Manages Planner Agent for requirements gathering
    2. Manages Coder Agent for code generation and execution
    3. Handles state transitions between planning and coding phases
    4. Persists workflow state and results
    5. Provides callbacks for UI integration

    Example:
        >>> orchestrator = IRAOrchestrator(
        ...     workflow_name="Sales Analysis",
        ...     workflow_description="Analyze Q4 sales data",
        ...     csv_filepaths=["data/sales.csv"]
        ... )
        >>> await orchestrator.start()
        >>> response = await orchestrator.process_user_input("Option A")
        >>> if orchestrator.is_plan_ready():
        ...     await orchestrator.approve_plan()
        ...     result = await orchestrator.execute_code_generation()
    """

    def __init__(
        self,
        workflow_name: str,
        workflow_description: str,
        csv_filepaths: List[str],
        output_filename: str = "result.csv",
        workflow_id: Optional[str] = None,
        model: Optional[str] = None,
        max_planner_questions: int = 10,
        max_coder_iterations: int = 5,
        code_execution_timeout: int = 120,
        state_persistence_dir: Optional[str] = None,
        on_phase_change: Optional[Callable[[WorkflowPhase], None]] = None,
        on_planner_response: Optional[Callable[[str, PlannerResponseType], None]] = None,
        on_coder_progress: Optional[Callable[[int, int], None]] = None
    ):
        """
        Initialize the IRA Orchestrator.

        Args:
            workflow_name: Name of the workflow
            workflow_description: Description of what workflow should accomplish
            csv_filepaths: List of absolute paths to CSV files
            output_filename: Name for output file (default: result.csv)
            workflow_id: Unique identifier for the workflow (optional, defaults to sanitized workflow_name)
            model: Model to use (or None to use provider default from config)
            max_planner_questions: Maximum questions Planner can ask
            max_coder_iterations: Maximum code generation attempts
            code_execution_timeout: Timeout for code execution in seconds
            state_persistence_dir: Directory to save state (default: ./storage/workflows)
            on_phase_change: Callback when workflow phase changes
            on_planner_response: Callback for Planner agent responses
            on_coder_progress: Callback for Coder agent progress updates
        """
        self.workflow_name = workflow_name
        self.workflow_description = workflow_description
        self.csv_filepaths = csv_filepaths
        self.output_filename = output_filename
        self.model = model  # Can be None - will use provider default

        # State management
        self.state = WorkflowState(workflow_name, workflow_description, csv_filepaths)

        # State persistence
        if state_persistence_dir:
            self.state_dir = Path(state_persistence_dir)
        else:
            self.state_dir = Path("./storage/workflows")

        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Use workflow_id for state file path, or fall back to sanitized workflow_name
        if workflow_id:
            safe_workflow_id = sanitize_filename(workflow_id)
        else:
            safe_workflow_id = sanitize_filename(workflow_name)
        self.state_file_path = self.state_dir / f"{safe_workflow_id}_state.json"

        # Callbacks for UI integration
        self.on_phase_change = on_phase_change
        self.on_planner_response = on_planner_response
        self.on_coder_progress = on_coder_progress

        # Agents (initialized later)
        self.planner: Optional[PlannerAgent] = None
        self.coder: Optional[CoderAgent] = None

        # Agent configuration
        self.max_planner_questions = max_planner_questions
        self.max_coder_iterations = max_coder_iterations
        self.code_execution_timeout = code_execution_timeout

        logger.info(f"Orchestrator initialized for workflow: {workflow_name}")

    async def analyze_uploaded_files(self) -> Dict[str, Any]:
        """
        Analyze uploaded CSV files using LLM to generate:
        1. Column descriptions for each column in each file
        2. File description for each file
        3. Overall dataset description

        This analysis provides rich context to the Planner agent.

        Returns:
            Dictionary with status and analysis results
        """
        try:
            logger.info("=" * 80)
            logger.info("ANALYZING UPLOADED FILES")
            logger.info("=" * 80)
            logger.info(f"Files to analyze: {len(self.csv_filepaths)}")

            # Run file analysis using LLM (Groq for speed)
            analysis_result = await analyze_dataset(self.csv_filepaths)

            # Store results in state
            self.state.file_analysis_results = analysis_result
            self.state.dataset_description = analysis_result.get("dataset_description")

            # Persist state
            self._persist_state()

            logger.info("✅ File analysis completed successfully")
            logger.info(f"   - Total files analyzed: {analysis_result.get('total_files', 0)}")
            logger.info(f"   - Total columns: {analysis_result.get('total_columns', 0)}")
            logger.info(f"   - Total rows: {analysis_result.get('total_rows', 0)}")
            logger.info(f"   - Dataset description: {self.state.dataset_description[:100]}...")

            return {
                "status": "success",
                "analysis_result": analysis_result
            }

        except Exception as e:
            logger.error(f"Error analyzing files: {str(e)}", exc_info=True)
            # Don't fail the workflow - continue without file analysis
            return {
                "status": "error",
                "error": str(e)
            }

    async def start(self) -> Dict[str, Any]:
        """
        Start the workflow by initializing the Planner Agent.

        This begins the planning phase where the Planner asks questions
        to understand business requirements.

        Returns:
            Dictionary with initial planner response
        """
        logger.info("=" * 80)
        logger.info(f"STARTING WORKFLOW: {self.workflow_name}")
        logger.info("=" * 80)

        self.state.started_at = datetime.now()
        self._change_phase(WorkflowPhase.PLANNING)

        try:
            # Step 1: Analyze uploaded files to provide context to Planner
            logger.info("Step 1: Analyzing uploaded CSV files...")
            await self.analyze_uploaded_files()

            # Step 2: Create Planner Agent (using phase-specific provider)
            logger.info("Step 2: Creating Planner Agent...")
            config = get_config()
            self.planner = create_planner_agent(
                model=self.model,
                temperature=0.7,
                max_questions=self.max_planner_questions,
                provider=config.planner_provider
            )
            logger.info(f"Planner Agent created with provider: {config.planner_provider}")

            # Step 3: Inject file analysis into Planner's memory (if available)
            if self.state.file_analysis_results:
                logger.info("Step 3: Injecting file analysis into Planner memory...")
                self.planner.csv_memory.set_file_analysis(self.state.file_analysis_results)
                logger.info("✅ File analysis injected into Planner context")

            logger.info("Initializing Planner Agent...")

            # Initialize workflow with Planner
            response = await self.planner.initialize_workflow(
                workflow_name=self.workflow_name,
                workflow_description=self.workflow_description,
                csv_filepaths=self.csv_filepaths
            )

            # Update state
            self.state.planner_conversation_history.append({
                "role": "assistant",
                "content": str(response),
                "timestamp": datetime.now().isoformat()
            })
            self.state.current_question = str(response)

            # Detect response type
            response_type = self.planner._detect_response_type(str(response))

            # Trigger callbacks
            if self.on_planner_response:
                self.on_planner_response(str(response), response_type)

            # Persist state
            self._persist_state()

            logger.info("Planning phase started successfully")

            return {
                "status": "success",
                "phase": self.state.phase.value,
                "response": str(response),
                "response_type": response_type.value
            }

        except Exception as e:
            logger.error(f"Error starting workflow: {str(e)}", exc_info=True)
            self.state.error_message = str(e)
            self._change_phase(WorkflowPhase.FAILED)
            self._persist_state()

            return {
                "status": "error",
                "phase": self.state.phase.value,
                "error": str(e)
            }

    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user's response during planning phase.

        Args:
            user_input: User's answer to Planner's question

        Returns:
            Dictionary with next question or business logic plan
        """
        if self.state.phase != WorkflowPhase.PLANNING and self.state.phase != WorkflowPhase.PLAN_REVIEW:
            return {
                "status": "error",
                "error": f"Cannot process user input in phase: {self.state.phase.value}"
            }

        if not self.planner:
            return {
                "status": "error",
                "error": "Planner not initialized. Call start() first."
            }

        try:
            logger.info(f"Processing user input: {user_input[:100]}...")

            # Record user input
            self.state.planner_conversation_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now().isoformat()
            })
            self.state.planner_questions_asked += 1

            # Get response from Planner (could be next question or "GENERATE_PLAN" signal)
            response = await self.planner.ask_question(user_input)

            # Convert response to string for checking
            response_str = str(response).strip()

            # Check if Planner is signaling to generate plan
            if response_str == "GENERATE_PLAN":
                logger.info("Planner signaled GENERATE_PLAN - calling generate_business_logic()")

                # Call the specialized method to generate the actual plan
                plan_response = await self.planner.generate_business_logic(force=False)

                # Record the plan generation in history
                self.state.planner_conversation_history.append({
                    "role": "assistant",
                    "content": str(plan_response),
                    "timestamp": datetime.now().isoformat(),
                    "is_business_logic_plan": True
                })

                # Store the business logic plan
                self.state.business_logic_plan = str(plan_response)
                self.state.current_question = None  # No more questions
                self._change_phase(WorkflowPhase.PLAN_REVIEW)

                response_type = PlannerResponseType.BUSINESS_LOGIC_PLAN
                response = plan_response  # Replace signal with actual plan
            else:
                # Record normal Planner response
                self.state.planner_conversation_history.append({
                    "role": "assistant",
                    "content": response_str,
                    "timestamp": datetime.now().isoformat()
                })

                # Detect response type
                response_type = self.planner._detect_response_type(response_str)

                # Store the next question
                self.state.current_question = response_str

            # Trigger callbacks
            if self.on_planner_response:
                self.on_planner_response(str(response), response_type)

            # Persist state
            self._persist_state()

            return {
                "status": "success",
                "phase": self.state.phase.value,
                "response": str(response),
                "response_type": response_type.value,
                "questions_asked": self.state.planner_questions_asked
            }

        except Exception as e:
            logger.error(f"Error processing user input: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def request_plan_generation(self, force: bool = False) -> Dict[str, Any]:
        """
        Request Planner to generate Business Logic Plan.

        Args:
            force: Force generation even if not all questions asked

        Returns:
            Dictionary with business logic plan
        """
        if not self.planner:
            return {
                "status": "error",
                "error": "Planner not initialized"
            }

        try:
            logger.info("Requesting business logic plan generation...")

            response = await self.planner.generate_business_logic(force=force)

            self.state.business_logic_plan = str(response)
            self._change_phase(WorkflowPhase.PLAN_REVIEW)

            # Record in history
            self.state.planner_conversation_history.append({
                "role": "assistant",
                "content": str(response),
                "timestamp": datetime.now().isoformat(),
                "is_business_logic_plan": True
            })

            # Trigger callbacks
            if self.on_planner_response:
                self.on_planner_response(str(response), PlannerResponseType.BUSINESS_LOGIC_PLAN)

            self._persist_state()

            return {
                "status": "success",
                "phase": self.state.phase.value,
                "business_logic_plan": str(response)
            }

        except Exception as e:
            logger.error(f"Error generating plan: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def refine_plan(self, feedback: str) -> Dict[str, Any]:
        """
        Refine business logic plan based on user feedback.

        Args:
            feedback: User's feedback on the plan

        Returns:
            Dictionary with refined plan
        """
        if self.state.phase != WorkflowPhase.PLAN_REVIEW:
            return {
                "status": "error",
                "error": "Can only refine plan in PLAN_REVIEW phase"
            }

        if not self.planner:
            return {
                "status": "error",
                "error": "Planner not initialized"
            }

        try:
            logger.info("Refining business logic plan...")

            response = await self.planner.refine_business_logic(feedback)

            self.state.business_logic_plan = str(response)

            # Record in history
            self.state.planner_conversation_history.append({
                "role": "user",
                "content": f"[Feedback on plan] {feedback}",
                "timestamp": datetime.now().isoformat()
            })
            self.state.planner_conversation_history.append({
                "role": "assistant",
                "content": str(response),
                "timestamp": datetime.now().isoformat(),
                "is_refined_plan": True
            })

            self._persist_state()

            return {
                "status": "success",
                "business_logic_plan": str(response)
            }

        except Exception as e:
            logger.error(f"Error refining plan: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def update_plan_based_on_feedback(self, feedback: str) -> Dict[str, Any]:
        """
        Update the business logic plan to incorporate ALL cumulative feedback.

        This uses the Planner Agent to surgically update the affected sections
        while preserving the original structure, format, and unaffected content.
        All requirements are actually implemented in the business logic (not just noted),
        but the plan maintains consistency with the original.

        Args:
            feedback: User's latest feedback (already added to cumulative requirements)

        Returns:
            Dictionary with updated business logic plan
        """
        if not self.planner:
            return {
                "status": "error",
                "error": "Planner not initialized"
            }

        try:
            logger.info("=" * 80)
            logger.info("UPDATING BUSINESS LOGIC PLAN BASED ON ALL FEEDBACK")
            logger.info("=" * 80)
            logger.info(f"User feedback: {feedback}")

            # Get CSV summary for context
            from ai.ira_builder.tools.csv_tools import get_csv_summary
            try:
                csv_summary = get_csv_summary(self.csv_filepaths)
                logger.info("Retrieved CSV structure for context")

                # Reinitialize planner's memory with CSV context (if not already set)
                if self.planner and hasattr(self.planner, 'memory') and self.planner.memory:
                    if not self.planner.memory.csv_analysis:
                        self.planner.memory.set_csv_analysis(csv_summary)
                        self.planner.memory.set_workflow_context(
                            self.workflow_name,
                            self.workflow_description,
                            self.csv_filepaths
                        )
                        logger.info("Reinitialized planner memory with CSV context")
            except Exception as e:
                logger.warning(f"Could not retrieve CSV summary: {e}")
                csv_summary = f"CSV Files: {', '.join(self.csv_filepaths)}"

            # Format all cumulative requirements
            all_requirements = "\n".join([
                f"  {i}. {req}"
                for i, req in enumerate(self.state.cumulative_refinement_requirements, 1)
            ])

            # Build prompt to UPDATE the plan while preserving structure
            update_prompt = f"""
You are updating the Business Logic Plan to incorporate user refinement requirements.

WORKFLOW CONTEXT:
- Name: {self.workflow_name}
- Description: {self.workflow_description}

CSV DATA STRUCTURE:
{csv_summary}

CURRENT BUSINESS LOGIC PLAN (BASE to build upon):
{self.state.business_logic_plan}

ALL REFINEMENT REQUIREMENTS (must be incorporated):
{all_requirements}

CRITICAL INSTRUCTIONS:

1. PRESERVE THE ORIGINAL STRUCTURE:
   - Keep the exact same section structure as the current plan
   - Maintain the same HTML format with <b> tags
   - Keep the same level of detail and writing style
   - Preserve all sections: Business Logic, Data Processing Steps, Output Columns, Additional Requirements

2. UPDATE ONLY WHAT'S NECESSARY:
   - Identify which sections are affected by the refinement requirements
   - Update ONLY those specific sections to incorporate the requirements
   - For Business Logic: Add/modify rules to implement the requirements (not just note them)
   - For Data Processing Steps: Add/modify steps to handle the requirements
   - For Output Columns: Add new columns or modify existing column descriptions as needed
   - For Additional Requirements: Update this section to list the refinements

3. IMPLEMENT, DON'T JUST DOCUMENT:
   - DO NOT just add comments like "Note: User requested X"
   - DO update the actual business rules to implement X
   - DO add new data processing steps if needed
   - DO add new output columns if requested
   - Ensure every requirement is actually implemented in the logic

4. PRESERVE UNAFFECTED SECTIONS:
   - Sections/rules/steps not affected by requirements should remain EXACTLY the same
   - Do not rephrase or restructure content that doesn't need to change
   - Only modify what's directly impacted by the refinement requirements

5. MAINTAIN CONSISTENCY:
   - Ensure new rules/steps are numbered consistently with existing ones
   - Keep the same terminology and naming conventions
   - Match the writing style of the original plan

Output the COMPLETE updated Business Logic Plan with:
- The same structure and format as the current plan
- Only the necessary sections updated to incorporate ALL refinement requirements
- All requirements actually implemented in the business logic (not just noted)
"""

            # Use planner's thread to maintain context
            response = await self.planner.agent.run(update_prompt, thread=self.planner.thread)

            # Extract the updated plan
            updated_plan = str(response)

            # Update state
            old_plan = self.state.business_logic_plan
            self.state.business_logic_plan = updated_plan

            # Record in conversation history
            self.state.planner_conversation_history.append({
                "role": "user",
                "content": f"[Output Refinement Request] {feedback}",
                "timestamp": datetime.now().isoformat()
            })
            self.state.planner_conversation_history.append({
                "role": "assistant",
                "content": updated_plan,
                "timestamp": datetime.now().isoformat(),
                "is_updated_plan": True,
                "refinement_type": "output_feedback"
            })

            # Store the old plan in feedback history for audit trail (if feedback exists)
            if self.state.output_feedback_history:
                self.state.output_feedback_history[-1]["plan_before"] = old_plan
                self.state.output_feedback_history[-1]["plan_after"] = updated_plan

            self._persist_state()

            logger.info("✅ Business Logic Plan updated successfully with all cumulative requirements")

            return {
                "status": "success",
                "updated_plan": updated_plan
            }

        except Exception as e:
            logger.error(f"Error updating plan: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def approve_output_and_continue(self) -> Dict[str, Any]:
        """
        Approve the output and proceed to analysis report generation.

        This transitions from OUTPUT_REVIEW to ANALYSIS_REPORT_GENERATION phase.

        Returns:
            Dictionary with analysis instructions generation result
        """
        if self.state.phase != WorkflowPhase.OUTPUT_REVIEW:
            return {
                "status": "error",
                "error": "Can only approve output in OUTPUT_REVIEW phase"
            }

        try:
            logger.info("=" * 80)
            logger.info("OUTPUT APPROVED - PROCEEDING TO ANALYSIS REPORT GENERATION")
            logger.info("=" * 80)

            self.state.output_approved = True
            self._persist_state()

            logger.info("✅ Output approved, generating analysis instructions...")

            # Automatically generate analysis instructions
            return await self.generate_analysis_instructions()

        except Exception as e:
            logger.error(f"Error approving output: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def refine_output(self, feedback: str, max_refinement_iterations: int = 3) -> Dict[str, Any]:
        """
        Refine the output based on user feedback using the plan-first approach.

        This method:
        1. Adds feedback to cumulative refinement requirements
        2. Updates the Business Logic Plan to incorporate ALL requirements surgically
        3. Transitions to PLAN_REVIEW phase so user can review the updated plan
        4. User must approve updated plan before code regeneration

        The plan is updated to preserve original structure and format while ensuring
        all cumulative requirements are properly implemented in the business logic.

        Args:
            feedback: User's feedback describing what needs to be changed
            max_refinement_iterations: Maximum refinement attempts (default: 3)

        Returns:
            Dictionary with updated plan
        """
        if self.state.phase != WorkflowPhase.OUTPUT_REVIEW:
            return {
                "status": "error",
                "error": "Can only refine output in OUTPUT_REVIEW phase"
            }

        if self.state.output_refinement_iterations >= max_refinement_iterations:
            return {
                "status": "error",
                "error": f"Maximum refinement iterations ({max_refinement_iterations}) reached"
            }

        try:
            logger.info("=" * 80)
            logger.info(f"REFINING OUTPUT (Attempt {self.state.output_refinement_iterations + 1}/{max_refinement_iterations})")
            logger.info("=" * 80)
            logger.info(f"User feedback: {feedback}")

            # Record feedback in history
            self.state.output_feedback_history.append({
                "timestamp": datetime.now().isoformat(),
                "feedback": feedback,
                "iteration": self.state.output_refinement_iterations + 1
            })
            self.state.output_refinement_iterations += 1

            # Add to cumulative requirements (BEFORE updating plan so it's available in prompt)
            self.state.cumulative_refinement_requirements.append(feedback)
            logger.info(f"Added to cumulative requirements. Total requirements: {len(self.state.cumulative_refinement_requirements)}")

            # Step 1: Update Business Logic Plan to incorporate ALL cumulative requirements
            update_result = await self.update_plan_based_on_feedback(feedback)

            if update_result['status'] != 'success':
                return update_result

            # Step 2: Transition to PLAN_REVIEW phase
            self._change_phase(WorkflowPhase.PLAN_REVIEW)
            self._persist_state()

            logger.info("✅ Business Logic Plan updated. User must review and approve the updated plan.")

            return {
                "status": "success",
                "phase": self.state.phase.value,
                "updated_plan": update_result['updated_plan'],
                "message": f"Business Logic Plan has been updated to incorporate all {len(self.state.cumulative_refinement_requirements)} refinement requirement(s). Please review the updated plan and approve to regenerate code.",
                "refinement_iteration": self.state.output_refinement_iterations
            }

        except Exception as e:
            logger.error(f"Error refining output: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def regenerate_code_from_updated_plan(self) -> Dict[str, Any]:
        """
        Regenerate code from the updated Business Logic Plan after user approval.

        This is called after the user approves the updated plan during refinement.
        It follows the same code generation flow as the original approval.

        Returns:
            Dictionary with code generation and execution results
        """
        if self.state.phase != WorkflowPhase.PLAN_REVIEW:
            return {
                "status": "error",
                "error": "Can only regenerate code in PLAN_REVIEW phase"
            }

        if not self.state.business_logic_plan:
            return {
                "status": "error",
                "error": "No business logic plan available"
            }

        try:
            logger.info("=" * 80)
            logger.info("UPDATED PLAN APPROVED - REGENERATING CODE")
            logger.info("=" * 80)

            # Transition to CODING phase
            self._change_phase(WorkflowPhase.CODING)

            # Update Coder's memory with the new plan
            if self.coder:
                # Update the business logic plan in Coder's memory
                self.coder.business_logic_plan = self.state.business_logic_plan
                if self.coder.memory:
                    self.coder.memory.business_logic_plan = self.state.business_logic_plan

                # Reset coder iteration count for fresh code generation
                self.coder.iteration_count = 0

                logger.info("Updated Coder with new Business Logic Plan")
            else:
                return {
                    "status": "error",
                    "error": "Coder not initialized"
                }

            # Generate and execute code using the updated plan
            logger.info("Generating and executing code from updated plan...")

            result = await self.coder.generate_and_execute_code()

            # Update state based on result
            if result['status'] == 'success':
                logger.info("✅ CODE REGENERATION AND EXECUTION SUCCESSFUL!")

                self.state.generated_code = result['code']
                self.state.code_execution_iterations = result['iterations']
                self.state.code_execution_result = result

                # Save generated code to file
                code_filepath = self._save_generated_code(result['code'])

                logger.info(f"Regenerated code saved to: {code_filepath}")
                logger.info(f"Output data saved to: {result['output_path']}")
                logger.info(f"Total iterations: {result['iterations']}")

                # Transition to OUTPUT_REVIEW phase for user validation
                self._change_phase(WorkflowPhase.OUTPUT_REVIEW)
                self._persist_state()

                return {
                    "status": "success",
                    "phase": self.state.phase.value,
                    "code": result['code'],
                    "code_filepath": str(code_filepath),
                    "output_path": result['output_path'],
                    "output_preview": result.get('output_preview'),
                    "output_summary": result.get('output_summary'),
                    "iterations": result['iterations'],
                    "refinement_iteration": self.state.output_refinement_iterations
                }

            else:
                logger.error(f"❌ CODE REGENERATION FAILED: {result.get('error')}")

                # Transition back to OUTPUT_REVIEW to allow user to try again
                self._change_phase(WorkflowPhase.OUTPUT_REVIEW)
                self._persist_state()

                return {
                    "status": "error",
                    "phase": self.state.phase.value,
                    "error": result.get('error'),
                    "iterations": result.get('iterations', 0),
                    "last_code": result.get('last_code'),
                    "last_execution_result": result.get('last_execution_result'),
                    "refinement_iteration": self.state.output_refinement_iterations
                }

        except Exception as e:
            logger.error(f"Error during code regeneration: {str(e)}", exc_info=True)
            self._change_phase(WorkflowPhase.OUTPUT_REVIEW)
            self._persist_state()

            return {
                "status": "error",
                "phase": self.state.phase.value,
                "error": str(e)
            }

    # =========================================================================
    # ANALYSIS REPORT GENERATION METHODS
    # =========================================================================

    async def generate_analysis_instructions(self) -> Dict[str, Any]:
        """
        Generate analysis report instructions based on workflow context.

        This is called after output is approved to move to analysis report phase.
        Uses Groq mode to generate instructions describing what will be in the report.

        Returns:
            Dictionary with generated instructions
        """
        if self.state.phase != WorkflowPhase.OUTPUT_REVIEW:
            return {
                "status": "error",
                "error": "Can only generate analysis instructions after output review"
            }

        try:
            logger.info("=" * 80)
            logger.info("GENERATING ANALYSIS REPORT INSTRUCTIONS")
            logger.info("=" * 80)

            # Transition to analysis report generation phase
            self._change_phase(WorkflowPhase.ANALYSIS_REPORT_GENERATION)

            # Create a simple chat client using Groq (coder_provider)
            from ai.ira_builder.utils.llm_provider import create_chat_client
            config = get_config()

            chat_client = create_chat_client(
                provider=config.coder_provider,
                model=None  # Use provider default
            )

            # Create prompt for generating instructions
            prompt = f"""You are generating concise analysis report instructions for a data analysis workflow.

**Workflow Context:**
- **Workflow Name:** {self.workflow_name}
- **Workflow Description:** {self.workflow_description}

**Business Logic Plan:**
{self.state.business_logic_plan}

**Generated Code (how output was created):**
```python
{self.state.generated_code}
```

**IMPORTANT:**
- The Business Logic Plan explains WHAT the workflow is supposed to do and WHY
- The Generated Code shows HOW the output DataFrame was created from raw input data
- Use both to understand: What validations were performed? Was data filtered or do all rows remain with flags? What columns were added?
- The analysis report will be generated by an LLM with token limits, so keep instructions BRIEF and focused on HIGH-LEVEL SUMMARIES only

**CRITICAL - Analysis Report Input:**
- The analysis report code will ONLY receive the OUTPUT CSV file from the generated code above
- It will NOT have access to any raw input files
- All analysis must be performed on the OUTPUT CSV ONLY
- The instructions should reference columns that exist in the OUTPUT CSV, not raw data

**CRITICAL - Understanding Data Filtering:**
- LOOK AT THE GENERATED CODE to see if data was FILTERED
- If the code has filtering like `df[df['Exception_Flag'] == 1]`, then OUTPUT contains ONLY exceptions
- In this case, counting rows gives exception count directly - NO NEED to filter again or calculate percentages
- If OUTPUT is already filtered to exceptions, instructions should NOT say "count rows where Exception_Flag = 1" - just say "count all rows"
- If OUTPUT contains all data with flags, then instructions should say "count rows where Exception_Flag = 1"
- Be accurate about whether to filter or just count based on what the generated code already did

Based on the Business Logic Plan and Generated Code, generate concise instructions covering these points:

---

# Analysis Report Instructions

## 1. Exception Summary
- Total count of exceptions identified (based on whether output is filtered or contains all rows with flags)
- If output already filtered to exceptions only, just count total rows
- If output contains all rows with exception flag, count rows where flag indicates exception

## 2. Key Trends by Dimensions
- Analyze exception distribution by 3-5 key dimensions (specify which columns)
- Identify which entities/categories have the most exceptions

## 3. Time-Based Trends
[Only if applicable]
- Exception count by time period (month/quarter)
- Peak period with highest exceptions

## 4. Monetary Impact
[Only if applicable]
- Total value, average value, and range of exceptions
- Specify which amount column to use

## 5. Statistical Analysis
[Include if data is suitable for statistical/ML analysis]
- Correlation analysis between numeric columns (if multiple numeric columns exist)
- Distribution analysis (mean, median, std dev, outliers)
- Regression analysis to identify key factors (if applicable)
- Clustering patterns (if categories show groupings)

## 6. Overall Observations
- Main patterns from the exception data
- Notable findings from statistical analysis
- Actionable insights

## 7. No Exceptions Case
If no exceptions found, state: "No exceptions identified"

---

IMPORTANT:
- Keep it CONCISE and SIMPLE - users should easily understand and edit these instructions
- Be SPECIFIC - use actual column names from the workflow
- Focus on HIGH-LEVEL SUMMARIES only (no detailed data extraction)
- Each section: 2-4 bullet points maximum
- For statistical analysis, only suggest it if data is suitable (numeric columns, sufficient rows, etc.)
- DO NOT reference specific systems (SAP, Oracle, etc.) unless they appear in the workflow context
- Use generic terms like "documents", "records", "transactions" instead of system-specific terminology
- Avoid making assumptions about data sources - just describe the analysis to perform
- The LLM generating the report will understand the context from the Business Logic Plan and code you saw above
"""

            # Make the LLM call
            from agent_framework import ChatAgent
            temp_agent = ChatAgent(
                name="Analysis-Instruction-Generator",
                chat_client=chat_client,
                instructions="You generate clear, structured analysis report instructions.",
                tools=[]
            )

            thread = temp_agent.get_new_thread()
            instructions = await temp_agent.run(prompt, thread=thread)

            self.state.analysis_instructions = str(instructions)
            self._persist_state()

            logger.info("✅ Analysis report instructions generated")
            logger.info(f"Instructions preview: {str(instructions)[:200]}...")

            return {
                "status": "success",
                "phase": self.state.phase.value,
                "instructions": str(instructions)
            }

        except Exception as e:
            logger.error(f"Error generating analysis instructions: {str(e)}", exc_info=True)
            self._change_phase(WorkflowPhase.OUTPUT_REVIEW)
            self._persist_state()
            return {
                "status": "error",
                "error": str(e)
            }

    async def approve_analysis_instructions(self, edited_instructions: Optional[str] = None) -> Dict[str, Any]:
        """
        Approve analysis instructions (possibly edited by user) and generate analysis report.

        Args:
            edited_instructions: User-edited instructions (if None, use generated ones)

        Returns:
            Dictionary with analysis report generation results
        """
        if self.state.phase != WorkflowPhase.ANALYSIS_REPORT_GENERATION:
            return {
                "status": "error",
                "error": "Can only approve instructions in ANALYSIS_REPORT_GENERATION phase"
            }

        try:
            logger.info("=" * 80)
            logger.info("ANALYSIS INSTRUCTIONS APPROVED - GENERATING REPORT")
            logger.info("=" * 80)

            # Update instructions if user edited them
            if edited_instructions:
                self.state.analysis_instructions = edited_instructions
                logger.info("Using user-edited instructions")

            self.state.analysis_instructions_approved = True
            self._persist_state()

            # Now generate the analysis report
            return await self.generate_analysis_report()

        except Exception as e:
            logger.error(f"Error approving analysis instructions: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def generate_analysis_report(self) -> Dict[str, Any]:
        """
        Generate analysis report code and execute it to create .txt report.

        Uses Coder agent (with Groq) to generate code that:
        1. Reads the output CSV from previous step
        2. Performs analysis as per instructions
        3. Generates a .txt report file

        Returns:
            Dictionary with report content and file path
        """
        if not self.state.analysis_instructions_approved:
            return {
                "status": "error",
                "error": "Analysis instructions must be approved first"
            }

        try:
            logger.info("=" * 80)
            logger.info("GENERATING ANALYSIS REPORT CODE")
            logger.info("=" * 80)

            # Create Coder Agent with Groq provider
            config = get_config()
            if not self.coder:
                self.coder = create_coder_agent(
                    model=None,
                    temperature=0.3,
                    max_iterations=self.max_coder_iterations,
                    execution_timeout=self.code_execution_timeout,
                    provider=config.coder_provider
                )
                logger.info(f"Coder Agent created with provider: {config.coder_provider}")

            # Create analysis plan prompt using the structured planner approach
            analysis_plan_prompt = f"""You are a Planner. You have been provided with a processed dataframe, derived from raw data according to a specific query. Your primary responsibility is to conduct a detailed analysis of a particular question in relation to the headers of the provided dataframe. Your goal is to develop a comprehensive, step-by-step strategy that will guide a coder agent in creating an in-depth analysis report. This report should not only address the user's query directly but also uncover additional insights and observations that may be relevant.

**Workflow Context:**
- **Workflow Name:** {self.workflow_name}
- **Workflow Description:** {self.workflow_description}

**User's Question/Query:**
{self.state.analysis_instructions}

**Understanding Previous Data Processing Steps:**
The raw data has been processed according to the following Business Logic Plan:

{self.state.business_logic_plan}

**Generated Code (How the Filtered DataFrame Was Created):**
```python
{self.state.generated_code}
```

**Input Data Available for Analysis:**
- The output CSV file: {self.state.output_file_path}
- This CSV contains the processed dataframe with all validation results

#### Step-by-Step Strategy

1. **Understanding the Query**:
   - Start by thoroughly examining the user's question in the Analysis Instructions above
   - Break it down to grasp its core components, paying special attention to any explicit requirements or constraints mentioned
   - Consider the broader context and the underlying purpose of the query to ensure a comprehensive understanding

2. **Understanding Previous Data Processing Steps**:
   - Understand what data processing steps have been taken so far to generate this filtered dataframe
   - As per the user query, previous agents have processed raw data as per the Business Logic Plan to generate this filtered dataframe
   - Review the Generated Code to see exactly how the output dataframe was created

3. **Examining Filtered Dataframe Headers**:
   - Carefully review the dataframe columns (visible in the Generated Code) to identify columns that directly relate to the user's question
   - Also identify other columns that, while not directly related, could provide valuable insights or contribute to a more nuanced understanding of the data
   - Remember, the user can view the dataframe; focus on performing meaningful analysis that answers the question and offers additional insights

4. **Defining Analysis Objectives**:
   - Clearly state the objectives of your analysis, including both the primary goal focused on the user's query and secondary goals aimed at uncovering further insights
   - Ensure these objectives are SMART (Specific, Measurable, Achievable, Relevant, Time-bound) to guide a focused and effective analysis
   - Keep in mind that the user can view the dataframe; your analysis should go beyond mere data extraction to provide useful insights

5. **Selecting Analysis Techniques**:
   - Outline the statistical and ML methods that are most appropriate for analyzing the data in light of your objectives
   - Consider using scikit-learn for: correlation analysis, linear/logistic regression, clustering (KMeans), outlier detection
   - Match these techniques with their intended objectives in a logical and systematic manner
   - For basic statistics: use simple pandas operations like len(), value_counts(), sum(), mean(), median(), std()
   - For advanced analysis: correlation matrices, regression to identify key factors, clustering to find patterns
   - IMPORTANT: Only suggest ML techniques if data is suitable (sufficient numeric columns, adequate sample size)
   - Do NOT include any coding instructions or visualization plans - focus only on WHAT analysis should be done, not HOW to code it

6. **Planning Data Aggregation**:
   - Determine which columns are relevant for grouping and aggregation based on the demands of the query
   - Specify the precise statistical aggregations needed (e.g., count, sum, mean) to support your analysis effectively
   - Keep aggregations simple and avoid complex date manipulations

7. **Identifying Key Metrics**:
   - Identify crucial metrics or indicators that will play a key role in answering the user's question
   - Also consider other metrics that could reveal additional insights into the dataset, enhancing the depth of your analysis

**Instruction**:
Your response should strictly focus on Steps 3, 4, 5, 6, and 7 only, guiding the coder agent on what analysis needs to be done to generate an analysis report with data.

**Note:** Please add 'TERMINATE' at the end of your final response to indicate completion."""

            # Initialize Coder with analysis task
            from agent_framework import ChatAgent
            from ai.ira_builder.utils.llm_provider import create_chat_client

            chat_client = create_chat_client(
                provider=config.coder_provider,
                model=None
            )

            # Create planner for analysis plan
            planner_agent = ChatAgent(
                name="Analysis-Planner",
                chat_client=chat_client,
                instructions="You create detailed analysis plans for data reporting.",
                tools=[]
            )

            thread = planner_agent.get_new_thread()
            analysis_plan = await planner_agent.run(analysis_plan_prompt, thread=thread)

            self.state.analysis_plan = str(analysis_plan)
            self._persist_state()

            logger.info("✅ Analysis plan generated")
            logger.info(f"Plan preview: {str(analysis_plan)[:300]}...")

            # Now generate code using Coder agent
            logger.info("Generating analysis report code...")

            code_prompt = f"""Generate professional Python code to create a comprehensive analysis report.

**Workflow Context:**
- Workflow Name: {self.workflow_name}
- Workflow Description: {self.workflow_description}

**Business Logic Plan (How the output data was created):**
{self.state.business_logic_plan}

**Generated Code (How exceptions were filtered/processed):**
```python
{self.state.generated_code}
```

**IMPORTANT CONTEXT:**
- The OUTPUT CSV you are analyzing was created by the code above
- Understand what filters were applied (e.g., only exception rows, specific conditions)
- If code filtered for exceptions, then all rows in output ARE exceptions
- Reference the Business Logic Plan to understand what was validated and why
- Don't assume output contains all original data - it may be filtered

**Analysis Instructions:**
{self.state.analysis_instructions}

**Analysis Plan:**
{analysis_plan}

**Code Template (MUST follow exactly):**

```python
# PART 1: IMPORT LIBRARIES
# NOTE: NO IRA PREPROCESSING - This is analysis code, not data processing code!
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
import warnings
warnings.filterwarnings('ignore')

# DO NOT import ira - this is not a data processing workflow!

# PART 2: FILE PATHS AND FILE LOADING
# CRITICAL: DO NOT use hardcoded paths - use the provided variables
input_csv_path = csv_files[0]  # The already-processed CSV from the workflow
output_file_path = output_path  # The .txt file where the report will be saved

# Load the already-processed CSV file
# NOTE: This CSV is the OUTPUT from the previous workflow step - do NOT apply IRA preprocessing!
df = pd.read_csv(input_csv_path)
print(f"Loaded {{len(df):,}} rows from processed output CSV")

# PART 3: ANALYSIS AND REPORT GENERATION
# Build the report as a list of text lines
report_lines = []

# HEADER SECTION
report_lines.append("=" * 80)
report_lines.append("WORKFLOW ANALYSIS REPORT")
report_lines.append(f"Workflow: [USE WORKFLOW NAME FROM CONTEXT]")
report_lines.append(f"Description: [USE WORKFLOW DESCRIPTION FROM CONTEXT]")
report_lines.append(f"Generated on: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
report_lines.append("=" * 80)
report_lines.append("")

# SECTION 1: EXCEPTION COUNT / DATASET OVERVIEW
report_lines.append("1. EXCEPTION COUNT")
report_lines.append("-" * 80)
report_lines.append(f"   Total Exceptions Identified: {{len(df):,}}")
report_lines.append("")

# SECTION 2: KEY TRENDS AND PATTERNS
report_lines.append("2. KEY TRENDS AND PATTERNS")
report_lines.append("-" * 80)
# Analyze top categories/dimensions
# Example: Top 10 by exception count
# ⚠️ IMPORTANT: When using groupby().size(), the grouped column becomes INDEX
# CORRECT WAY:
# top_categories = df.groupby('category_column').size().sort_values(ascending=False).head(10)
# for category, count in top_categories.items():  # Use .items(), not .iterrows()
#     report_lines.append(f"   • {{category}}: {{count:,}} exceptions")
#
# ALTERNATIVE: Convert to DataFrame first
# top_df = df.groupby('category_column').size().reset_index(name='Exception_Count').head(10)
# for i, row in top_df.iterrows():
#     report_lines.append(f"   • {{row['category_column']}}: {{int(row['Exception_Count']):,}} exceptions")
report_lines.append("")

# SECTION 3: TIME-BASED TRENDS (if applicable)
report_lines.append("3. PEAK PERIOD TRENDS")
report_lines.append("-" * 80)
# Analyze by time period if date columns exist
# period_analysis = df.groupby('period_column').size()
# peak_period = period_analysis.idxmax()
# report_lines.append(f"   Peak Period: {{peak_period}} with {{period_analysis.max()}} exceptions")
report_lines.append("")

# SECTION 4: MONETARY IMPACT (if applicable)
report_lines.append("4. MONETARY IMPACT")
report_lines.append("-" * 80)
# Analyze monetary columns if they exist
# total_amount = df['amount_column'].sum()
# avg_amount = df['amount_column'].mean()
# report_lines.append(f"   Total Amount: ${{total_amount:,.2f}}")
# report_lines.append(f"   Average Amount: ${{avg_amount:,.2f}}")
report_lines.append("")

# SECTION 5: STATISTICAL ANALYSIS (if applicable)
report_lines.append("5. STATISTICAL ANALYSIS")
report_lines.append("-" * 80)
# Perform correlation, regression, clustering as per analysis plan
# Example correlation:
# numeric_cols = df.select_dtypes(include=[np.number]).columns
# if len(numeric_cols) > 1:
#     corr_matrix = df[numeric_cols].corr()
#     # Report top correlations
report_lines.append("")

# SECTION 6: OVERALL OBSERVATIONS
report_lines.append("6. OVERALL OBSERVATIONS")
report_lines.append("-" * 80)
# Summarize key findings
# report_lines.append(f"   • {{observation_1}}")
# report_lines.append(f"   • {{observation_2}}")
report_lines.append("")

# SECTION 7: RECOMMENDATIONS (if applicable)
report_lines.append("7. RECOMMENDATIONS")
report_lines.append("-" * 80)
# Provide actionable recommendations
report_lines.append("")

# FOOTER
report_lines.append("=" * 80)
report_lines.append("END OF ANALYSIS")
report_lines.append("=" * 80)

# Build final report (join all report lines into a single string)
report_content = "\\n".join(report_lines)

# ⚠️ CRITICAL: Write to .TXT file (NOT CSV!)
# This MUST use open() and write(), NOT df.to_csv()
with open(output_file_path, 'w') as f:
    f.write(report_content)

print(f"✓ Analysis report saved to: {{output_file_path}}")

# ❌ DO NOT write: result_df.to_csv(output_file_path, index=False)
# ❌ DO NOT create or save any CSV files
# ✅ The output file MUST be a text report, not a CSV!
```

**❌❌❌ CRITICAL - WHAT THIS CODE SHOULD NOT DO ❌❌❌**

THIS IS NOT A DATA PROCESSING WORKFLOW! DO NOT:
- ❌ Use IRA preprocessing (no ira.convert_date_column, no ira.clean_strings_batch, etc.)
- ❌ Perform data transformations or calculations
- ❌ Filter or modify the dataframe
- ❌ Use df.to_csv() - this creates a CSV file, NOT a text report!
- ❌ Generate validation logic or business rules
- ❌ Process raw data - the data is ALREADY PROCESSED

**✅✅✅ WHAT THIS CODE SHOULD DO ✅✅✅**

THIS IS AN ANALYSIS REPORT GENERATOR! YOU MUST:
- ✅ Read the ALREADY-PROCESSED CSV file (it's the output from previous step)
- ✅ Analyze the data using pandas operations (groupby, value_counts, sum, mean, etc.)
- ✅ Build a text report as a list of strings (report_lines.append())
- ✅ Write the report to a .TXT file using: with open(output_file_path, 'w') as f: f.write(report_content)
- ✅ The output MUST be a human-readable text report, NOT a CSV file!

**CRITICAL Instructions - READ CAREFULLY:**

1. MANDATORY STRUCTURE:
   - MUST follow the template structure with proper headers and sections
   - Use "=" * 80 for main dividers, "-" * 80 for section dividers
   - Include clear section numbers (1., 2., 3., etc.)
   - Add proper indentation (3-6 spaces) for subsection content
   - Header MUST use actual workflow name and description from context (not placeholder text)
   - End with "END OF ANALYSIS" footer
   - Do NOT use "SAP" or other company names unless they appear in workflow context

2. FILE PATHS:
   - Use csv_files[0] for input (NOT hardcoded paths)
   - Use output_path variable for output (NOT hardcoded paths)
   - INPUT is the already-processed CSV from the workflow
   - OUTPUT is a .TXT file containing the analysis report

3. REPORT FORMATTING:
   - Format numbers with commas: f"{{value:,}}" or f"{{value:,.2f}}"
   - Use bullet points (•) for observations
   - Indent lists and sub-points properly
   - Keep lines readable (avoid overly long lines)
   - Use descriptive labels, not just raw values

4. ALLOWED Basic Pandas Operations:
   - len(df), df['column'].value_counts(), df['column'].sum(), df['column'].mean()
   - df['column'].describe(), df['column'].quantile([0.25, 0.5, 0.75])
   - df.groupby('col')['col2'].count(), df.groupby('col')['col2'].sum()
   - df.groupby('col').size().sort_values(ascending=False).head(10)
   - df[df['col'] == value] - basic filtering
   - df.select_dtypes(include=[np.number]) - select numeric columns

   ⚠️ CRITICAL - Handling Grouped Data:
   - When you do: grouped = df.groupby('Company Code').size()
   - The result is a Series where 'Company Code' is the INDEX, not a column!
   - To iterate: for company_code, count in grouped.items():
   - NOT: for row in grouped.iterrows(): row['Company Code']  ❌ This will fail!
   - If you need DataFrame: grouped.reset_index(name='Count') to convert index to column

5. HANDLING LARGE DATASETS:
   - ⚠️ CRITICAL: If dataset has more than 100,000 rows, SAMPLE IT FIRST!
   - Use: df_sample = df.sample(n=min(50000, len(df)), random_state=42)
   - Perform analysis on the sample to avoid timeouts
   - Mention in report: "Analysis based on sample of X rows"

6. STATISTICAL/ML Operations - USE SPARINGLY:
   - Basic stats only: df['col'].describe(), df.corr() for correlation
   - ⚠️ AVOID EXPENSIVE OPERATIONS on large datasets:
     - NO LinearRegression, KMeans, IsolationForest if > 50K rows
     - NO complex ML that takes > 5 seconds
   - If you must use ML, use the sampled dataset (max 50K rows)
   - Always use try-except blocks for ML operations

7. FORBIDDEN operations (DO NOT USE):
   - df['date_col'].dt.to_period() - NO date period conversions
   - df['date_col'].dt.anything() - NO datetime operations
   - Complex string operations or regex
   - Pivot tables or complex reshaping
   - Complex ML models (neural networks, ensemble methods beyond what's shown)

8. DATA PRESENTATION:
   - Show TOP 10 items for categories/trends (not all data)
   - Calculate percentages where relevant
   - Provide totals, averages, min, max for monetary values
   - Use descriptive category names (include column values, not just keys)
   - Present data in ranked/sorted order (highest to lowest)

9. ANALYSIS REQUIREMENTS:
   - Each section MUST have actual data analysis, not just headers
   - Provide insights, not just raw numbers
   - Include context and interpretation
   - Add observations about patterns and anomalies
   - Suggest recommendations based on findings

10. DATA CONTEXT UNDERSTANDING:
   - Read the Business Logic Plan and Generated Code to understand what the output data represents
   - If the generated code filtered for exceptions (e.g., df[df['exception_flag'] == 1]), then ALL rows in output are exceptions
   - Don't say "32,067 exceptions out of total rows" if all rows ARE the exceptions
   - Understand what columns were added (flags, calculations) vs original data
   - Know whether output is filtered or complete dataset
   - Reference the validation logic when explaining findings

Generate complete, professional-quality analysis code now."""

            # CRITICAL: For analysis reports, we need to bypass the Coder agent's Business Logic workflow
            # and directly generate simple analysis code using a Chat agent

            # Create a simple code generation prompt that doesn't confuse the Coder
            simple_code_prompt = f"""⚠️⚠️⚠️ THIS IS NOT A WORKFLOW CODE GENERATION TASK! ⚠️⚠️⚠️

This is an ANALYSIS REPORT generation task. You must generate code that:
- ✅ Reads an ALREADY-PROCESSED CSV file
- ✅ Analyzes the data
- ✅ Writes a TEXT REPORT (NOT a CSV!)

❌ DO NOT generate workflow code
❌ DO NOT use IRA preprocessing
❌ DO NOT use df.to_csv()
❌ DO NOT apply business logic or transformations

**YOUR TASK:**
Generate Python code to analyze a CSV file and write an analysis report to a .txt file.

**INPUT:**
- CSV file path: csv_files[0] (this is ALREADY PROCESSED data)
- Output file path: output_path (this will be a .txt file)

**WHAT TO ANALYZE:**
{self.state.analysis_instructions}

**HOW TO ANALYZE:**
{analysis_plan}

**CODE TEMPLATE - FOLLOW THIS EXACTLY:**

```python
import pandas as pd
import numpy as np
from datetime import datetime

# Load data
df = pd.read_csv(csv_files[0])

# Build report
report_lines = []
report_lines.append("=" * 80)
report_lines.append("WORKFLOW ANALYSIS REPORT")
report_lines.append(f"Workflow: {self.workflow_name}")
report_lines.append(f"Generated on: {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}")
report_lines.append("=" * 80)

# Add your analysis sections here
# Example: report_lines.append(f"Total rows: {{len(df):,}}")

# Build and write report
report_content = "\\n".join(report_lines)
with open(output_path, 'w') as f:
    f.write(report_content)
```

Generate the complete analysis code following this structure. Focus on ANALYZING the data, not transforming it!"""

            # Initialize coder workflow with the simple prompt
            init_result = await self.coder.initialize_workflow(
                workflow_name=f"{self.workflow_name} - Analysis Report",
                business_logic_plan=simple_code_prompt,
                csv_filepaths=[self.state.output_file_path],
                output_filename=f"{sanitize_filename(self.workflow_name)}_analysis_report.txt"
            )

            logger.info("Coder initialized for analysis report generation")

            # Generate and execute code
            result = await self.coder.generate_and_execute_code()

            if result['status'] == 'success':
                logger.info("✅ ANALYSIS REPORT GENERATED SUCCESSFULLY")

                self.state.analysis_code = result['code']
                # Get the actual output path from coder result
                actual_output_path = result.get('output_path')

                if actual_output_path and Path(actual_output_path).exists():
                    self.state.analysis_report_file_path = actual_output_path
                    # Read the report content
                    with open(actual_output_path, 'r') as f:
                        self.state.analysis_report_content = f.read()

                    logger.info(f"📄 Analysis report saved to: {actual_output_path}")
                else:
                    logger.warning(f"Expected .txt file not found at {actual_output_path}")
                    self.state.analysis_report_content = "Report file not found. Code executed but output location may differ."

                # Transition to review phase
                self._change_phase(WorkflowPhase.ANALYSIS_REPORT_REVIEW)
                self._persist_state()

                return {
                    "status": "success",
                    "phase": self.state.phase.value,
                    "analysis_plan": self.state.analysis_plan,
                    "code": self.state.analysis_code,
                    "report_file_path": self.state.analysis_report_file_path,
                    "report_content": self.state.analysis_report_content,
                    "iterations": result.get('iterations', 0)
                }
            else:
                logger.error(f"❌ ANALYSIS REPORT GENERATION FAILED: {result.get('error')}")
                return {
                    "status": "error",
                    "phase": self.state.phase.value,
                    "error": result.get('error'),
                    "iterations": result.get('iterations', 0)
                }

        except Exception as e:
            logger.error(f"Error generating analysis report: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def approve_analysis_report(self) -> Dict[str, Any]:
        """
        Approve the analysis report and complete the workflow.

        This transitions from ANALYSIS_REPORT_REVIEW to COMPLETED phase.

        Returns:
            Dictionary with completion status
        """
        if self.state.phase != WorkflowPhase.ANALYSIS_REPORT_REVIEW:
            return {
                "status": "error",
                "error": "Can only approve analysis report in ANALYSIS_REPORT_REVIEW phase"
            }

        try:
            logger.info("=" * 80)
            logger.info("ANALYSIS REPORT APPROVED - WORKFLOW COMPLETED")
            logger.info("=" * 80)

            self.state.analysis_report_approved = True
            self.state.is_successful = True
            self.state.completed_at = datetime.now()
            self._change_phase(WorkflowPhase.COMPLETED)
            self._persist_state()

            execution_time = (self.state.completed_at - self.state.started_at).total_seconds()

            logger.info(f"✅ Workflow completed successfully in {execution_time:.2f} seconds")

            return {
                "status": "success",
                "phase": self.state.phase.value,
                "output_path": self.state.output_file_path,
                "analysis_report_path": self.state.analysis_report_file_path,
                "execution_time": execution_time,
                "is_successful": True
            }

        except Exception as e:
            logger.error(f"Error approving analysis report: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def refine_analysis_report(self, feedback: str) -> Dict[str, Any]:
        """
        Refine the analysis report based on user feedback.

        Regenerates the analysis code to incorporate feedback and creates new report.

        Args:
            feedback: User's feedback on how to improve the report

        Returns:
            Dictionary with updated report content
        """
        if self.state.phase != WorkflowPhase.ANALYSIS_REPORT_REVIEW:
            return {
                "status": "error",
                "error": "Can only refine report in ANALYSIS_REPORT_REVIEW phase"
            }

        try:
            logger.info("=" * 80)
            logger.info("REFINING ANALYSIS REPORT BASED ON FEEDBACK")
            logger.info("=" * 80)
            logger.info(f"User feedback: {feedback}")

            self.state.analysis_refinement_iterations += 1
            self.state.analysis_feedback_history.append({
                "iteration": self.state.analysis_refinement_iterations,
                "feedback": feedback,
                "timestamp": datetime.now().isoformat()
            })

            # Create refinement prompt
            refinement_prompt = f"""The user has provided feedback on the analysis report. Regenerate the code to address their feedback.

**Original Analysis Instructions:**
{self.state.analysis_instructions}

**Current Analysis Plan:**
{self.state.analysis_plan}

**User Feedback:**
{feedback}

**Current Code:**
{self.state.analysis_code}

**Task:** Update the code to incorporate the user's feedback while maintaining the three-part structure and ensuring the output is saved to the correct .txt file path.

Generate the complete, updated code now."""

            # Reinitialize coder with refinement prompt
            config = get_config()
            if not self.coder:
                self.coder = create_coder_agent(
                    model=None,
                    temperature=0.3,
                    max_iterations=self.max_coder_iterations,
                    execution_timeout=self.code_execution_timeout,
                    provider=config.coder_provider
                )

            init_result = await self.coder.initialize_workflow(
                workflow_name=f"{self.workflow_name} - Analysis Report (Refined)",
                business_logic_plan=refinement_prompt,
                csv_filepaths=[self.state.output_file_path],
                output_filename=f"{sanitize_filename(self.workflow_name)}_analysis_report.txt"
            )

            # Generate and execute updated code
            result = await self.coder.generate_and_execute_code()

            if result['status'] == 'success':
                logger.info("✅ REFINED ANALYSIS REPORT GENERATED")

                self.state.analysis_code = result['code']

                # Look for the updated .txt file
                txt_file_pattern = f"storage/analysis_reports/{sanitize_filename(self.workflow_name)}_analysis_report.txt"
                txt_file = Path(txt_file_pattern)

                if txt_file.exists():
                    self.state.analysis_report_file_path = str(txt_file)
                    with open(txt_file, 'r') as f:
                        self.state.analysis_report_content = f.read()

                    logger.info(f"📄 Refined analysis report saved to: {txt_file}")

                self._persist_state()

                return {
                    "status": "success",
                    "phase": self.state.phase.value,
                    "code": self.state.analysis_code,
                    "report_file_path": self.state.analysis_report_file_path,
                    "report_content": self.state.analysis_report_content,
                    "refinement_iteration": self.state.analysis_refinement_iterations
                }
            else:
                logger.error(f"❌ REFINED REPORT GENERATION FAILED: {result.get('error')}")
                return {
                    "status": "error",
                    "error": result.get('error')
                }

        except Exception as e:
            logger.error(f"Error refining analysis report: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }

    async def approve_plan_and_generate_code(self) -> Dict[str, Any]:
        """
        Approve the business logic plan and proceed to code generation.

        This transitions from PLAN_REVIEW to CODING phase and starts
        the Coder Agent to generate and execute Python code.

        Returns:
            Dictionary with code generation and execution results
        """
        if self.state.phase != WorkflowPhase.PLAN_REVIEW:
            return {
                "status": "error",
                "error": "Can only approve plan in PLAN_REVIEW phase"
            }

        if not self.state.business_logic_plan:
            return {
                "status": "error",
                "error": "No business logic plan available to approve"
            }

        try:
            logger.info("=" * 80)
            logger.info("PLAN APPROVED - STARTING CODE GENERATION")
            logger.info("=" * 80)

            self.state.plan_approved = True
            self._change_phase(WorkflowPhase.CODING)

            # Create Coder Agent (using phase-specific provider)
            config = get_config()
            self.coder = create_coder_agent(
                model=self.model,
                temperature=0.3,
                max_iterations=self.max_coder_iterations,
                execution_timeout=self.code_execution_timeout,
                provider=config.coder_provider
            )
            logger.info(f"Coder Agent created with provider: {config.coder_provider}")

            logger.info("Initializing Coder Agent...")

            # Initialize Coder with Business Logic Plan
            init_result = await self.coder.initialize_workflow(
                workflow_name=self.workflow_name,
                business_logic_plan=self.state.business_logic_plan,
                csv_filepaths=self.csv_filepaths,
                output_filename=self.output_filename
            )

            self.state.output_file_path = init_result['output_path']

            logger.info(f"Coder initialized. Output will be saved to: {init_result['output_path']}")

            # Generate and execute code
            logger.info("Generating and executing code...")

            result = await self.coder.generate_and_execute_code()

            # Update state based on result
            if result['status'] == 'success':
                logger.info("✅ CODE GENERATION AND EXECUTION SUCCESSFUL!")

                self.state.generated_code = result['code']
                self.state.code_execution_iterations = result['iterations']
                self.state.code_execution_result = result

                # Save generated code to file
                code_filepath = self._save_generated_code(result['code'])

                logger.info(f"Generated code saved to: {code_filepath}")
                logger.info(f"Output data saved to: {result['output_path']}")
                logger.info(f"Total iterations: {result['iterations']}")

                # Transition to OUTPUT_REVIEW phase for user validation
                self._change_phase(WorkflowPhase.OUTPUT_REVIEW)
                self._persist_state()

                return {
                    "status": "success",
                    "phase": self.state.phase.value,
                    "code": result['code'],
                    "code_filepath": str(code_filepath),
                    "output_path": result['output_path'],
                    "output_preview": result.get('output_preview'),
                    "output_summary": result.get('output_summary'),
                    "iterations": result['iterations']
                }

            else:
                logger.error(f"❌ CODE GENERATION FAILED: {result.get('error')}")

                self.state.error_message = result.get('error', 'Code generation failed')
                self.state.code_execution_iterations = result.get('iterations', 0)
                self.state.generated_code = result.get('last_code')
                self.state.code_execution_result = result
                self._change_phase(WorkflowPhase.FAILED)

                self.state.completed_at = datetime.now()
                self._persist_state()

                return {
                    "status": "error",
                    "phase": self.state.phase.value,
                    "error": result.get('error'),
                    "iterations": result.get('iterations', 0),
                    "last_code": result.get('last_code'),
                    "last_execution_result": result.get('last_execution_result')
                }

        except Exception as e:
            logger.error(f"Error during code generation: {str(e)}", exc_info=True)
            self.state.error_message = str(e)
            self._change_phase(WorkflowPhase.FAILED)
            self._persist_state()

            return {
                "status": "error",
                "phase": self.state.phase.value,
                "error": str(e)
            }

    def _save_generated_code(self, code: str) -> Path:
        """Save generated code to a Python file."""
        code_dir = Path("./storage/generated_code")
        code_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize workflow name for filename
        safe_workflow_name = sanitize_filename(self.workflow_name)
        filename = f"{safe_workflow_name}_{timestamp}.py"
        filepath = code_dir / filename

        with open(filepath, 'w') as f:
            f.write(code)

        logger.info(f"Saved generated code to: {filepath}")
        return filepath

    def _is_user_ready_for_plan(self, user_input: str) -> bool:
        """
        Detect if user input indicates they're ready for plan generation.

        This saves an LLM call by detecting readiness at the orchestrator level
        instead of having the planner agent signal with "GENERATE_PLAN".

        Args:
            user_input: User's response text

        Returns:
            True if user is ready for plan generation, False otherwise
        """
        user_input_lower = user_input.lower().strip()

        # Common phrases indicating readiness for plan generation
        readiness_indicators = [
            # Direct affirmatives to "is there anything else?"
            "no, i think we've covered everything",
            "no, we've covered everything",
            "we've covered everything",
            "covered everything",
            "no, that's everything",
            "that's everything",
            "no, nothing else",
            "nothing else",

            # Explicit plan generation requests
            "generate the plan",
            "please generate the plan",
            "generate plan",
            "create the plan",
            "please create the plan",
            "proceed with the plan",
            "proceed with plan",

            # Simple affirmatives (if they seem confident)
            "yes, proceed",
            "yes proceed",
            "proceed",
            "continue",
            "looks good",
            "approved",
            "perfect",

            # Negative responses to "anything else?"
            "no",
            "nope",
            "nah",
        ]

        # Check if user input contains any of these indicators
        for indicator in readiness_indicators:
            if indicator in user_input_lower:
                return True

        # Check for pattern: starts with "no" and mentions "plan"
        if user_input_lower.startswith("no") and "plan" in user_input_lower:
            return True

        # Check for very short negative responses (likely answering "anything else?")
        # But only if we've asked at least 5 questions (likely at final review stage)
        if self.state.planner_questions_asked >= 5:
            if user_input_lower in ["no", "nope", "nah", "no.", "nope.", "n"]:
                return True

        return False

    def _format_feedback_history(self) -> str:
        """
        Format the complete feedback history for inclusion in prompts.

        This formats all previous refinement requirements in a clear, numbered format
        to ensure the LLM understands all cumulative requirements.

        Returns:
            Formatted string of all refinement requirements
        """
        if not self.state.cumulative_refinement_requirements:
            return "No previous refinements."

        formatted_items = []
        for i, requirement in enumerate(self.state.cumulative_refinement_requirements, 1):
            formatted_items.append(f"{i}. {requirement}")

        return "\n".join(formatted_items)

    def _change_phase(self, new_phase: WorkflowPhase):
        """Change workflow phase and trigger callback."""
        old_phase = self.state.phase
        self.state.phase = new_phase

        logger.info(f"Workflow phase: {old_phase.value} → {new_phase.value}")

        if self.on_phase_change:
            self.on_phase_change(new_phase)

    def _persist_state(self):
        """Persist current workflow state to disk."""
        try:
            self.state.save_to_file(str(self.state_file_path))
        except Exception as e:
            logger.warning(f"Failed to persist state: {str(e)}")

    def get_state(self) -> Dict[str, Any]:
        """Get current workflow state."""
        return self.state.to_dict()

    def is_plan_ready(self) -> bool:
        """Check if business logic plan is ready for approval."""
        return self.state.phase == WorkflowPhase.PLAN_REVIEW and self.state.business_logic_plan is not None

    def is_output_ready(self) -> bool:
        """Check if output is ready for review."""
        return self.state.phase == WorkflowPhase.OUTPUT_REVIEW and self.state.output_file_path is not None

    def is_completed(self) -> bool:
        """Check if workflow is completed successfully."""
        return self.state.phase == WorkflowPhase.COMPLETED

    def is_failed(self) -> bool:
        """Check if workflow has failed."""
        return self.state.phase == WorkflowPhase.FAILED

    def get_planner_summary(self) -> Dict[str, Any]:
        """Get summary of planning phase."""
        if not self.planner:
            return {}

        return {
            "questions_asked": self.state.planner_questions_asked,
            "max_questions": self.max_planner_questions,
            "conversation_history": self.state.planner_conversation_history,
            "business_logic_plan": self.state.business_logic_plan,
            "plan_approved": self.state.plan_approved
        }

    def get_coder_summary(self) -> Dict[str, Any]:
        """Get summary of coding phase."""
        return {
            "iterations": self.state.code_execution_iterations,
            "max_iterations": self.max_coder_iterations,
            "generated_code": self.state.generated_code,
            "output_path": self.state.output_file_path,
            "execution_result": self.state.code_execution_result
        }

    def get_output_review_summary(self) -> Dict[str, Any]:
        """Get summary of output review phase."""
        return {
            "output_approved": self.state.output_approved,
            "refinement_iterations": self.state.output_refinement_iterations,
            "feedback_history": self.state.output_feedback_history,
            "output_path": self.state.output_file_path
        }

    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get complete workflow summary."""
        return {
            "workflow_name": self.workflow_name,
            "workflow_description": self.workflow_description,
            "phase": self.state.phase.value,
            "started_at": self.state.started_at.isoformat() if self.state.started_at else None,
            "completed_at": self.state.completed_at.isoformat() if self.state.completed_at else None,
            "current_question": self.state.current_question,
            "is_successful": self.state.is_successful,
            "error_message": self.state.error_message,
            "planner_summary": self.get_planner_summary(),
            "coder_summary": self.get_coder_summary(),
            "output_review_summary": self.get_output_review_summary(),
            # Analysis report fields
            "analysis_instructions": self.state.analysis_instructions,
            "analysis_instructions_approved": self.state.analysis_instructions_approved,
            "analysis_plan": self.state.analysis_plan,
            "analysis_code": self.state.analysis_code,
            "analysis_report_file_path": self.state.analysis_report_file_path,
            "analysis_report_content": self.state.analysis_report_content,
            "analysis_report_approved": self.state.analysis_report_approved,
            "analysis_refinement_iterations": self.state.analysis_refinement_iterations
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_orchestrator(
    workflow_name: str,
    workflow_description: str,
    csv_filepaths: List[str],
    output_filename: str = "result.csv",
    model: Optional[str] = None,
    **kwargs
) -> IRAOrchestrator:
    """
    Create and configure an IRA Orchestrator.

    Args:
        workflow_name: Name of the workflow
        workflow_description: Description of workflow goals
        csv_filepaths: List of CSV file paths
        output_filename: Name for output file
        model: Model to use (or None to use provider default from config)
        **kwargs: Additional orchestrator configuration

    Returns:
        Configured IRAOrchestrator instance

    Example:
        >>> # Use provider default model
        >>> orchestrator = create_orchestrator(
        ...     workflow_name="Sales Analysis",
        ...     workflow_description="Analyze Q4 sales data",
        ...     csv_filepaths=["data/sales.csv"]
        ... )

        >>> # Or specify a model explicitly
        >>> orchestrator = create_orchestrator(
        ...     workflow_name="Sales Analysis",
        ...     workflow_description="Analyze Q4 sales data",
        ...     csv_filepaths=["data/sales.csv"],
        ...     model="gpt-4o"  # For OpenAI
        ... )

        >>> await orchestrator.start()
    """
    return IRAOrchestrator(
        workflow_name=workflow_name,
        workflow_description=workflow_description,
        csv_filepaths=csv_filepaths,
        output_filename=output_filename,
        model=model,
        **kwargs
    )
