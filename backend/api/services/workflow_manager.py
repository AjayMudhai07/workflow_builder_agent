"""
Workflow Manager Service

This service manages workflow instances and provides an in-memory store
for active orchestrators with persistence to disk.
"""

import json
import asyncio
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from ai.ira_builder.orchestrator import IRAOrchestrator, WorkflowPhase, WorkflowState
from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.exceptions.errors import AgentException

logger = get_logger(__name__)


class WorkflowManager:
    """
    Manages workflow instances and provides access to orchestrators.

    This class maintains an in-memory store of active workflow orchestrators
    and handles loading/saving workflow state.
    """

    def __init__(self, storage_dir: str = "./storage/workflows", upload_dir: str = "./data/uploads"):
        """
        Initialize the workflow manager.

        Args:
            storage_dir: Directory to store workflow state files
            upload_dir: Directory to store uploaded CSV files
        """
        self.storage_dir = Path(storage_dir)
        self.upload_dir = Path(upload_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # In-memory store of active orchestrators
        self._orchestrators: Dict[str, IRAOrchestrator] = {}

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        logger.info(f"WorkflowManager initialized (storage: {storage_dir})")

    def _generate_workflow_id(self, workflow_name: str) -> str:
        """
        Generate a unique workflow ID using UUID.

        Args:
            workflow_name: Name of the workflow (not used, kept for compatibility)

        Returns:
            Unique UUID-based workflow ID
        """
        return str(uuid.uuid4())

    async def create_workflow(
        self,
        workflow_name: str,
        workflow_description: str,
        csv_files: List[Path],
        output_filename: str = "result.csv"
    ) -> tuple[str, IRAOrchestrator]:
        """
        Create a new workflow and initialize its orchestrator.

        Args:
            workflow_name: Name of the workflow
            workflow_description: Description of what the workflow should accomplish
            csv_files: List of paths to uploaded CSV files
            output_filename: Name for the output file

        Returns:
            Tuple of (workflow_id, orchestrator)
        """
        async with self._lock:
            # Generate workflow ID
            workflow_id = self._generate_workflow_id(workflow_name)

            # Create workflow-specific directory for uploads
            workflow_upload_dir = self.upload_dir / workflow_id
            workflow_upload_dir.mkdir(parents=True, exist_ok=True)

            # Move uploaded files to workflow directory
            csv_filepaths = []
            for csv_file in csv_files:
                destination = workflow_upload_dir / csv_file.name
                # Copy file to workflow directory
                import shutil
                shutil.copy(str(csv_file), str(destination))
                csv_filepaths.append(str(destination))

            logger.info(f"Created workflow: {workflow_id}")
            logger.info(f"CSV files: {csv_filepaths}")

            # Create orchestrator
            orchestrator = IRAOrchestrator(
                workflow_name=workflow_name,
                workflow_description=workflow_description,
                csv_filepaths=csv_filepaths,
                output_filename=output_filename,
                workflow_id=workflow_id,
                state_persistence_dir=str(self.storage_dir)
            )

            # Store in memory
            self._orchestrators[workflow_id] = orchestrator

            logger.info(f"Orchestrator created for workflow: {workflow_id}")

            return workflow_id, orchestrator

    async def get_orchestrator(self, workflow_id: str) -> Optional[IRAOrchestrator]:
        """
        Get an orchestrator by workflow ID.

        If the orchestrator is not in memory, attempts to load it from disk.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            IRAOrchestrator instance or None if not found
        """
        # Check in-memory store first
        if workflow_id in self._orchestrators:
            return self._orchestrators[workflow_id]

        # Try to load from disk
        async with self._lock:
            state_file = self.storage_dir / f"{workflow_id}_state.json"

            if not state_file.exists():
                logger.warning(f"Workflow not found: {workflow_id}")
                return None

            try:
                # Load workflow state
                state = WorkflowState.load_from_file(str(state_file))

                # Recreate orchestrator from state
                orchestrator = IRAOrchestrator(
                    workflow_name=state.workflow_name,
                    workflow_description=state.workflow_description,
                    csv_filepaths=state.csv_filepaths,
                    state_persistence_dir=str(self.storage_dir)
                )

                # Restore state
                orchestrator.state = state

                # Reinitialize agents if needed based on phase
                # Always initialize Planner if we have a business logic plan (needed for refinement)
                if state.phase in [WorkflowPhase.PLANNING, WorkflowPhase.PLAN_REVIEW] or state.business_logic_plan:
                    from ai.ira_builder.agents.planner import create_planner_agent
                    orchestrator.planner = create_planner_agent()
                    # Note: We can't perfectly restore the conversation thread,
                    # but the state has the conversation history

                if state.phase in [WorkflowPhase.CODING, WorkflowPhase.OUTPUT_REVIEW]:
                    from ai.ira_builder.agents.coder import create_coder_agent
                    from pathlib import Path
                    orchestrator.coder = create_coder_agent()
                    # Set the CSV file paths and output path on the coder agent's memory
                    orchestrator.coder.csv_filepaths = state.csv_filepaths
                    orchestrator.coder.memory.csv_filepaths = state.csv_filepaths
                    if state.output_file_path:
                        orchestrator.coder.memory.output_path = state.output_file_path
                    # Set business logic plan in coder's memory
                    if state.business_logic_plan:
                        orchestrator.coder.business_logic_plan = state.business_logic_plan
                        orchestrator.coder.memory.business_logic_plan = state.business_logic_plan
                    # Set the work directory
                    orchestrator.coder.workflow_name = state.workflow_name
                    orchestrator.coder.work_dir = Path("./data/outputs") / state.workflow_name.replace(" ", "_")
                    orchestrator.coder.work_dir.mkdir(parents=True, exist_ok=True)

                # Store in memory
                self._orchestrators[workflow_id] = orchestrator

                logger.info(f"Loaded workflow from disk: {workflow_id}")

                return orchestrator

            except Exception as e:
                logger.error(f"Error loading workflow {workflow_id}: {str(e)}")
                return None

    async def list_workflows(
        self,
        phase: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all workflows with optional filtering.

        Args:
            phase: Filter by workflow phase
            limit: Maximum number of workflows to return
            offset: Number of workflows to skip

        Returns:
            List of workflow summary dictionaries
        """
        workflows = []

        # Get all state files
        state_files = list(self.storage_dir.glob("*_state.json"))

        for state_file in state_files:
            try:
                with open(state_file, 'r') as f:
                    state_data = json.load(f)

                # Apply phase filter if specified
                if phase and state_data.get("phase") != phase:
                    continue

                # Extract workflow ID from filename
                workflow_id = state_file.stem.replace("_state", "")

                # Get CSV files count
                csv_files = state_data.get("csv_filepaths", [])

                workflows.append({
                    "workflow_id": workflow_id,
                    "name": state_data.get("workflow_name", ""),
                    "description": state_data.get("workflow_description", ""),
                    "phase": state_data.get("phase", "not_started"),
                    "created_at": state_data.get("started_at") or datetime.now().isoformat(),
                    "updated_at": state_data.get("completed_at") or state_data.get("started_at") or datetime.now().isoformat(),
                    "csv_files_count": len(csv_files),
                    "is_successful": state_data.get("is_successful", False),
                    "error_message": state_data.get("error_message")
                })

            except Exception as e:
                logger.warning(f"Error loading workflow state from {state_file}: {str(e)}")
                continue

        # Sort by created_at (most recent first)
        workflows.sort(key=lambda x: x["created_at"], reverse=True)

        # Apply pagination
        total = len(workflows)
        workflows = workflows[offset:offset + limit]

        return workflows

    async def get_workflow_detail(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a workflow.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            Detailed workflow information or None if not found
        """
        orchestrator = await self.get_orchestrator(workflow_id)

        if not orchestrator:
            return None

        return orchestrator.get_workflow_summary()

    async def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow and its associated files.

        Args:
            workflow_id: Unique workflow identifier

        Returns:
            True if deleted successfully, False otherwise
        """
        async with self._lock:
            try:
                # Remove from memory
                if workflow_id in self._orchestrators:
                    del self._orchestrators[workflow_id]

                # Delete state file
                state_file = self.storage_dir / f"{workflow_id}_state.json"
                if state_file.exists():
                    state_file.unlink()

                # Delete uploaded files
                workflow_upload_dir = self.upload_dir / workflow_id
                if workflow_upload_dir.exists():
                    import shutil
                    shutil.rmtree(str(workflow_upload_dir))

                logger.info(f"Deleted workflow: {workflow_id}")
                return True

            except Exception as e:
                logger.error(f"Error deleting workflow {workflow_id}: {str(e)}")
                return False


# Global workflow manager instance
_workflow_manager: Optional[WorkflowManager] = None


def get_workflow_manager() -> WorkflowManager:
    """
    Get the global workflow manager instance.

    Returns:
        WorkflowManager instance
    """
    global _workflow_manager

    if _workflow_manager is None:
        _workflow_manager = WorkflowManager()

    return _workflow_manager
