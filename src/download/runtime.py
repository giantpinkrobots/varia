from __future__ import annotations
from typing import Any, Protocol

class DownloadRuntime(Protocol):
    api: Any
    appconf: dict[str, Any]
    appdir: str
    downloads: list[Any]
    ffmpegexec: str
    jsruntimeexec: dict[str, str]
    ltsession: Any
    scheduler_currently_downloading: bool
    sevenzexec: str
    supported_archive_formats: list[str]
    terminating: bool
