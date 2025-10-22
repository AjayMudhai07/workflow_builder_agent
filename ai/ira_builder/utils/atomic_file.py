"""
Atomic file writing utilities for safe concurrent file operations.

This module provides utilities for writing files atomically to prevent
corruption from concurrent access by multiple processes/threads.
"""

import os
import tempfile
import json
from typing import Any, Dict
from pathlib import Path
import fcntl
from contextlib import contextmanager

from .logger import get_logger

logger = get_logger(__name__)


def atomic_write_json(filepath: str, data: Dict[str, Any], indent: int = 2):
    """
    Write JSON data to a file atomically.

    This function ensures that the file write operation is atomic by:
    1. Writing to a temporary file in the same directory
    2. Using os.replace() which is atomic on POSIX systems
    3. Cleaning up the temp file on error

    Args:
        filepath: Target file path
        data: Dictionary to serialize as JSON
        indent: JSON indentation level

    Raises:
        IOError: If write operation fails
        json.JSONDecodeError: If data cannot be serialized
    """
    filepath = Path(filepath)
    parent_dir = filepath.parent

    # Ensure parent directory exists
    parent_dir.mkdir(parents=True, exist_ok=True)

    # Create temp file in same directory for atomic rename
    temp_fd = None
    temp_path = None

    try:
        # Create temporary file in same directory (required for atomic rename)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=str(parent_dir),
            prefix=f".{filepath.name}.",
            suffix=".tmp"
        )

        # Write JSON data to temp file
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(data, f, indent=indent)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk

        temp_fd = None  # File descriptor is closed by fdopen context manager

        # Atomic rename - replaces target file atomically
        # On POSIX systems, this is guaranteed to be atomic
        os.replace(temp_path, str(filepath))

        logger.debug(f"Atomically wrote JSON to {filepath}")

    except Exception as e:
        logger.error(f"Failed to write JSON to {filepath}: {str(e)}")
        # Clean up temp file on error
        if temp_fd is not None:
            try:
                os.close(temp_fd)
            except:
                pass
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass
        raise


@contextmanager
def file_lock(filepath: str, timeout: float = 30.0):
    """
    Context manager for file-based locking using fcntl.

    This provides an advisory lock on a file to coordinate access
    between multiple processes.

    Args:
        filepath: Path to the lock file
        timeout: Maximum time to wait for lock (seconds)

    Yields:
        File descriptor for the lock file

    Example:
        >>> with file_lock("/tmp/mylock"):
        ...     # Critical section
        ...     do_something()
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    lock_fd = None
    try:
        # Open lock file (create if doesn't exist)
        lock_fd = os.open(str(filepath), os.O_RDWR | os.O_CREAT, 0o666)

        # Try to acquire exclusive lock
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.debug(f"Acquired file lock: {filepath}")
        except IOError:
            # Lock is held by another process, wait with timeout
            logger.debug(f"Waiting for file lock: {filepath}")
            import time
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    logger.debug(f"Acquired file lock after wait: {filepath}")
                    break
                except IOError:
                    time.sleep(0.1)
            else:
                raise TimeoutError(f"Failed to acquire lock on {filepath} within {timeout}s")

        yield lock_fd

    finally:
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)
                logger.debug(f"Released file lock: {filepath}")
            except Exception as e:
                logger.warning(f"Error releasing lock on {filepath}: {str(e)}")


def read_json_with_retry(filepath: str, max_retries: int = 3, retry_delay: float = 0.1) -> Dict[str, Any]:
    """
    Read JSON file with retry logic for handling concurrent access.

    Args:
        filepath: Path to JSON file
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries (seconds)

    Returns:
        Parsed JSON data as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist after retries
        json.JSONDecodeError: If file contains invalid JSON after retries
        IOError: If file cannot be read after retries
    """
    import time

    last_error = None
    for attempt in range(max_retries):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            # File might be partially written, retry
            last_error = e
            if attempt < max_retries - 1:
                logger.debug(f"JSON decode error on attempt {attempt + 1}/{max_retries}: {filepath}")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to read JSON after {max_retries} attempts: {filepath}")
                raise
        except IOError as e:
            last_error = e
            if attempt < max_retries - 1:
                logger.debug(f"IO error on attempt {attempt + 1}/{max_retries}: {filepath}")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to read file after {max_retries} attempts: {filepath}")
                raise

    # Should never reach here, but just in case
    raise last_error
