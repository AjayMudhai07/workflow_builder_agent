"""
Helper utilities for IRA Workflow Builder.

General-purpose utility functions used across the application.
"""

import uuid
from datetime import datetime
from pathlib import Path
import re
from typing import Optional


def generate_workflow_id() -> str:
    """
    Generate a unique workflow ID.

    Returns:
        Unique workflow ID string

    Example:
        >>> workflow_id = generate_workflow_id()
        >>> print(workflow_id)
        'wf_8f7e6d5c4b3a'
    """
    return f"wf_{uuid.uuid4().hex[:12]}"


def format_timestamp(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime object as string.

    Args:
        dt: Datetime object (default: now)
        format_str: Format string for strftime

    Returns:
        Formatted timestamp string

    Example:
        >>> timestamp = format_timestamp()
        >>> print(timestamp)
        '2025-10-15 14:30:45'
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to be filesystem-safe.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename

    Example:
        >>> safe_name = sanitize_filename("My File (v2).csv")
        >>> print(safe_name)
        'my_file_v2.csv'
    """
    # Convert to lowercase
    filename = filename.lower()

    # Replace spaces and special characters with underscores
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'[\s]+', '_', filename)

    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)

    # Remove leading/trailing underscores
    filename = filename.strip('_')

    return filename


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")

    Example:
        >>> size = format_file_size(1536000)
        >>> print(size)
        '1.46 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated string

    Example:
        >>> text = truncate_string("This is a very long text...", max_length=20)
        >>> print(text)
        'This is a very lo...'
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def parse_csv_list(value: str) -> list:
    """
    Parse a comma-separated string into a list.

    Args:
        value: Comma-separated string

    Returns:
        List of values

    Example:
        >>> items = parse_csv_list("apple, banana, orange")
        >>> print(items)
        ['apple', 'banana', 'orange']
    """
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def ensure_directory(path: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Path object

    Example:
        >>> dir_path = ensure_directory("data/uploads")
        >>> print(dir_path.exists())
        True
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
