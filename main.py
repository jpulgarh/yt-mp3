#!/usr/bin/env python3
"""
CLAUDIA – Asistente IA Local con voz
Punto de entrada principal. Ejecutar con: python main.py

Controles:
  ESPACIO  →  Activar / Desactivar micrófono
  C        →  Menú de configuración
  Q / ESC  →  Salir
"""

import curses
import threading
import time
import sys
from pathlib import Path
from datetime import datetime

# ── Bootstrap: verificar dependencias críticas ───────────────────────────────
def _check_deps():
    missing = []
    for pkg in ("yaml", "ollama", "faster_whisper", "sounddevice", "edge_tts", "psutil", "rich"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[ERROR] Dependencias faltantes: {', '.join(missing)}")
        print("Instala con: pip install -r requirements.txt")
        sys.exit(1)

_check_deps()

from claudia.core import config as cfg_module
from claudia.core.voice import speak, beep
from claudia.core.listener import listen_command
from claudia.core.router import route, handle_general
from claudia.core.wake_word import listen_for_wake_word
from claudia.core.brain import is_ollama_available
from claudia.modules import MODULE_MAP
from claudia.modules.system_monitor import SystemMonitorModule

# ── Estado global (compartido entre hilos) ───────────────────────────────────
_lock = threading.Lock()
_active = cfg_module.get("system.active", True)
_log: list[tuple[str, str]] = []   # (timestamp, mensaje) – solo en memoria
_mode = "Iniciando..."
_stop_event = threading.Event()
_wake_thread: threading.Thread = None
_monitor = SystemMonitorModule()

MAX_LOG = 30


def _log_add(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    with _lock:
        _log.append((ts, msg))
        if len(_log) > MAX_LOG:
            _log.pop(0)


def _set_mode(m: str) -> None:
    global _mode
    with _lock:
        _mode = m


# ── Procesamiento de comandos ─────────────────────────────────────────────────
def _process_command(full_text: str) -> None:
    wake_word = cfg_module.get("system.wake_word", "hey claudia")
    command = full_text.lower().replace(wake_word, "").strip()

    if not command:
        _set_mode("Escuchando comando...")
        _log_add("[sistema] Escuchando comando...")
        beep()
        timeout = cfg_module.get("system.listen_timeout", 12)
        command = listen_command(max_seconds=timeout)

    if not command.strip():
        _set_mode(f"Esperando '{wake_word}'...")
        return

    _log_add(f"[tú] {command}")
    _set_mode("Procesando con IA...")

    intent = route(command)
    module_name = intent.get("module", "general")
    action = intent.get("action", "chat")
    params = intent.get("params", {})

    if module_name == "general":
        response = handle_general(command)
    elif module_name in MODULE_MAP and MODULE_MAP[module_name].is_enabled():
        response = MODULE_MAP[module_name].execute(action, params)
    else:
        response = handle_general(command)

    preview = response[:120] + ("..." if len(response) > 120 else "")
    _log_add(f"[claudia] {preview}")
    _set_mode("Hablando...")
    speak(response)
    _set_mode(f"Esperando '{wake_word}'...")


def _wake_callback(text: str) -> None:
    if not _active:
        return
    _log_add("[sistema] ¡Palabra de activación detectada!")
    _set_mode("Procesando comando...")
    t = threading.Thread(target=_process_command, args=(text,), daemon=True)
    t.start()


def _start_wake_listener() -> threading.Thread:
    wake_word = cfg_module.get("system.wake_word", "hey claudia")
    t = threading.Thread(
        target=listen_for_wake_word,
        args=(wake_word, _wake_callback, _stop_event, _log_add),
        daemon=True,
    )
    t.start()
    return t


# ── Menú de configuración ─────────────────────────────────────────────────────
_CONFIG_FIELDS = [
    ("llm.model",               "Modelo LLM"),
    ("llm.host",                "Servidor Ollama"),
    ("tts.voice",               "Voz TTS"),
    ("tts.provider",            "Proveedor TTS (edge-tts / pyttsx3)"),
    ("stt.model",               "Modelo STT (tiny/base/small/medium/large)"),
    ("system.wake_word",        "Palabra de activación"),
    ("system.language",         "Idioma (es / en)"),
    ("paths.music_dir",         "Carpeta de música"),
    ("player.preferred",        "Reproductor (mpg123/audacious/vlc)"),
]


def _draw_config(stdscr, sel: int) -> None:
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    title = " CONFIGURACIÓN "
    stdscr.addstr(0, (w - len(title)) // 2, title, curses.A_BOLD | curses.color_pair(3))
    stdscr.addstr(1, 2, "─" * (w - 4), curses.color_pair(5))
    stdscr.addstr(2, 2, "↑↓ Navegar   ENTER Editar   ESC Volver", curses.color_pair(4))
    stdscr.addstr(3, 2, "─" * (w - 4), curses.color_pair(5))

    for i, (key, label) in enumerate(_CONFIG_FIELDS):
        row = 4 + i
        if row >= h - 2:
            break
        val = str(cfg_module.get(key, ""))
        line = f" {label:<38} {val}"
        attr = curses.color_pair(3) | curses.A_BOLD if i == sel else curses.color_pair(5)
        stdscr.addstr(row, 2, line[:w - 4], attr)

    stdscr.addstr(h - 1, 2, "Módulos activos: " + " | ".join(MODULE_MAP.keys()), curses.color_pair(4))
    stdscr.refresh()


def _edit_field(stdscr, key: str, label: str) -> None:
    h, w = stdscr.getmaxyx()
    current = str(cfg_module.get(key, ""))
    prompt = f" Editar [{label}]  (ENTER=guardar, ESC=cancelar): "
    stdscr.addstr(h - 2, 0, " " * (w - 1), curses.color_pair(1))
    stdscr.addstr(h - 2, 0, prompt + current, curses.color_pair(1))
    stdscr.refresh()

    curses.echo()
    curses.curs_set(1)
    try:
        raw = stdscr.getstr(h - 2, len(prompt), w - len(prompt) - 2)
        new_val = raw.decode("utf-8").strip()
        if new_val:
            cfg_module.set_value(key, new_val)
    except Exception:
        pass
    finally:
        curses.noecho()
        curses.curs_set(0)


def _config_menu(stdscr) -> None:
    sel = 0
    while True:
        _draw_config(stdscr, sel)
        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")) and sel > 0:
            sel -= 1
        elif key in (curses.KEY_DOWN, ord("j")) and sel < len(_CONFIG_FIELDS) - 1:
            sel += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            field_key, field_label = _CONFIG_FIELDS[sel]
            _edit_field(stdscr, field_key, field_label)
        elif key in (27, ord("q")):
            break


# ── Pantalla principal ────────────────────────────────────────────────────────
def _draw_main(stdscr) -> None:
    global _active, _mode
    h, w = stdscr.getmaxyx()

    with _lock:
        active_snapshot = _active
        mode_snapshot = _mode
        log_snapshot = list(_log)

    stdscr.clear()

    # ── Cabecera
    cfg = cfg_module.load()
    model = cfg["llm"]["model"]
    header = f" CLAUDIA – Asistente IA Local  |  Modelo: {model} "
    stdscr.addstr(0, max(0, (w - len(header)) // 2), header, curses.A_BOLD | curses.color_pair(3))
    stdscr.addstr(1, 2, "═" * (w - 4), curses.color_pair(3))

    # ── Estado
    status_text = "● ACTIVO" if active_snapshot else "○ INACTIVO"
    status_color = curses.color_pair(1) if active_snapshot else curses.color_pair(2)
    stdscr.addstr(2, 4, status_text, status_color | curses.A_BOLD)
    stdscr.addstr(2, 16, f"│ {mode_snapshot}", curses.color_pair(4))

    # ── Música dir
    music_dir = cfg["paths"]["music_dir"]
    stdscr.addstr(3, 4, f"Música: {music_dir}", curses.color_pair(5))

    stdscr.addstr(4, 2, "─" * (w - 4), curses.color_pair(5))

    # ── Log de actividad
    log_title = " ACTIVIDAD RECIENTE "
    stdscr.addstr(5, 4, log_title, curses.A_BOLD | curses.color_pair(5))
    log_area_height = h - 10
    visible_log = log_snapshot[-(log_area_height):]
    for i, (ts, msg) in enumerate(visible_log):
        row = 6 + i
        if row >= h - 4:
            break
        color = (
            curses.color_pair(3) if msg.startswith("[claudia]")
            else curses.color_pair(4) if msg.startswith("[sistema]")
            else curses.color_pair(5)
        )
        line = f"  {ts}  {msg}"
        try:
            stdscr.addstr(row, 2, line[:w - 4], color)
        except curses.error:
            pass

    # ── Sistema
    try:
        sys_line = _monitor.status_line()
    except Exception:
        sys_line = "Sistema: N/A"
    stdscr.addstr(h - 4, 2, "─" * (w - 4), curses.color_pair(5))
    stdscr.addstr(h - 3, 4, sys_line, curses.color_pair(4))

    # ── Barra de controles
    stdscr.addstr(h - 2, 2, "─" * (w - 4), curses.color_pair(5))
    controls = "[ESPACIO] Activar/Desactivar  [C] Configuración  [Q] Salir"
    stdscr.addstr(h - 1, max(0, (w - len(controls)) // 2), controls, curses.color_pair(5))

    stdscr.refresh()


def _run(stdscr) -> None:
    global _active, _wake_thread

    # ── Inicializar colores
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)    # activo / claudia
    curses.init_pair(2, curses.COLOR_RED, -1)      # inactivo / error
    curses.init_pair(3, curses.COLOR_CYAN, -1)     # títulos / claudia
    curses.init_pair(4, curses.COLOR_YELLOW, -1)   # sistema / usuario
    curses.init_pair(5, curses.COLOR_WHITE, -1)    # normal
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(500)

    # ── Verificar Ollama
    _log_add("[sistema] Verificando conexión con Ollama...")
    if not is_ollama_available():
        _log_add("[error] Ollama no disponible. Verifica que esté corriendo.")
    else:
        model = cfg_module.get("llm.model", "?")
        _log_add(f"[sistema] Ollama conectado. Modelo: {model}")

    # ── Cargar modelo de wake word en segundo plano
    _log_add("[sistema] Cargando modelos de voz (primera vez puede tardar)...")

    def _preload():
        try:
            from claudia.core.wake_word import _get_wake_model
            from claudia.core.listener import _get_command_model
            _get_wake_model()
            _get_command_model()
            _log_add("[sistema] Modelos cargados correctamente.")
        except Exception as e:
            _log_add(f"[error] Error cargando modelos: {e}")

    threading.Thread(target=_preload, daemon=True).start()

    # ── Iniciar listener si está activo
    wake_word = cfg_module.get("system.wake_word", "hey claudia")
    if _active:
        _wake_thread = _start_wake_listener()
        _set_mode(f"Esperando '{wake_word}'...")
        _log_add(f"[sistema] Escuchando '{wake_word}'...")
    else:
        _set_mode("Sistema inactivo – micrófono bloqueado")

    # ── Bucle principal
    while True:
        _draw_main(stdscr)
        key = stdscr.getch()

        if key == ord(" "):
            _active = not _active
            cfg_module.set_value("system.active", _active)

            if _active:
                _stop_event.clear()
                _wake_thread = _start_wake_listener()
                _set_mode(f"Esperando '{wake_word}'...")
                _log_add("[sistema] Micrófono ACTIVADO.")
            else:
                _stop_event.set()
                _set_mode("Sistema inactivo – micrófono bloqueado")
                _log_add("[sistema] Micrófono DESACTIVADO.")

        elif key in (ord("c"), ord("C")):
            _config_menu(stdscr)
            # Recargar wake_word por si cambió
            wake_word = cfg_module.get("system.wake_word", "hey claudia")

        elif key in (ord("q"), ord("Q"), 27):
            _stop_event.set()
            break


def main() -> None:
    try:
        curses.wrapper(_run)
    except KeyboardInterrupt:
        pass
    finally:
        _stop_event.set()
        print("\nHasta luego.")


if __name__ == "__main__":
    main()
