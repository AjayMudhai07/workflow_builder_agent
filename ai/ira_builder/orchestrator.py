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
        model: str = "gpt-5",
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
            model: OpenAI model to use for both agents
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
        self.model = model

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
            # Create Planner Agent
            self.planner = create_planner_agent(
                model=self.model,
                temperature=0.7,
                max_questions=self.max_planner_questions
            )

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

    async def approve_output_and_complete(self) -> Dict[str, Any]:
        """
        Approve the output and complete the workflow.

        This transitions from OUTPUT_REVIEW to COMPLETED phase.

        Returns:
            Dictionary with completion status
        """
        if self.state.phase != WorkflowPhase.OUTPUT_REVIEW:
            return {
                "status": "error",
                "error": "Can only approve output in OUTPUT_REVIEW phase"
            }

        try:
            logger.info("=" * 80)
            logger.info("OUTPUT APPROVED - WORKFLOW COMPLETED")
            logger.info("=" * 80)

            self.state.output_approved = True
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
                "execution_time": execution_time,
                "is_successful": True
            }

        except Exception as e:
            logger.error(f"Error completing workflow: {str(e)}", exc_info=True)
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

            # Create Coder Agent
            self.coder = create_coder_agent(
                model=self.model,
                temperature=0.3,
                max_iterations=self.max_coder_iterations,
                execution_timeout=self.code_execution_timeout
            )

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
            "output_review_summary": self.get_output_review_summary()
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_orchestrator(
    workflow_name: str,
    workflow_description: str,
    csv_filepaths: List[str],
    output_filename: str = "result.csv",
    model: str = "gpt-5",
    **kwargs
) -> IRAOrchestrator:
    """
    Create and configure an IRA Orchestrator.

    Args:
        workflow_name: Name of the workflow
        workflow_description: Description of workflow goals
        csv_filepaths: List of CSV file paths
        output_filename: Name for output file
        model: OpenAI model to use
        **kwargs: Additional orchestrator configuration

    Returns:
        Configured IRAOrchestrator instance

    Example:
        >>> orchestrator = create_orchestrator(
        ...     workflow_name="Sales Analysis",
        ...     workflow_description="Analyze Q4 sales data",
        ...     csv_filepaths=["data/sales.csv"],
        ...     model="gpt-5"
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
