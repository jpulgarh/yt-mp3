"""Módulos funcionales de Claudia."""

from .youtube_downloader import YouTubeDownloaderModule
from .music_player import MusicPlayerModule
from .system_monitor import SystemMonitorModule
from .english_tutor import EnglishTutorModule
from .teacher import TeacherModule

ALL_MODULES = [
    YouTubeDownloaderModule(),
    MusicPlayerModule(),
    SystemMonitorModule(),
    EnglishTutorModule(),
    TeacherModule(),
]

MODULE_MAP: dict = {m.name: m for m in ALL_MODULES}
