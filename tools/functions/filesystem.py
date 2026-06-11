from pathlib import Path
import os
from tools.registry import register_tool

PROJECT_ROOT = Path(os.getcwd()).resolve()

def _is_safe_path(target_path: str) -> bool:
    """
    Internal guardrail function. Checks if a given path is within the allowed project directory.
    This prevents path traversal attacks (e.g., moving outside the project structure).
    """
    p = Path(target_path).resolve()
    try:
        return p.is_relative_to(PROJECT_ROOT)
    except Exception:
        return False


@register_tool
def read_file(path: str, offset: int = 1, limit: int = 200, raw: bool = True) -> str:
    """Read lines from a file, with optional offset and limit."""
    if not _is_safe_path(path):
        return "Error: Access denied. Attempted access outside the authorized project directory."

    p = Path(path)
    if not p.exists() or not p.is_file(): # Check if it exists AND is a file
        return f"Error: File not found: {path}"
    
    # Proceed with reading only after safety check and existence confirmation
    try:
        lines = p.read_text(errors="replace").splitlines()
        selected = lines[offset - 1: offset - 1 + limit]
        if raw:
            return "\n".join(selected)
        else:
            return "\n".join(f"{offset + i}: {line}" for i, line in enumerate(selected))
    except Exception as e:
        return f"Error reading file '{path}': {e}"


@register_tool
def write_file(path: str, content: str) -> str:
    """Writes the provided content string to a specified file."""
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
    """Edits a file by replacing a range of lines (1-indexed, inclusive) with new content."""
    # Prevent editing outside the project boundary
    if not _is_safe_path(path):
        return "Error: Access denied. Attempted modification outside the authorized project directory."

    p = Path(path)
    if not p.exists():
        return f"Error: file not found: {path}"
    
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
        
        # Guard against invalid line ranges
        num_lines = len(lines)
        if not (1 <= start_line <= num_lines + 1) or not (1 <= end_line <= num_lines + 1) or (start_line > end_line):
            return f"Error: Invalid line range {start_line}-{end_line} (File has {num_lines} lines)."
            
        start_idx = start_line - 1
        # Python slices are exclusive at the stop index, so end_line works directly.
        end_idx = end_line
        
        replacement_lines = replacement_content.splitlines()
        lines[start_idx:end_idx] = replacement_lines
        
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return f"Success: Replaced lines {start_line} to {end_line} in '{path}'."
    except Exception as e:
        return f"Error modifying file: {e}"