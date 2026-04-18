"""
Módulo: Profesor / modo educativo.
Explica cualquier tema de forma clara, adaptada para voz.
Ideal para tareas con hijos o aprendizaje personal.
"""

from .base import BaseModule
from ..core.brain import ask
from ..core.config import load as load_config

_SYSTEM_ES = """Eres un profesor experto, claro y amigable que enseña en español.
Cuando expliques un tema:
1. Empieza con una introducción breve y atractiva.
2. Desarrolla los puntos más importantes con ejemplos concretos y analogías simples.
3. Usa un tono cálido y motivador, adaptado a cualquier edad.
4. Habla como si fuera una conversación hablada: no uses listas, viñetas ni markdown.
5. Mantén cada respuesta a no más de 3 o 4 párrafos cortos.
6. Al terminar, pregunta si quieren profundizar en algún aspecto específico."""

_SYSTEM_EN = """You are a clear, friendly expert teacher.
Explain topics in simple, engaging spoken language.
No markdown or bullet points. Keep responses to 3-4 short paragraphs.
End with a follow-up question."""


class TeacherModule(BaseModule):
    name = "teacher"
    description = "Explica cualquier tema de forma didáctica y clara"

    def __init__(self):
        self._history: list = []
        self._current_topic: str = ""

    def execute(self, action: str, params: dict) -> str:
        cfg = load_config()
        system = _SYSTEM_ES if cfg["system"]["language"] == "es" else _SYSTEM_EN

        if action == "explain":
            topic = params.get("topic", "").strip()
            if not topic:
                return "¿Sobre qué tema te gustaría aprender hoy?"
            self._current_topic = topic
            self._history = []
            prompt = f"Explícame de forma clara y didáctica el siguiente tema: {topic}"
            return self._ask(prompt, system)

        if action in ("follow_up", "chat", "general"):
            text = params.get("text", "")
            if not text:
                return "¿Tienes alguna pregunta sobre lo que hablamos?"
            return self._ask(text, system)

        topic = params.get("topic", params.get("text", ""))
        if topic:
            return self.execute("explain", {"topic": topic})
        return "¿Sobre qué tema te gustaría aprender?"

    def _ask(self, prompt: str, system: str) -> str:
        self._history.append({"role": "user", "content": prompt})
        response = ask(prompt, system_prompt=system, history=self._history[:-1])
        self._history.append({"role": "assistant", "content": response})
        if len(self._history) > 12:
            self._history = self._history[-12:]
        return response
