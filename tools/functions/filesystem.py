from pathlib import Path
from tools.registry import register_tool

@register_tool
def read_file(path: str, offset: int = 1, limit: int = 200) -> str:
    """Read lines from a file, with optional offset and limit."""
    p = Path(path)
    if not p.exists():
        return f"Error: file not found: {path}"
    lines = p.read_text(errors="replace").splitlines()
    selected = lines[offset - 1: offset - 1 + limit]
    return "\n".join(f"{offset + i}: {line}" for i, line in enumerate(selected))

@register_tool
def write_file(path: str, content: str) -> str:
    """Writes the provided content string to a specified file."""
    p = Path(path)
    try:
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: File '{path}' has been created and written successfully."
    except IOError as e:
        return f"Error writing file '{path}': {e}"
    
@register_tool
def edit_file(path: str, old_str: str, new_str: str) -> str:
    """Edits a file by replacing a specific block of text with a new block."""
    p = Path(path)
    if not p.exists():
        return f"Error: file not found: {path}"
    try:
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()
        count = content.count(old_str)
        if count == 0:
            return (
                f"Error: The exact text block to replace was not found in {p}.\n"
                "Ensure spelling, indentation, and newlines match perfectly."
            )
        elif count > 1:
            return (
                f"Error: The text block to replace is not unique (found {count} matches).\n"
                "Please include more surrounding context lines in your 'old_str' anchor."
            )
        
        new_content = content.replace(old_str, new_str)

        with open(p, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"Success: Safely updated '{p}'"
    except Exception as e:
        return f"Error writing to file: {str(e)}"