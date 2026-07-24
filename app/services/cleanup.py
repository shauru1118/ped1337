from __future__ import annotations

import threading
import time
from pathlib import Path

from loguru import logger


class TempCleanupService:
    """Periodically removes stale temp and visualization artifacts."""

    def __init__(
        self,
        temp_dir: Path,
        generated_dir: Path,
        max_age_seconds: int = 300,
        interval_seconds: int = 60,
    ) -> None:
        self.temp_dir = temp_dir
        self.generated_dir = generated_dir
        self.max_age_seconds = max_age_seconds
        self.interval_seconds = interval_seconds
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="temp-cleanup", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.run_once()
            except Exception as exc:  # noqa: BLE001
                logger.error(f"Error during periodic cleanup: {exc}")
            self._stop.wait(self.interval_seconds)

    def run_once(self) -> None:
        cutoff = time.time() - self.max_age_seconds
        self._purge_dir(self.temp_dir, cutoff)
        self._purge_dir(self.generated_dir, cutoff, prefix="vis_")

    @staticmethod
    def _purge_dir(
        directory: Path, cutoff: float, prefix: str | None = None
    ) -> None:
        if not directory.exists():
            return
        for item in directory.iterdir():
            if not item.is_file():
                continue
            if prefix and not item.name.startswith(prefix):
                continue
            try:
                if item.stat().st_mtime < cutoff:
                    item.unlink()
            except OSError:
                continue
