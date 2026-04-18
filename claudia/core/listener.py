"""
Reconocimiento de voz (STT) con faster-whisper.
El audio se procesa completamente en memoria – nunca se guarda en disco.
"""

import numpy as np
import sounddevice as sd
import webrtcvad
from faster_whisper import WhisperModel
from .config import load as load_config

_command_model: WhisperModel = None


def _get_command_model() -> WhisperModel:
    global _command_model
    if _command_model is None:
        cfg = load_config()
        _command_model = WhisperModel(
            cfg["stt"]["model"],
            compute_type="int8",
            device="cpu",
        )
    return _command_model


def _record_until_silence(sr: int, max_sec: int, vad_level: int) -> np.ndarray:
    """Graba hasta detectar silencio prolongado o alcanzar max_sec."""
    vad = webrtcvad.Vad(vad_level)
    frame_ms = 30
    frame_size = int(sr * frame_ms / 1000)
    max_silence = int(1500 / frame_ms)   # 1.5 s de silencio para cortar
    max_frames = int(max_sec * 1000 / frame_ms)

    chunks = []
    silence_frames = 0
    has_speech = False

    with sd.InputStream(samplerate=sr, channels=1, dtype="int16",
                        blocksize=frame_size) as stream:
        for _ in range(max_frames):
            chunk, _ = stream.read(frame_size)
            flat = chunk.flatten()
            chunks.append(flat)

            try:
                is_speech = vad.is_speech(flat.tobytes(), sr)
            except Exception:
                is_speech = False

            if is_speech:
                has_speech = True
                silence_frames = 0
            else:
                silence_frames += 1
                if has_speech and silence_frames >= max_silence:
                    break

    audio = np.concatenate(chunks).astype(np.float32) / 32768.0
    return audio


def transcribe(audio: np.ndarray, language: str = None) -> str:
    """Transcribe audio (float32 numpy array a 16kHz) a texto."""
    model = _get_command_model()
    segments, _ = model.transcribe(audio, language=language, beam_size=5)
    return " ".join(seg.text for seg in segments).strip()


def listen_command(max_seconds: int = 12) -> str:
    """Graba un comando de voz y retorna el texto transcrito."""
    cfg = load_config()
    sr = cfg["audio"]["sample_rate"]
    vad_level = cfg["audio"]["vad_aggressiveness"]
    lang = cfg["stt"]["language"]
    audio = _record_until_silence(sr, max_seconds, vad_level)
    return transcribe(audio, language=lang)
