import httpx
from openai import OpenAI
from pathlib import Path

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

def read_system_prompt(prompt_file: str | Path) -> str:
    p = Path(prompt_file)
    if not p.exists():
        raise FileNotFoundError(f"File at {p} does not exist.")
    lines = p.read_text(errors="replace").splitlines()
    return '\n'.join(lines)