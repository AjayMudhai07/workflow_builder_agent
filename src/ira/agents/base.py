"""
Base agent utilities and helper functions.

This module provides common utilities used across all agent implementations.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime

from ira.utils.logger import get_logger

logger = get_logger(__name__)


class AgentRole(Enum):
    """Enumeration of agent roles in the system."""

    PLANNER = "planner"
    CODER = "coder"
    REVIEWER = "reviewer"
    ORCHESTRATOR = "orchestrator"


class ConversationMessage:
    """Represents a message in agent conversation history."""

    def __init__(
        self,
        role: str,
        content: str,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a conversation message.

        Args:
            role: Role of the message sender (user, assistant, system)
            content: Message content
            timestamp: When the message was created
            metadata: Additional metadata
        """
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        """Create message from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


def format_agent_response(
    content: str,
    agent_name: str = "IRA",
    include_timestamp: bool = False
) -> str:
    """
    Format an agent response with consistent styling.

    Args:
        content: Response content
        agent_name: Name of the agent
        include_timestamp: Whether to include timestamp

    Returns:
        Formatted response string

    Example:
        >>> response = format_agent_response("Hello!", "IRA-Planner")
        >>> print(response)
        [IRA-Planner]: Hello!
    """
    header = f"[{agent_name}]"

    if include_timestamp:
        timestamp = datetime.now().strftime("%H:%M:%S")
        header = f"{header} ({timestamp})"

    return f"{header}: {content}"


def extract_code_blocks(text: str, language: str = "python") -> List[str]:
    """
    Extract code blocks from markdown text.

    Args:
        text: Markdown text containing code blocks
        language: Programming language to extract (default: python)

    Returns:
        List of code block contents

    Example:
        >>> text = "Here's code:\\n```python\\nprint('hi')\\n```"
        >>> blocks = extract_code_blocks(text)
        >>> print(blocks[0])
        print('hi')
    """
    import re

    # Pattern to match code blocks with optional language specifier
    pattern = rf"```{language}?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)

    return [match.strip() for match in matches]


def truncate_conversation_history(
    history: List[Dict[str, Any]],
    max_messages: int = 20,
    keep_system: bool = True
) -> List[Dict[str, Any]]:
    """
    Truncate conversation history to last N messages.

    Args:
        history: Full conversation history
        max_messages: Maximum number of messages to keep
        keep_system: Whether to always keep system messages

    Returns:
        Truncated conversation history

    Example:
        >>> history = [{"role": "user", "content": "hi"}] * 30
        >>> truncated = truncate_conversation_history(history, max_messages=10)
        >>> len(truncated)
        10
    """
    if len(history) <= max_messages:
        return history

    if keep_system:
        # Keep system messages and last N non-system messages
        system_messages = [msg for msg in history if msg.get("role") == "system"]
        other_messages = [msg for msg in history if msg.get("role") != "system"]

        # Take last N-len(system) other messages
        keep_count = max_messages - len(system_messages)
        other_messages = other_messages[-keep_count:] if keep_count > 0 else []

        return system_messages + other_messages
    else:
        # Simply take last N messages
        return history[-max_messages:]


def calculate_token_estimate(text: str) -> int:
    """
    Estimate token count for text (rough approximation).

    Args:
        text: Input text

    Returns:
        Estimated token count

    Note:
        This is a rough estimate. Use actual tokenizer for precise counts.

    Example:
        >>> text = "Hello world"
        >>> tokens = calculate_token_estimate(text)
        >>> print(tokens)
        3
    """
    # Rough estimate: 1 token ≈ 4 characters for English text
    return len(text) // 4


def validate_agent_response(response: str, min_length: int = 10) -> bool:
    """
    Validate that an agent response is meaningful.

    Args:
        response: Agent response text
        min_length: Minimum required length

    Returns:
        True if response is valid

    Example:
        >>> validate_agent_response("Hi")
        False
        >>> validate_agent_response("Here is a detailed explanation...")
        True
    """
    if not response or not isinstance(response, str):
        return False

    if len(response.strip()) < min_length:
        return False

    # Check if response is not just whitespace or special characters
    if not any(c.isalnum() for c in response):
        return False

    return True


def merge_agent_contexts(
    *contexts: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Merge multiple agent context dictionaries.

    Later contexts override earlier ones for conflicting keys.

    Args:
        *contexts: Variable number of context dictionaries

    Returns:
        Merged context dictionary

    Example:
        >>> ctx1 = {"workflow_name": "Analysis", "step": 1}
        >>> ctx2 = {"step": 2, "status": "active"}
        >>> merged = merge_agent_contexts(ctx1, ctx2)
        >>> print(merged)
        {'workflow_name': 'Analysis', 'step': 2, 'status': 'active'}
    """
    merged = {}
    for context in contexts:
        if context:
            merged.update(context)
    return merged


