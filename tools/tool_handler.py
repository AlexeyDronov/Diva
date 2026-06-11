import json
from typing import Any
from tools.registry import TOOL_REGISTRY

def handle_tool_calls(
        tool_calls
):
    tool_responses: list[dict[str, str]] = []
    completion_flag = False

    for tool_call in tool_calls:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        print(f"    [tool] {name}({args})")

        if name not in TOOL_REGISTRY:
            result = f"Error: unkown tool '{name}'. Available tools: {list(TOOL_REGISTRY.keys())}"
        else:
            result = TOOL_REGISTRY[name](**args)

        print(f"    [tool results] {result[:200]}{'...' if len(result) > 200 else result}")
        tool_responses.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": _serialise_answers(result)
        })

        if name == "stop_response":
            completion_flag = True
            break
    return tool_responses, completion_flag

def _serialise_answers(result: Any) -> str:
    if isinstance(result, str):
        return result
    else:
        try:
            return json.dumps(result)
        except Exception as e:
            return str(result)