from logging import root
from pathlib import Path
import os
from typing import Any
from tools.registry import register_tool

PROJECT_ROOT = Path(os.getcwd()).resolve()

def _is_safe_path(target_path: str | Path) -> bool:
    """
    Internal guardrail function. Checks if a given path is within the allowed project directory.
    This prevents path traversal attacks (e.g., moving outside the project structure).
    """
    p = Path(target_path).resolve()
    try:
        # Ensure it's relative to the project root and not the root itself being an ancestor of something external
        return p.is_relative_to(PROJECT_ROOT)
    except Exception:
        return False

IGNORED_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".DS_Store"}

def _should_ignore(path: Path) -> bool:
    """Helper to check if a path contains ignored directories like .venv, .git, etc."""
    for part in path.parts:
        if part in IGNORED_DIRS:
            return True
    return False


@register_tool
def read_file(path: str, offset: int = 1, limit: int = 200, raw: bool = True) -> str:
    """
    Read lines from a file, with optional offset and limit.

    Args:
        path (str): Path to the file to read.
        offset (int): The starting line number to read (1-indexed). Defaults to 1.
        limit (int): The maximum number of lines to read. Defaults to 200.
        raw (bool): If True, returns raw file content. If False, prepends line numbers to each line. Defaults to True.
    """
    if not _is_safe_path(path):
        return "Error: Access denied. Attempted access outside the authorized project directory."

    p = Path(path)
    if not p.exists() or not p.is_file(): # Check if it exists AND is a file
        return f"Error: File not found: {path}"
    
    # Proceed with reading only after safety check and existence confirmation
    try:
        # Read all lines first for offset/limit logic
        lines = p.read_text(errors="replace").splitlines()
        
        if offset <= 0:
            return "Error: Offset must be 1 or greater."

        selected = lines[offset - 1: offset - 1 + limit]
        
        if raw:
            return "\n".join(selected)
        else:
            # Format: line_number: content
            return "\n".join(f"{offset + i}: {line}" for i, line in enumerate(selected))
    except Exception as e:
        return f"Error reading file '{path}': {e}"


@register_tool
def write_file(path: str, content: str) -> str:
    """
    Writes the provided content string to a specified file.

    Args:
        path (str): Path to the file where content should be written.
        content (str): The content string to write to the file.
    """
    # Prevent writing outside the project boundary
    if not _is_safe_path(path):
        return "Error: Access denied. Attempted creation/writing outside the authorized project directory."

    p = Path(path)
    try:
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: File '{path}' has been created and written successfully."
    except IOError as e:
        return f"Error writing file '{path}': {e}"

@register_tool
def edit_file(path: str, start_line: int, end_line: int, replacement_content: str) -> str:
    """
    Edits a file by replacing a range of lines (1-indexed, inclusive) with new content.

    Args:
        path (str): Path to the file to edit.
        start_line (int): The starting line number of the range to replace (1-indexed, inclusive).
        end_line (int): The ending line number of the range to replace (1-indexed, inclusive).
        replacement_content (str): The new content to insert in place of the range.
    """
    # Prevent editing outside the project boundary
    if not _is_safe_path(path):
        return "Error: Access denied. Attempted modification outside the authorized project directory."

    p = Path(path)
    if not p.exists():
        return f"Error: file not found: {path}"
    
    try:
        # Read all lines as string list, assuming file exists based on existence check
        lines = p.read_text(encoding="utf-8").splitlines()
        
        num_lines = len(lines)

        if num_lines == 0:
            return f"Error: File '{path}' is empty."
        
        # Validate ranges (1 <= start <= end <= N+1)
        if not (1 <= start_line <= num_lines + 1) or not (1 <= end_line <= num_lines + 1) or (start_line > end_line):
            return f"Error: Invalid line range {start_line}-{end_line}. File has {num_lines} lines."
            
        start_idx = start_line - 1
        end_idx = end_line # Slice stops before this index
        
        replacement_lines = replacement_content.splitlines()
        # Replace the segment [start_idx:end_idx] with new lines
        lines[start_idx:end_idx] = replacement_lines
        
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return f"Success: Replaced {len(lines[start_idx:end_idx])} lines (from {start_line} to {end_line}) in '{path}' with {len(replacement_lines)} lines."
    except Exception as e:
        return f"Error modifying file: {e}"

@register_tool
def file_glob(pattern: str, path: str = '.') -> list[str]:
    """
    Find all files matching a given glob pattern.
    
    Args:
        pattern (str): The glob pattern (e.g., '*.py', 'data/config*').
        path (str): The path to search in, defaults to the current working directory.

    Returns:
        list[str]: A list of absolute paths matching the pattern, or an error message string.
    """
    if not _is_safe_path(path):
        return ["Error: Access denied. Attempted access outside the authorized project directory."]

    path_resolved = Path(path).resolve()
    results = []
    
    try:
        for p in path_resolved.glob(pattern):
            p_resolved = p.resolve()
            # Ensure safety check for the actual matched path and exclude ignored dirs
            if _is_safe_path(p_resolved) and not _should_ignore(p_resolved):
                if p_resolved.is_file() or p_resolved.is_dir():
                    results.append(str(p_resolved))

    except Exception as e:
        return [f"Search failed due to internal error: {e}"]
    
    return results if results else [f"No files found matching pattern '{pattern}' in '{path}'." ]


@register_tool
def grep_file(search_term: str, target_path: str) -> list[dict[str, Any]] | str:
    """
    Searches for a search term (case-insensitive) within a file or recursively within a directory.

    Args:
        search_term (str): The pattern/term to search for.
        target_path (str): Path to the target file or directory to search.

    Returns:
        list[dict] | str: A list of dicts with 'path', 'line', and 'content' keys, or an error message string.
    """
    if not _is_safe_path(target_path):
        return "Error: Access denied. Attempted access outside the authorized project directory."

    p = Path(target_path).resolve()
    if not p.exists():
        return f"Error: Target path does not exist: {target_path}"

    files_to_search = []
    if p.is_file():
        files_to_search.append(p)
    elif p.is_dir():
        try:
            for filepath in p.rglob("*"):
                if filepath.is_file() and _is_safe_path(filepath) and not _should_ignore(filepath):
                    files_to_search.append(filepath)
        except Exception as e:
            return f"Error listing directory: {e}"

    matches = []
    search_term_lower = search_term.lower()
    max_matches = 150

    for filepath in files_to_search:
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, 1):
                    if search_term_lower in line.lower():
                        matches.append({
                            "path": str(filepath.relative_to(PROJECT_ROOT)),
                            "line": line_num,
                            "content": line.strip()
                        })
                        if len(matches) >= max_matches:
                            return matches
        except Exception:
            # Skip unreadable/binary files
            pass

    return matches