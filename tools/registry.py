from inspect import signature
from collections.abc import Callable
from typing import Any

from pydantic import create_model

TOOL_REGISTRY: dict[str, Callable] = {}
TOOL_SCHEMAS: list[dict[str, Any]] = []

def register_tool(func: Callable) -> Callable:
    name = func.__name__
    TOOL_REGISTRY[name] = func

    sig = signature(func)
    model_name = func.__name__ + "Args"
    docstring = func.__doc__ or "No description provided"

    fields = {}
    for param_name, param in sig.parameters.items():
        annotation = param.annotation if param.annotation != param.empty else Any
        default = param.default if param.default != param.empty else ...

        fields[param_name] = (annotation, default)

    model = create_model(model_name, **fields)
    schema = model.model_json_schema()

    schema.pop("title", None)
    if "properties" in schema:
        for prop in schema["properties"].values():
            prop.pop("title", None)
            
    openai_schema = {
        "type": "function",
        "function": {
            "name": name,
            "description": docstring.strip(),
            "parameters": schema
        }
    }
    TOOL_SCHEMAS.append(openai_schema)
    return func
