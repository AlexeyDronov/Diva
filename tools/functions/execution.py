from tools.registry import register_tool

@register_tool
def stop_response(summary: str) -> str:
    """Stops the response of the agent and breaks out of the loop."""
    return f"Task completed. Summary: {summary}"