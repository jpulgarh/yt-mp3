"""
Módulo: Descarga de playlists de YouTube como MP3.
Wrapper del script downloader.py adaptado a la arquitectura de módulos.
La carpeta de destino se lee desde config.yaml (paths.music_dir).
"""

import threading
from pathlib import Path

from .base import BaseModule
from ..core.config import load as load_config


class YouTubeDownloaderModule(BaseModule):
    name = "youtube_downloader"
    description = "Descarga listas de reproducción de YouTube como archivos MP3"

    _active_downloads: list = []

    def execute(self, action: str, params: dict) -> str:
        if action == "download":
            url = params.get("url", "").strip()
            if not url or not url.startswith("http"):
                return (
                    "Por favor, indícame la URL completa de la lista de "
                    "reproducción de YouTube que quieres descargar."
                )
            cfg = load_config()
            music_dir = Path(cfg["paths"]["music_dir"])
            music_dir.mkdir(parents=True, exist_ok=True)

            t = threading.Thread(
                target=self._download_bg,
                args=(url, music_dir),
                daemon=True,
            )
            t.start()
            self._active_downloads.append(t)
            return (
                f"Comenzando la descarga en segundo plano. "
                f"Los archivos se guardarán en {music_dir}. "
                "Te avisaré cuando termine."
            )

        return "No entendí el comando de descarga. ¿Puedes repetir la URL de la lista?"

    def _download_bg(self, url: str, output_dir: Path) -> None:
        from ..core.voice import speak
        try:
            import sys
            root = Path(__file__).parent.parent.parent
            sys.path.insert(0, str(root))
            from downloader import download_playlist, normalize_playlist_url
            clean_url, _ = normalize_playlist_url(url)
            download_playlist(url=clean_url, output_base=output_dir)
            speak("La descarga de la lista de reproducción ha terminado.")
        except Exception as e:
            speak(f"Hubo un error al descargar la lista: {e}")
