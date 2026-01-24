"""Shared utility functions for data cleaning operations."""

import re
from pathlib import Path
from typing import List, Optional


def to_snake_case(name: str) -> str:
    """
    Convert a string to snake_case.

    Handles:
    - CamelCase: "FirstName" -> "first_name"
    - Spaces: "First Name" -> "first_name"
    - Multiple spaces/underscores: "first  name" -> "first_name"
    - Special characters: "First-Name" -> "first_name"
    - Mixed: "firstName lastName" -> "first_name_last_name"

    Args:
        name: The string to convert

    Returns:
        The snake_case version of the string
    """
    if not name:
        return ""

    # Replace special characters and spaces with underscores
    s = re.sub(r'[^\w\s]', '_', str(name))

    # Insert underscore before uppercase letters (for CamelCase)
    s = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s)

    # Replace spaces with underscores
    s = re.sub(r'\s+', '_', s)

    # Collapse multiple underscores
    s = re.sub(r'_+', '_', s)

    # Remove leading/trailing underscores and lowercase
    return s.strip('_').lower()


def ensure_output_dir(output_path: Optional[str] = None) -> Path:
    """
    Ensure the output directory exists and return its path.

    Args:
        output_path: Optional custom output path. Defaults to './output/'

    Returns:
        Path object for the output directory
    """
    if output_path:
        path = Path(output_path)
    else:
        path = Path("./output")

    path.mkdir(parents=True, exist_ok=True)
    return path


def format_row_numbers(row_numbers: List[int]) -> str:
    """
    Format a list of row numbers into a human-readable string with ranges.

    Examples:
        [1, 2, 3, 5, 7, 8, 9] -> "1-3, 5, 7-9"
        [1] -> "1"
        [1, 3, 5] -> "1, 3, 5"
        [] -> ""

    Args:
        row_numbers: List of 1-indexed row numbers

    Returns:
        Formatted string with ranges collapsed
    """
    if not row_numbers:
        return ""

    # Sort and deduplicate
    sorted_nums = sorted(set(row_numbers))

    if len(sorted_nums) == 1:
        return str(sorted_nums[0])

    ranges = []
    range_start = sorted_nums[0]
    range_end = sorted_nums[0]

    for num in sorted_nums[1:]:
        if num == range_end + 1:
            # Extend the current range
            range_end = num
        else:
            # End current range and start new one
            if range_start == range_end:
                ranges.append(str(range_start))
            else:
                ranges.append(f"{range_start}-{range_end}")
            range_start = num
            range_end = num

    # Add the last range
    if range_start == range_end:
        ranges.append(str(range_start))
    else:
        ranges.append(f"{range_start}-{range_end}")

    return ", ".join(ranges)


def truncate_string(s: str, max_length: int = 50) -> str:
    """
    Truncate a string to a maximum length, adding ellipsis if needed.

    Args:
        s: The string to truncate
        max_length: Maximum length (default 50)

    Returns:
        Truncated string with "..." if it was shortened
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - 3] + "..."


def get_file_extension(filepath: str) -> str:
    """
    Get the lowercase file extension from a filepath.

    Args:
        filepath: Path to the file

    Returns:
        Lowercase extension without the dot (e.g., "csv", "xlsx")
    """
    return Path(filepath).suffix.lower().lstrip('.')
