"""
WebSocket routes for real-time workflow updates.

This module provides WebSocket connections for streaming real-time updates
during code generation and execution.
"""

import asyncio
import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

from backend.api.services.workflow_manager import get_workflow_manager
from backend.api.models.responses import WebSocketEvent
from ai.ira_builder.utils.logger import get_logger
from ai.ira_builder.orchestrator import WorkflowPhase

logger = get_logger(__name__)

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections for workflows.

    Handles:
    - Active WebSocket connections per workflow
    - Broadcasting messages to connected clients
    - Connection lifecycle management
    """

    def __init__(self):
        # Map of workflow_id to set of active WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, workflow_id: str):
        """Accept a new WebSocket connection for a workflow."""
        await websocket.accept()

        if workflow_id not in self.active_connections:
            self.active_connections[workflow_id] = set()

        self.active_connections[workflow_id].add(websocket)
        logger.info(f"WebSocket connected for workflow: {workflow_id} (total: {len(self.active_connections[workflow_id])})")

    def disconnect(self, websocket: WebSocket, workflow_id: str):
        """Remove a WebSocket connection."""
        if workflow_id in self.active_connections:
            self.active_connections[workflow_id].discard(websocket)

            if len(self.active_connections[workflow_id]) == 0:
                del self.active_connections[workflow_id]

        logger.info(f"WebSocket disconnected for workflow: {workflow_id}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")

    async def broadcast(self, workflow_id: str, event: WebSocketEvent):
        """
        Broadcast an event to all connected clients for a workflow.

        Args:
            workflow_id: Workflow identifier
            event: WebSocket event to broadcast
        """
        if workflow_id not in self.active_connections:
            return

        # Convert event to JSON
        message = event.model_dump_json()

        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections[workflow_id]:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {str(e)}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, workflow_id)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/workflows/{workflow_id}")
async def workflow_websocket(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for real-time workflow updates.

    Provides:
    - Phase change notifications
    - Progress updates during code generation
    - Log streaming
    - Error notifications
    - Completion events

    Example client usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/workflows/my_workflow_id');

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Event:', data.event_type, data.data);
    };
    ```
    """
    await manager.connect(websocket, workflow_id)

    try:
        # Verify workflow exists
        workflow_manager = get_workflow_manager()
        orchestrator = await workflow_manager.get_orchestrator(workflow_id)

        if not orchestrator:
            await manager.send_personal_message(
                json.dumps({
                    "event_type": "error",
                    "workflow_id": workflow_id,
                    "data": {"error": "Workflow not found"},
                    "timestamp": datetime.now().isoformat()
                }),
                websocket
            )
            await websocket.close()
            return

        # Send initial connection success message
        await manager.send_personal_message(
            json.dumps({
                "event_type": "connected",
                "workflow_id": workflow_id,
                "data": {
                    "phase": orchestrator.state.phase.value,
                    "workflow_name": orchestrator.workflow_name
                },
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )

        # Set up callbacks for orchestrator events
        original_phase_change = orchestrator.on_phase_change
        original_planner_response = orchestrator.on_planner_response
        original_coder_progress = orchestrator.on_coder_progress

        async def phase_change_handler(new_phase: WorkflowPhase):
            """Handle phase change events."""
            event = WebSocketEvent(
                event_type="phase_change",
                workflow_id=workflow_id,
                data={
                    "phase": new_phase.value,
                    "timestamp": datetime.now().isoformat()
                }
            )
            await manager.broadcast(workflow_id, event)

            if original_phase_change:
                original_phase_change(new_phase)

        async def planner_response_handler(response: str, response_type: str):
            """Handle planner response events."""
            event = WebSocketEvent(
                event_type="planner_response",
                workflow_id=workflow_id,
                data={
                    "response": response[:500],  # Truncate for WebSocket
                    "response_type": response_type,
                    "timestamp": datetime.now().isoformat()
                }
            )
            await manager.broadcast(workflow_id, event)

            if original_planner_response:
                original_planner_response(response, response_type)

        async def coder_progress_handler(current: int, total: int):
            """Handle coder progress events."""
            event = WebSocketEvent(
                event_type="progress",
                workflow_id=workflow_id,
                data={
                    "current": current,
                    "total": total,
                    "percentage": int((current / total) * 100) if total > 0 else 0,
                    "timestamp": datetime.now().isoformat()
                }
            )
            await manager.broadcast(workflow_id, event)

            if original_coder_progress:
                original_coder_progress(current, total)

        # Register handlers
        orchestrator.on_phase_change = phase_change_handler
        orchestrator.on_planner_response = planner_response_handler
        orchestrator.on_coder_progress = coder_progress_handler

        # Keep connection alive and listen for messages
        while True:
            try:
                # Wait for messages from client (e.g., ping/pong)
                data = await websocket.receive_text()

                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")

                # Handle status request
                elif data == "status":
                    await manager.send_personal_message(
                        json.dumps({
                            "event_type": "status",
                            "workflow_id": workflow_id,
                            "data": {
                                "phase": orchestrator.state.phase.value,
                                "questions_asked": orchestrator.state.planner_questions_asked,
                                "plan_approved": orchestrator.state.plan_approved,
                                "output_approved": orchestrator.state.output_approved,
                                "is_successful": orchestrator.state.is_successful,
                                "error_message": orchestrator.state.error_message
                            },
                            "timestamp": datetime.now().isoformat()
                        }),
                        websocket
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {str(e)}")
                break

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        try:
            await manager.send_personal_message(
                json.dumps({
                    "event_type": "error",
                    "workflow_id": workflow_id,
                    "data": {"error": str(e)},
                    "timestamp": datetime.now().isoformat()
                }),
                websocket
            )
        except:
            pass

    finally:
        manager.disconnect(websocket, workflow_id)


@router.websocket("/workflows/{workflow_id}/logs")
async def workflow_logs_websocket(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for streaming workflow execution logs.

    Provides real-time log streaming during code generation and execution.

    Example client usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/workflows/my_workflow_id/logs');

    ws.onmessage = (event) => {
        const log = JSON.parse(event.data);
        console.log(`[${log.level}] ${log.message}`);
    };
    ```
    """
    await manager.connect(websocket, f"{workflow_id}_logs")

    try:
        # Verify workflow exists
        workflow_manager = get_workflow_manager()
        orchestrator = await workflow_manager.get_orchestrator(workflow_id)

        if not orchestrator:
            await manager.send_personal_message(
                json.dumps({"error": "Workflow not found"}),
                websocket
            )
            await websocket.close()
            return

        # Send connection confirmation
        await manager.send_personal_message(
            json.dumps({
                "level": "INFO",
                "message": f"Connected to logs for workflow: {orchestrator.workflow_name}",
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )

        # TODO: Implement log streaming from orchestrator/agents
        # For now, just keep the connection alive
        while True:
            try:
                data = await websocket.receive_text()

                if data == "ping":
                    await websocket.send_text("pong")

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in logs WebSocket: {str(e)}")
                break

    except Exception as e:
        logger.error(f"Logs WebSocket error: {str(e)}", exc_info=True)

    finally:
        manager.disconnect(websocket, f"{workflow_id}_logs")


# Utility function to broadcast events from anywhere in the codebase
async def broadcast_event(workflow_id: str, event_type: str, data: dict):
    """
    Broadcast a custom event to all connected clients.

    Args:
        workflow_id: Workflow identifier
        event_type: Type of event
        data: Event data dictionary
    """
    event = WebSocketEvent(
        event_type=event_type,
        workflow_id=workflow_id,
        data=data
    )
    await manager.broadcast(workflow_id, event)
