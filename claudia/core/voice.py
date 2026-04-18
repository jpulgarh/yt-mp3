"""Síntesis de voz (TTS) – edge-tts o pyttsx3 como alternativa offline."""

import asyncio
import os
import subprocess
import tempfile
from .config import load as load_config


async def _speak_edge(text: str, cfg: dict) -> None:
    import edge_tts
    tts_cfg = cfg["tts"]
    communicate = edge_tts.Communicate(
        text=text,
        voice=tts_cfg["voice"],
        rate=tts_cfg["rate"],
        volume=tts_cfg["volume"],
    )
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp = f.name
    try:
        await communicate.save(tmp)
        subprocess.run(["mpg123", "-q", tmp], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _speak_pyttsx3(text: str) -> None:
    import pyttsx3
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


def speak(text: str) -> None:
    """Convierte texto a voz usando el proveedor configurado."""
    if not text:
        return
    cfg = load_config()
    provider = cfg["tts"]["provider"]
    try:
        if provider == "edge-tts":
            asyncio.run(_speak_edge(text, cfg))
        else:
            _speak_pyttsx3(text)
    except Exception:
        # Silencia errores de TTS para no interrumpir el flujo principal
        pass


def beep() -> None:
    """Sonido de activación para indicar que Claudia está escuchando."""
    try:
        import numpy as np
        import sounddevice as sd
        sr = 22050
        t = np.linspace(0, 0.15, int(sr * 0.15), False)
        tone = (np.sin(2 * np.pi * 880 * t) * 0.3).astype(np.float32)
        sd.play(tone, sr)
        sd.wait()
    except Exception:
        pass
