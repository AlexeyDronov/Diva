from openai import OpenAI
import json
from tools.registry import TOOL_REGISTRY, TOOL_SCHEMAS
import tools
from config import get_llm_client, unload_model, read_system_prompt


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
            "content": result
        })

        if name == "stop_response":
            completion_flag = True
            break
    return tool_responses, completion_flag

def agent_loop(
        client: OpenAI, 
        model_name: str, 
        system_prompt: str = "", 
        max_retries: int = 10
) -> None:
    messages = [{"role": "system", "content": system_prompt}]

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() == "/bye":
                unload_model(model_name)
                break

            messages.append({"role": "user", "content": user_input})
            while True:
                tool_max_retries = max_retries
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages, # type: ignore
                    tools=TOOL_SCHEMAS # type: ignore
                )
                
                message = response.choices[0].message
                messages.append(message) # type: ignore
                
                if message.tool_calls:
                    tool_response, completion_flag = handle_tool_calls(message.tool_calls)
                    messages.extend(tool_response)
                else:
                    print(f"Assistant: {message.content}")
                    completion_flag = True

                if completion_flag:
                    break
        except KeyboardInterrupt:
            break
    
if __name__ == "__main__":
    client = get_llm_client()
    system_prompt = read_system_prompt("SYSTEM_PROMPT.md")
    session = agent_loop(client, "gemma4:e4b-mlx", system_prompt=system_prompt)