class AgentMetrics:
    """Track metrics for agent performance."""

    def __init__(self):
        """Initialize metrics tracker."""
        self.start_time = datetime.now()
        self.message_count = 0
        self.tool_calls = 0
        self.errors = 0
        self.total_tokens = 0

    def record_message(self, token_count: int = 0):
        """Record a message exchange."""
        self.message_count += 1
        self.total_tokens += token_count

    def record_tool_call(self):
        """Record a tool call."""
        self.tool_calls += 1

    def record_error(self):
        """Record an error."""
        self.errors += 1

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        duration = (datetime.now() - self.start_time).total_seconds()

        return {
            "duration_seconds": round(duration, 2),
            "message_count": self.message_count,
            "tool_calls": self.tool_calls,
            "errors": self.errors,
            "total_tokens": self.total_tokens,
            "messages_per_minute": round((self.message_count / duration) * 60, 2) if duration > 0 else 0,
        }

    def reset(self):
        """Reset all metrics."""
        self.__init__()


def create_agent_context(
    workflow_id: str,
    workflow_name: str,
    workflow_description: str,
    csv_files: List[str],
    additional_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create standardized agent context dictionary.

    Args:
        workflow_id: Unique workflow identifier
        workflow_name: Name of the workflow
        workflow_description: Description of workflow goals
        csv_files: List of CSV file paths
        additional_context: Optional additional context

    Returns:
        Context dictionary for agent initialization

    Example:
        >>> context = create_agent_context(
        ...     "wf_123",
        ...     "Sales Analysis",
        ...     "Analyze Q4 sales",
        ...     ["sales.csv"]
        ... )
        >>> print(context["workflow_id"])
        wf_123
    """
    context = {
        "workflow_id": workflow_id,
        "workflow_name": workflow_name,
        "workflow_description": workflow_description,
        "csv_files": csv_files,
        "created_at": datetime.now().isoformat(),
    }

    if additional_context:
        context.update(additional_context)

    return context


def format_business_logic_for_display(logic_text: str) -> str:
    """
    Format business logic document for user-friendly display.

    Args:
        logic_text: Raw business logic markdown text

    Returns:
        Formatted text with improved readability

    Example:
        >>> logic = "# Business Logic\\n## Section 1\\nContent..."
        >>> formatted = format_business_logic_for_display(logic)
    """
    # Add extra spacing around headers
    formatted = logic_text.replace("\n# ", "\n\n# ")
    formatted = formatted.replace("\n## ", "\n\n## ")

    # Ensure proper spacing after lists
    formatted = formatted.replace("\n- ", "\n  - ")

    return formatted.strip()


def extract_requirements_from_logic(logic_text: str) -> List[str]:
    """
    Extract requirements section from business logic document.

    Args:
        logic_text: Business logic document text

    Returns:
        List of requirements

    Example:
        >>> logic = "## 3. Detailed Requirements\\n1. Req 1\\n2. Req 2"
        >>> reqs = extract_requirements_from_logic(logic)
        >>> len(reqs)
        2
    """
    import re

    # Find the requirements section
    pattern = r"## \d+\. Detailed Requirements\s*((?:\d+\..*\n?)+)"
    match = re.search(pattern, logic_text)

    if not match:
        return []

    requirements_text = match.group(1)

    # Extract individual requirements
    req_pattern = r"\d+\.\s*(.+?)(?=\n\d+\.|\Z)"
    requirements = re.findall(req_pattern, requirements_text, re.DOTALL)

    return [req.strip() for req in requirements]
