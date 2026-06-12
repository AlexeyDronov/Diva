from openai import OpenAI
from openai.types.chat import ChatCompletionAssistantMessageParam, ChatCompletionMessageParam, ChatCompletionMessageToolCallParam

from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.status import Status

from tools.tool_handler import handle_tool_calls
from tools.registry import TOOL_SCHEMAS
from config import get_llm_client, unload_model, read_system_prompt

console = Console()
prompt_style = Style.from_dict({
    'prompt': 'bold #00ff87'
})

def agent_loop(
        client: OpenAI, 
        model_name: str,
        thinking_enabled: bool = True,
        system_prompt: str = ""
) -> None:
    messages: list[ChatCompletionMessageParam] = []
    messages.append({"role": "system", "content": system_prompt})

    input_session = PromptSession(style=prompt_style)
    console.print("Hey! Welcome to [bold green]Diva![/bold green] Type [bold red]/bye[/bold red] to exit.\n")

    while True:
        try:
            user_input = input_session.prompt([('class:prompt', '❯ ')])
            if not user_input.strip():
                continue
            if user_input.lower() == "/bye":
                with Status("[red]Unloading model...[/red]", spinner="bouncingBar"):
                    unload_model(model_name)
                    break

            messages.append({"role": "user", "content": user_input})

            while True:
                streaming_response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    stream=True,
                    extra_body={"think": thinking_enabled}
                )

                # Initialize the current assistant message structure to hold streaming updates and tool calls
                assistant_message: ChatCompletionAssistantMessageParam = {
                    "role": "assistant", 
                    "content": "", 
                    "tool_calls": []
                }

                # Placeholders for accumulating tool calls and content from stream
                tool_calls: dict[int, ChatCompletionMessageToolCallParam] = {}
                content = ""

                # Stream the content and render it as Markdown in real-time
                with Live(Markdown(""), auto_refresh=False, console=console) as live:
                    for chunk in streaming_response:
                        if not chunk.choices:
                            continue

                        delta = chunk.choices[0].delta
                        
                        if delta.content:
                            content += delta.content
                            live.update(Markdown(content), refresh=True)

                        if delta.tool_calls:
                            for tool_call in delta.tool_calls:
                                idx = tool_call.index
                                if idx not in tool_calls:
                                    tool_calls[idx] = {
                                        "id": "",
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""}
                                    }
                                entry = tool_calls[idx]
                                if tool_call.id:
                                    entry["id"] = tool_call.id
                                if tool_call.function:
                                    if tool_call.function.name:
                                        entry["function"]["name"] += tool_call.function.name
                                    if tool_call.function.arguments:
                                        entry["function"]["arguments"] += tool_call.function.arguments
                
                # Aggregate the content and tool calls from the stream
                assistant_message["content"] = content
                assistant_message["tool_calls"] = [
                    tool_calls[i] for i in sorted(tool_calls)
                ]
                
                # Append the assistant's response to conversation history
                messages.append(assistant_message)

                if not assistant_message["tool_calls"]:
                    break

                # Execute requested tools and append responses to the conversation
                tool_response = handle_tool_calls(assistant_message["tool_calls"])
                messages.extend(tool_response)

                # Break the loop if the model signaled stop_response
                if any(tc["function"]["name"] == "stop_response" for tc in assistant_message["tool_calls"]):
                    break

        except KeyboardInterrupt:
            break
    
if __name__ == "__main__":
    client = get_llm_client()
    system_prompt = read_system_prompt("SYSTEM_PROMPT.md")
    session = agent_loop(client, "gemma4:e4b-it-qat", system_prompt=system_prompt)