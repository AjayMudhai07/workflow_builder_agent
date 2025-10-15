"""
Simple cancellation token implementation for code execution.
Provides basic cancellation functionality without complex dependencies.
"""

import asyncio
from typing import Optional


class CancellationToken:
    """Simple cancellation token for stopping long-running operations."""
    
    def __init__(self):
        self._cancelled = False
        self._linked_tasks = []
    
    def cancel(self) -> None:
        """Cancel the operation and all linked tasks."""
        self._cancelled = True
        
        # Cancel all linked asyncio tasks
        for task in self._linked_tasks:
            if not task.done():
                task.cancel()
    
    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled
    
    def throw_if_cancellation_requested(self) -> None:
        """Raise CancelledError if cancellation has been requested."""
        if self._cancelled:
            raise asyncio.CancelledError("Operation was cancelled")
    
    def link_future(self, task: asyncio.Task) -> None:
        """Link an asyncio task to this cancellation token.
        
        When the token is cancelled, the linked task will also be cancelled.
        
        Args:
            task: The asyncio task to link to this cancellation token.
        """
        if task and not task.done():
            self._linked_tasks.append(task)
            
            # If already cancelled, cancel the task immediately
            if self._cancelled:
                task.cancel()
    
    def unlink_future(self, task: asyncio.Task) -> None:
        """Unlink a previously linked task."""
        if task in self._linked_tasks:
            self._linked_tasks.remove(task)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cancel on exit if needed."""
        # Could add auto-cancellation logic here if needed
        pass


# Factory function for convenience
def create_cancellation_token() -> CancellationToken:
    """Create a new cancellation token."""
    return CancellationToken()