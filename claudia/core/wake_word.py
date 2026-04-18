"""
Detección de palabra de activación ("Hey Claudia").
Usa faster-whisper tiny en fragmentos cortos de audio.
El audio nunca se guarda en disco ni se envía externamente.
"""

import threading
import numpy as np
import sounddevice as sd
import webrtcvad
from faster_whisper import WhisperModel
from .config import load as load_config

_wake_model: WhisperModel = None
_wake_lock = threading.Lock()


def _get_wake_model() -> WhisperModel:
    global _wake_model
    with _wake_lock:
        if _wake_model is None:
            _wake_model = WhisperModel("tiny", compute_type="int8", device="cpu")
    return _wake_model


def listen_for_wake_word(wake_word: str, on_detected, stop_event, log_fn=None) -> None:
    """
    Bucle de escucha permanente en segundo plano.
    Cuando detecta la wake_word llama a on_detected(text_transcribed).

    Args:
        wake_word:   Frase a detectar (minúsculas).
        on_detected: Callback(texto_detectado) llamado al detectar la frase.
        stop_event:  threading.Event – al activarlo detiene el bucle.
        log_fn:      Función opcional para logging en UI (no guarda en disco).
    """
    sr = 16000
    frame_ms = 30
    frame_size = int(sr * frame_ms / 1000)
    vad = webrtcvad.Vad(2)

    max_silence_frames = int(1200 / frame_ms)   # 1.2 s de silencio
    max_speech_frames = int(4000 / frame_ms)    # máx 4 s de chunk

    speech_buf: list = []
    silence_frames = 0
    processing = False

    def _check_chunk(audio_data: np.ndarray) -> None:
        nonlocal processing
        try:
            model = _get_wake_model()
            cfg = load_config()
            lang = cfg["stt"]["language"]
            segments, _ = model.transcribe(audio_data, language=lang, beam_size=1)
            text = " ".join(s.text for s in segments).strip().lower()
            if wake_word.lower() in text:
                if log_fn:
                    log_fn(f"Wake word detectada: '{text}'")
                on_detected(text)
        finally:
            processing = False

    try:
        with sd.InputStream(samplerate=sr, channels=1, dtype="int16",
                            blocksize=frame_size) as stream:
            while not stop_event.is_set():
                chunk, _ = stream.read(frame_size)
                flat = chunk.flatten()

                try:
                    is_speech = vad.is_speech(flat.tobytes(), sr)
                except Exception:
                    is_speech = False

                if is_speech:
                    speech_buf.append(flat)
                    silence_frames = 0
                elif speech_buf:
                    speech_buf.append(flat)
                    silence_frames += 1

                    should_check = (
                        silence_frames >= max_silence_frames
                        or len(speech_buf) >= max_speech_frames
                    )

                    if should_check and not processing:
                        audio = np.concatenate(speech_buf).astype(np.float32) / 32768.0
                        speech_buf = []
                        silence_frames = 0
                        processing = True
                        t = threading.Thread(target=_check_chunk, args=(audio,), daemon=True)
                        t.start()
    except Exception:
        pass
