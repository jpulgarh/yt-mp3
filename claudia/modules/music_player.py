"""
Módulo: Reproductor de música local.
Gestiona la reproducción de archivos MP3 descargados usando el reproductor configurado.
"""

import subprocess
from pathlib import Path
from .base import BaseModule
from ..core.config import load as load_config


class MusicPlayerModule(BaseModule):
    name = "music_player"
    description = "Reproduce archivos MP3 locales de tu carpeta de música"

    _proc: subprocess.Popen = None

    def execute(self, action: str, params: dict) -> str:
        cfg = load_config()
        music_dir = Path(cfg["paths"]["music_dir"])
        player = cfg["player"]["preferred"]
        player_opts = cfg["player"]["options"].get(player, [])

        if action == "play_all":
            return self._play(sorted(music_dir.rglob("*.mp3")), player, player_opts)

        if action == "play_playlist":
            name = params.get("playlist", "").strip()
            return self._play_by_name(music_dir, name, player, player_opts)

        if action == "stop":
            return self._stop()

        if action == "list":
            return self._list(music_dir)

        return "Comando de música no reconocido."

    def _play(self, files: list, player: str, opts: list) -> str:
        files = list(files)
        if not files:
            return "No encontré archivos MP3 en tu carpeta de música."
        self._stop()
        try:
            self._proc = subprocess.Popen(
                [player] + opts + [str(f) for f in files],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return f"Reproduciendo {len(files)} canciones."
        except FileNotFoundError:
            fallback = load_config()["player"]["fallback"]
            if fallback != player:
                return self._play(files, fallback, [])
            return (
                f"No encontré el reproductor '{player}'. "
                "¿Qué reproductor quieres usar? Por ejemplo: mpg123, audacious o vlc."
            )

    def _play_by_name(self, music_dir: Path, name: str, player: str, opts: list) -> str:
        playlists = [d for d in music_dir.iterdir() if d.is_dir()]
        if not name:
            if not playlists:
                return "No hay listas de reproducción descargadas todavía."
            names = ", ".join(p.name for p in playlists[:10])
            return f"Tengo estas listas: {names}. ¿Cuál quieres escuchar?"

        match = next(
            (p for p in playlists if name.lower() in p.name.lower()), None
        )
        if not match:
            available = ", ".join(p.name for p in playlists[:5])
            return (
                f"No encontré una lista llamada '{name}'. "
                f"Las disponibles son: {available}."
            )
        return self._play(sorted(match.glob("*.mp3")), player, opts)

    def _stop(self) -> str:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            self._proc = None
            return "Música detenida."
        self._proc = None
        return "No hay música reproduciéndose en este momento."

    def _list(self, music_dir: Path) -> str:
        if not music_dir.exists():
            return f"La carpeta de música {music_dir} no existe todavía."
        playlists = [d.name for d in music_dir.iterdir() if d.is_dir()]
        if not playlists:
            return "No hay listas descargadas. Puedes descargar una con 'Hey Claudia, descarga esta lista: [URL]'."
        return "Listas disponibles: " + ", ".join(playlists) + "."
