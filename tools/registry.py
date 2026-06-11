from inspect import signature
from collections.abc import Callable
from typing import Any
import re

from pydantic import create_model, Field

TOOL_REGISTRY: dict[str, Callable] = {}
TOOL_SCHEMAS: list[dict[str, Any]] = []

def _parse_docstring_args(docstring: str | None) -> dict[str, str]:
    """Parses a docstring to extract argument descriptions."""
    arg_descriptions = {}
    if not docstring:
        return arg_descriptions

    lines = docstring.splitlines()
    in_args_section = False
    current_arg = None
    current_desc = []

    for line in lines:
        stripped = line.strip()
        # Detect start of Args section
        if stripped.rstrip(":").lower() in ("args", "parameters", "arguments"):
            in_args_section = True
            continue
        
        # Detect end of Args section (any line that is not indented or starts a new top-level section)
        if in_args_section and not line.startswith(" ") and line.strip() and not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*\s*(?:\([^)]+\))?\s*:", line):
            if stripped.rstrip(":").lower() in ("returns", "raises", "yields", "example", "examples"):
                break

        if in_args_section:
            # Match formats like:
            # param_name: description
            # param_name (type): description
            match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^)]+\))?\s*:\s*(.*)$", stripped)
            if match:
                if current_arg:
                    arg_descriptions[current_arg] = " ".join(current_desc).strip()
                current_arg = match.group(1)
                current_desc = [match.group(2)]
            elif current_arg and (line.startswith(" ") or not stripped):
                if stripped:
                    current_desc.append(stripped)
            elif current_arg:
                arg_descriptions[current_arg] = " ".join(current_desc).strip()
                current_arg = None
                current_desc = []

    if current_arg:
        arg_descriptions[current_arg] = " ".join(current_desc).strip()

    return arg_descriptions

def register_tool(func: Callable) -> Callable:
    name = func.__name__
    TOOL_REGISTRY[name] = func

    sig = signature(func)
    model_name = func.__name__ + "Args"
    docstring = func.__doc__ or "No description provided"

    # Extract argument descriptions from the docstring
    arg_descriptions = _parse_docstring_args(func.__doc__)

    fields = {}
    for param_name, param in sig.parameters.items():
        annotation = param.annotation if param.annotation != param.empty else Any
        default = param.default if param.default != param.empty else ...

        # Inject description if parsed from docstring
        desc = arg_descriptions.get(param_name)
        if desc:
            fields[param_name] = (annotation, Field(default, description=desc))
        else:
            fields[param_name] = (annotation, default)

    model = create_model(model_name, **fields)
    schema = model.model_json_schema()

    schema.pop("title", None)
    if "properties" in schema:
        for prop in schema["properties"].values():
            prop.pop("title", None)
            
    # Extract only the top-level description summary (strip Args, Returns, etc.)
    clean_desc = docstring.strip()
    lower_desc = clean_desc.lower()
    sections = ["args:", "parameters:", "arguments:", "returns:", "raises:", "yields:"]
    indices = [lower_desc.find(sec) for sec in sections if sec in lower_desc]
    if indices:
        clean_desc = clean_desc[:min(indices)].strip()

    openai_schema = {
        "type": "function",
        "function": {
            "name": name,
            "description": clean_desc,
            "parameters": schema
        }
    }
    TOOL_SCHEMAS.append(openai_schema)
    return func
