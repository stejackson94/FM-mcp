from __future__ import annotations

import logging
import threading
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from football_manager_data_mcp.catalog import FootballCatalog


class DataLifecycleService:
    def __init__(
        self,
        input_data_dir: Path,
        uploaded_data_dir: Path,
        required_columns: set[str],
        auto_clear_uploads: bool,
        auto_clear_uploads_interval_seconds: int,
        logger: logging.Logger,
    ) -> None:
        self.input_data_dir = input_data_dir
        self.uploaded_data_dir = uploaded_data_dir
        self.required_columns = required_columns
        self.auto_clear_uploads = auto_clear_uploads
        self.auto_clear_uploads_interval_seconds = auto_clear_uploads_interval_seconds
        self.logger = logger

        self.uploaded_data_dir.mkdir(parents=True, exist_ok=True)
        self.catalog = self._build_catalog()

        self._cleanup_stop_event = threading.Event()
        self._cleanup_thread: threading.Thread | None = None

    def uploaded_html_files(self) -> list[Path]:
        return sorted(self.uploaded_data_dir.glob("*.html"))

    def delete_files(self, files: Iterable[Path]) -> int:
        removed = 0
        for file_path in files:
            if not file_path.exists():
                continue
            file_path.unlink()
            removed += 1
        return removed

    def _build_catalog(self) -> FootballCatalog:
        if self.uploaded_html_files():
            return FootballCatalog(input_data_dir=self.uploaded_data_dir)
        return FootballCatalog()

    def reload_catalog(self) -> None:
        self.catalog = self._build_catalog()

    def active_mode(self) -> str:
        return "uploaded" if self.uploaded_html_files() else "default"

    def validate_columns(self, new_catalog: FootballCatalog) -> list[str]:
        available_columns = {
            str(item["column"]) for item in new_catalog.list_available_columns() if "column" in item
        }
        return sorted(self.required_columns - available_columns)

    def data_status(self) -> dict[str, Any]:
        uploaded_files = [file_path.name for file_path in self.uploaded_html_files()]
        return {
            "mode": self.active_mode(),
            "uploaded_files": uploaded_files,
            "player_count": len(self.catalog._players),
        }

    def upload_html(self, filename: str, raw_content: bytes) -> dict[str, Any]:
        if not filename.lower().endswith(".html"):
            raise HTTPException(status_code=400, detail="Only .html files are supported.")
        if not raw_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        self.delete_files(self.uploaded_html_files())
        destination = self.uploaded_data_dir / "uploaded.html"
        destination.write_bytes(raw_content)

        new_catalog = FootballCatalog(input_data_dir=self.uploaded_data_dir)
        if not new_catalog._players:
            destination.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail=(
                    "No players could be parsed from this file. "
                    "Use an FM player-search HTML export."
                ),
            )

        missing_columns = self.validate_columns(new_catalog)
        if missing_columns:
            destination.unlink(missing_ok=True)
            raise HTTPException(
                status_code=400,
                detail=("Uploaded HTML is missing required columns: " + ", ".join(missing_columns)),
            )

        self.catalog = new_catalog
        return {
            "mode": "uploaded",
            "uploaded_files": [destination.name],
            "player_count": len(self.catalog._players),
        }

    def clear_data(self) -> dict[str, Any]:
        removed = self.delete_files(self.uploaded_html_files())
        self.reload_catalog()
        return {
            "removed_files": removed,
            "mode": self.active_mode(),
            "player_count": len(self.catalog._players),
        }

    def _auto_cleanup_uploaded_data(self) -> None:
        interval = max(self.auto_clear_uploads_interval_seconds, 60)
        while not self._cleanup_stop_event.wait(interval):
            removed = self.delete_files(self.uploaded_html_files())
            if removed > 0:
                self.reload_catalog()
                self.logger.info("Auto-cleared %s uploaded file(s)", removed)

    def start_background_tasks(self) -> None:
        if not self.auto_clear_uploads:
            self.logger.info("Auto-clear uploads disabled")
            return
        self._cleanup_stop_event.clear()
        self._cleanup_thread = threading.Thread(
            target=self._auto_cleanup_uploaded_data, daemon=True
        )
        self._cleanup_thread.start()

    def stop_background_tasks(self) -> None:
        self._cleanup_stop_event.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=1)
