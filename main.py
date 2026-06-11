from openai import OpenAI
from tools.tool_handler import handle_tool_calls
from tools.registry import TOOL_SCHEMAS
from config import get_llm_client, unload_model, read_system_prompt


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