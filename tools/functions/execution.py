from tools.registry import register_tool

@register_tool
def stop_response(summary: str) -> str:
    """
    Signal that you have completed the current task. Call this when you have finished all work and have no more actions to take.

    Args:
        summary (str): A detailed summary of the accomplished tasks.
    """
    return f"Task completed. Summary: {summary}"