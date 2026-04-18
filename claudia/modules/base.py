"""Clase base para todos los módulos de Claudia."""

from abc import ABC, abstractmethod
from ..core.config import get as cfg_get


class BaseModule(ABC):
    name: str = "base"
    description: str = ""

    @abstractmethod
    def execute(self, action: str, params: dict) -> str:
        """Ejecuta una acción y retorna el texto de respuesta."""

    def is_enabled(self) -> bool:
        return bool(cfg_get(f"modules.{self.name}", True))

    def help_text(self) -> str:
        return f"Módulo '{self.name}': {self.description}"
