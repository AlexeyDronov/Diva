import os
from openai import OpenAI
import httpx

OLLAMA_URL = "http://localhost:11434/"

def get_llm_client():
    base_url = OLLAMA_URL + "v1"
    return OpenAI(
        base_url=base_url,
        api_key="ollama"
    )

def unload_model(model_name: str) -> None:
    base_url = OLLAMA_URL + "api/generate"
    try:
        response = httpx.post(
            base_url, json={"model": model_name, "keep_alive": 0}
        )
        if response.status_code == 200:
            print(f"\n[SYSTEM] Successfully unloaded {model_name} from VRAM.")
    except Exception as e:
        print(f"\n[System] Failed to clear VRAM: {e}")

def agent_loop(client: OpenAI, model_name: str):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

    while True:
        user_input = input("User: ")
        if user_input.lower() == "\\bye":
            unload_model(model_name)
            break

        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model=model_name,
            messages=messages # type: ignore
        )

        reply = response.choices[0].message.content
        if not reply:
            raise ValueError("LLM did not produce a response.")
        
        messages.append({"role": "assistant", "content": reply})
        print(f"Assistant: {reply}")
    
if __name__ == "__main__":
    client = get_llm_client()
    session = agent_loop(client, "gemma4:e4b-mlx")