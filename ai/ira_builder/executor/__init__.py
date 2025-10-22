"""
Python Script Executor Module

A secure, feature-rich Python code execution environment for workflow systems.
Based on Microsoft AutoGen's LocalCommandLineCodeExecutor with enhancements.
"""

from .executor import PythonScriptExecutor
from .core.base import CodeBlock, CodeResult
from .core.common import CommandLineCodeResult

__version__ = "1.0.0"
__author__ = "Ajay Mudhai"

# Main exports for external usage
__all__ = [
    # Core executor
    "PythonScriptExecutor",

    # Data structures
    "CodeBlock",
    "CodeResult",
    "CommandLineCodeResult",
]

# Module metadata
MODULE_INFO = {
    "name": "python_executor",
    "description": "Python script execution with timeout, error handling, and security features",
    "node_type": "python_script_executor",
    "category": "execution",
    "supports": ["python", "py"],
    "features": [
        "timeout_control",
        "workspace_isolation", 
        "function_dependencies",
        "package_installation",
        "error_extraction"
    ]
}