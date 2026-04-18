"""
Router de intenciones: analiza el comando y decide qué módulo lo maneja.
Usa el LLM local para clasificar la intención.
"""

import json
import re
from .brain import ask
from .config import load as load_config

_ROUTING_PROMPT = """Eres Claudia, una asistente de IA. Analiza el comando del usuario \
y responde SOLO con un objeto JSON válido. Sin explicaciones, sin markdown, solo JSON.

Módulos y acciones disponibles:
  music_player:
    - play_all                        -> reproduce toda la música
    - play_playlist {playlist: str}   -> reproduce una lista específica
    - list                            -> lista las listas disponibles
    - stop                            -> detiene la música
  youtube_downloader:
    - download {url: str}             -> descarga una playlist de YouTube
  system_monitor:
    - status                          -> estado del sistema
  english_tutor:
    - start                           -> inicia práctica de inglés
    - chat {text: str}                -> continúa la práctica
    - stop                            -> termina la sesión de inglés
  teacher:
    - explain {topic: str}            -> explica un tema
  general:
    - chat {text: str}                -> conversación general

Formato de respuesta: {"module":"nombre","action":"accion","params":{}}

Ejemplos:
"reproduce toda la música" -> {"module":"music_player","action":"play_all","params":{}}
"pon la lista de rock" -> {"module":"music_player","action":"play_playlist","params":{"playlist":"rock"}}
"descarga https://youtube.com/..." -> {"module":"youtube_downloader","action":"download","params":{"url":"https://..."}}
"cómo está el sistema" -> {"module":"system_monitor","action":"status","params":{}}
"enséñame sobre la Segunda Guerra Mundial" -> {"module":"teacher","action":"explain","params":{"topic":"Segunda Guerra Mundial"}}
"quiero practicar inglés" -> {"module":"english_tutor","action":"start","params":{}}
"buenos días, cómo estás" -> {"module":"general","action":"chat","params":{"text":"buenos días, cómo estás"}}
"""

_GENERAL_PROMPT_ES = (
    "Eres Claudia, una asistente amigable y útil. Responde siempre en español, "
    "de forma conversacional y concisa. No uses markdown, viñetas ni listas. "
    "Habla como si fuera una conversación real en voz alta."
)

_GENERAL_PROMPT_EN = (
    "You are Claudia, a friendly and helpful AI assistant. Respond conversationally "
    "and concisely. No markdown or bullet points – speak naturally."
)


def route(command: str) -> dict:
    """Retorna un dict con module, action y params para el comando dado."""
    try:
        raw = ask(command, system_prompt=_ROUTING_PROMPT)
        match = re.search(r"\{[^{}]+\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return {"module": "general", "action": "chat", "params": {"text": command}}


def handle_general(text: str) -> str:
    cfg = load_config()
    system = _GENERAL_PROMPT_ES if cfg["system"]["language"] == "es" else _GENERAL_PROMPT_EN
    return ask(text, system_prompt=system)
