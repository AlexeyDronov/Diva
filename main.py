from openai import OpenAI
from openai.types.chat import ChatCompletionAssistantMessageParam, ChatCompletionMessageParam, ChatCompletionMessageToolCallParam

from tools.tool_handler import handle_tool_calls
from tools.registry import TOOL_SCHEMAS
from config import get_llm_client, unload_model, read_system_prompt


def agent_loop(
        client: OpenAI, 
        model_name: str, 
        system_prompt: str = "", 
        max_text_turns: int = 5
) -> None:
    messages: list[ChatCompletionMessageParam] = []
    messages.append({"role": "system", "content": system_prompt})

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() == "/bye":
                unload_model(model_name)
                break
            print()

            messages.append({"role": "user", "content": user_input})
            consecutive_text_turns = 0

            while True:
                streaming_response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    stream=True
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

                for chunk in streaming_response:
                    if not chunk.choices:
                        continue

                    delta = chunk.choices[0].delta
                    
                    if delta.content:
                        content += delta.content
                        print(delta.content, end="", flush=True)

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
                
                if not tool_calls:
                    consecutive_text_turns += 1
                    if consecutive_text_turns >= max_text_turns:
                        print("\n[SYSTEM] Agent did not signal completion. Breaking.")
                        break
                
                # Reset counter when a tool is invoked
                consecutive_text_turns = 0

                if any(tc["function"]["name"] == "stop_response" for tc in assistant_message["tool_calls"]):
                    break
                
                messages.append(assistant_message)

                # Check if tools were requested before finishing the message structure
                tool_response = handle_tool_calls(assistant_message["tool_calls"])
                messages.extend(tool_response)

        except KeyboardInterrupt:
            break
    
if __name__ == "__main__":
    client = get_llm_client()
    system_prompt = read_system_prompt("SYSTEM_PROMPT.md")
    session = agent_loop(client, "gemma4:e4b-it-qat", system_prompt=system_prompt)