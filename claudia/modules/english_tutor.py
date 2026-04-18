"""
Módulo: Tutor de inglés conversacional.
Corrige errores, motiva y adapta el nivel del estudiante.
"""

from .base import BaseModule
from ..core.brain import ask

_SYSTEM = """You are an English language tutor for Spanish speakers.
Your role:
1. Have natural English conversations adapted to the student's level.
2. Gently correct grammar and vocabulary mistakes inline.
3. Suggest more natural expressions when appropriate.
4. Keep responses short and conversational (they will be read aloud).
5. Encourage the student warmly.
6. Occasionally ask follow-up questions to keep the conversation going.
Do NOT use markdown, bullet points or headers. Speak naturally."""


class EnglishTutorModule(BaseModule):
    name = "english_tutor"
    description = "Práctica de inglés conversacional con correcciones amigables"

    def __init__(self):
        self._history: list = []
        self._active = False

    def execute(self, action: str, params: dict) -> str:
        if action == "start":
            self._history = []
            self._active = True
            return ask(
                "The student wants to start an English practice session. "
                "Greet them warmly and ask them to introduce themselves.",
                system_prompt=_SYSTEM,
            )

        if action in ("chat", "general"):
            text = params.get("text", "")
            if not text:
                return "What would you like to say?"
            return self._chat(text)

        if action == "stop":
            self._active = False
            self._history = []
            return (
                "Great practice session! Keep it up. "
                "Remember: a little practice every day makes a big difference!"
            )

        return self._chat(params.get("text", "Hello"))

    def _chat(self, text: str) -> str:
        self._history.append({"role": "user", "content": text})
        response = ask(text, system_prompt=_SYSTEM, history=self._history[:-1])
        self._history.append({"role": "assistant", "content": response})
        if len(self._history) > 20:
            self._history = self._history[-20:]
        return response
