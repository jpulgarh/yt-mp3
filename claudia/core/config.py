"""Gestión centralizada de la configuración."""

from pathlib import Path
import yaml

CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


def load() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save(cfg: dict) -> None:
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)


def get(key_path: str, default=None):
    """Accede a un valor anidado con notación de punto: 'llm.model'."""
    data = load()
    for key in key_path.split("."):
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data


def set_value(key_path: str, value) -> None:
    """Actualiza un valor anidado con notación de punto y guarda el archivo."""
    cfg = load()
    keys = key_path.split(".")
    node = cfg
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    node[keys[-1]] = value
    save(cfg)
