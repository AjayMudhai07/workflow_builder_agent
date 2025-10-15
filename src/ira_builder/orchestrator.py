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

from ira_builder.agents.planner import (
    create_planner_agent,
    PlannerAgent,
    PlannerResponseType
)
from ira_builder.agents.coder import create_coder_agent, CoderAgent
from ira_builder.utils.logger import get_logger
from ira_builder.utils.config import get_config

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
            "business_logic_plan": self.business_logic_plan,
            "plan_approved": self.plan_approved,
            "generated_code": self.generated_code,
            "code_execution_iterations": self.code_execution_iterations,
            "output_file_path": self.output_file_path,
            "output_approved": self.output_approved,
            "output_refinement_iterations": self.output_refinement_iterations,
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
        state.business_logic_plan = data.get("business_logic_plan")
        state.plan_approved = data.get("plan_approved", False)
        state.generated_code = data.get("generated_code")
        state.code_execution_iterations = data.get("code_execution_iterations", 0)
        state.output_file_path = data.get("output_file_path")
        state.output_approved = data.get("output_approved", False)
        state.output_refinement_iterations = data.get("output_refinement_iterations", 0)
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
        model: str = "gpt-4o",
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

        # Sanitize workflow name for file path
        safe_workflow_name = sanitize_filename(workflow_name)
        self.state_file_path = self.state_dir / f"{safe_workflow_name}_state.json"

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

            # Get next response from Planner
            response = await self.planner.ask_question(user_input)

            # Record Planner response
            self.state.planner_conversation_history.append({
                "role": "assistant",
                "content": str(response),
                "timestamp": datetime.now().isoformat()
            })

            # Detect response type
            response_type = self.planner._detect_response_type(str(response))

            # Check if this is a Business Logic Plan
            if response_type == PlannerResponseType.BUSINESS_LOGIC_PLAN:
                logger.info("Business Logic Plan generated!")
                self.state.business_logic_plan = str(response)
                self._change_phase(WorkflowPhase.PLAN_REVIEW)

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
        Refine the output based on user feedback.

        This allows the user to request changes to the generated output.
        The Coder Agent will modify the code based on feedback and regenerate.

        Args:
            feedback: User's feedback describing what needs to be changed
            max_refinement_iterations: Maximum refinement attempts (default: 3)

        Returns:
            Dictionary with new output and code
        """
        if self.state.phase != WorkflowPhase.OUTPUT_REVIEW:
            return {
                "status": "error",
                "error": "Can only refine output in OUTPUT_REVIEW phase"
            }

        if not self.coder:
            return {
                "status": "error",
                "error": "Coder not initialized"
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

            # Record feedback
            self.state.output_feedback_history.append({
                "timestamp": datetime.now().isoformat(),
                "feedback": feedback,
                "iteration": self.state.output_refinement_iterations + 1
            })
            self.state.output_refinement_iterations += 1

            # Transition back to CODING phase temporarily
            self._change_phase(WorkflowPhase.CODING)

            # Request code refinement from Coder Agent
            refinement_prompt = f"""
The user reviewed the output and provided the following feedback:

{feedback}

Please modify the code to address this feedback. Generate COMPLETE corrected code that:
1. Addresses the user's feedback
2. Maintains all existing functionality that was working
3. Follows the same structure and IRA preprocessing
4. Saves output to the same path

Provide the COMPLETE updated code.
"""

            # Get refined code from Coder
            response = await self.coder.agent.run(refinement_prompt, thread=self.coder.thread)

            # Extract and execute refined code
            from ira_builder.tools.code_executor_tools import extract_code_from_markdown
            refined_code = extract_code_from_markdown(response.text)

            logger.info(f"Generated refined code: {len(refined_code)} characters")

            # Execute the refined code
            exec_result = await self.coder._execute_code(refined_code)

            if exec_result['status'] == 'success':
                logger.info("✅ REFINED CODE EXECUTED SUCCESSFULLY!")

                # Validate output
                from ira_builder.tools.code_executor_tools import (
                    validate_output_dataframe,
                    preview_dataframe,
                    get_dataframe_summary
                )

                output_validation = validate_output_dataframe(self.state.output_file_path)

                if output_validation['valid']:
                    # Update state with refined code
                    self.state.generated_code = refined_code
                    self.state.code_execution_result = exec_result

                    # Save refined code
                    code_filepath = self._save_generated_code(refined_code)

                    # Get new preview and summary
                    preview = preview_dataframe(self.state.output_file_path, rows=10)
                    summary = get_dataframe_summary(self.state.output_file_path)

                    # Transition back to OUTPUT_REVIEW
                    self._change_phase(WorkflowPhase.OUTPUT_REVIEW)
                    self._persist_state()

                    logger.info(f"Output refined successfully")

                    return {
                        "status": "success",
                        "phase": self.state.phase.value,
                        "code": refined_code,
                        "code_filepath": str(code_filepath),
                        "output_path": self.state.output_file_path,
                        "output_preview": preview,
                        "output_summary": summary,
                        "refinement_iteration": self.state.output_refinement_iterations
                    }
                else:
                    logger.warning(f"Output validation failed after refinement: {output_validation['error']}")
                    self._change_phase(WorkflowPhase.OUTPUT_REVIEW)
                    self._persist_state()

                    return {
                        "status": "error",
                        "phase": self.state.phase.value,
                        "error": f"Output validation failed: {output_validation['error']}",
                        "refinement_iteration": self.state.output_refinement_iterations
                    }
            else:
                logger.error(f"Refined code execution failed: {exec_result['error_message']}")
                self._change_phase(WorkflowPhase.OUTPUT_REVIEW)
                self._persist_state()

                return {
                    "status": "error",
                    "phase": self.state.phase.value,
                    "error": f"Code execution failed: {exec_result['error_message']}",
                    "refinement_iteration": self.state.output_refinement_iterations
                }

        except Exception as e:
            logger.error(f"Error refining output: {str(e)}", exc_info=True)
            self._change_phase(WorkflowPhase.OUTPUT_REVIEW)
            self._persist_state()

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
    model: str = "gpt-4o",
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
        ...     model="gpt-4o"
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
