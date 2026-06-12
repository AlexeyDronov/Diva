import json
from typing import Any

from openai.types.chat import ChatCompletionMessageToolCallParam, ChatCompletionToolMessageParam
from rich.console import Console
from tools.registry import TOOL_REGISTRY

console = Console()

def handle_tool_calls(
        tool_calls: list[ChatCompletionMessageToolCallParam]
) -> list[ChatCompletionToolMessageParam]:
    tool_responses: list[ChatCompletionToolMessageParam] = []

    for tool_call in tool_calls:
        name = tool_call["function"]["name"]
        args = json.loads(tool_call["function"]["arguments"])

        # Display tool call with rich styling
        console.print(f"[bold cyan]🔧 tool:[/bold cyan] [green]{name}[/green] [dim]({args})[/dim]")

        if name not in TOOL_REGISTRY:
            result = f"Error: unkown tool '{name}'. Available tools: {list(TOOL_REGISTRY.keys())}"
        else:
            result = TOOL_REGISTRY[name](**args)

        res_str = _serialise_answers(result)
        truncated = res_str[:200] + "..." if len(res_str) > 200 else res_str
        
        # Display results with rich formatting and fix the double print bug
        console.print(f"[bold magenta]📥 tool results:[/bold magenta] [dim]{truncated}[/dim]")
        
        tool_responses.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": res_str
        })

    return tool_responses

def _serialise_answers(result: Any) -> str:
    if isinstance(result, str):
        return result
    else:
        try:
            return json.dumps(result)
        except Exception as e:
            return str(result)