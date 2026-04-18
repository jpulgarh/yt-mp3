"""Cliente LLM – interfaz con Ollama (completamente local)."""

import ollama
from .config import load as load_config


def ask(prompt: str, system_prompt: str = None, history: list = None) -> str:
    """
    Envía un mensaje al LLM local y retorna la respuesta como texto.
    No se envía ningún dato a servidores externos.
    """
    cfg = load_config()
    llm = cfg["llm"]

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    client = ollama.Client(host=llm["host"])
    response = client.chat(
        model=llm["model"],
        messages=messages,
        options={
            "temperature": llm["temperature"],
            "num_predict": llm["max_tokens"],
        },
    )
    return response["message"]["content"].strip()


def is_ollama_available() -> bool:
    try:
        cfg = load_config()
        client = ollama.Client(host=cfg["llm"]["host"])
        client.list()
        return True
    except Exception:
        return False
