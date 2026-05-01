from __future__ import annotations

import logging
import threading
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from football_manager_data_mcp.catalog import FootballCatalog


@dataclass
class SessionUploadState:
    catalog: FootballCatalog
    file_path: Path
    uploaded_filename: str
    last_used_at: float


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
        self._default_catalog = self._build_catalog()
        self._session_uploads: dict[str, SessionUploadState] = {}
        self._state_lock = threading.RLock()

        self._cleanup_stop_event = threading.Event()
        self._cleanup_thread: threading.Thread | None = None

    @property
    def catalog(self) -> FootballCatalog:
        # Backward-compatible accessor used by tests and older callers.
        return self._default_catalog

    @catalog.setter
    def catalog(self, value: FootballCatalog) -> None:
        self._default_catalog = value

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
        if self.input_data_dir.is_dir() and sorted(self.input_data_dir.glob("*.html")):
            return FootballCatalog(input_data_dir=self.input_data_dir)
        return FootballCatalog()

    @staticmethod
    def _safe_session_key(session_id: str | None) -> str:
        if not session_id:
            return "global"
        normalized = "".join(ch for ch in session_id.lower() if ch.isalnum())
        if not normalized:
            return "global"
        return normalized[:64]

    def _session_upload_path(self, session_id: str) -> Path:
        return self.uploaded_data_dir / f"session_{self._safe_session_key(session_id)}.html"

    def _get_session_upload(self, session_id: str | None) -> SessionUploadState | None:
        if not session_id:
            return None
        state = self._session_uploads.get(session_id)
        if state is None:
            return None
        if not state.file_path.exists():
            self._session_uploads.pop(session_id, None)
            return None
        return state

    def get_catalog(self, session_id: str | None = None) -> FootballCatalog:
        with self._state_lock:
            state = self._get_session_upload(session_id)
            if state is None:
                return self._default_catalog
            state.last_used_at = time.time()
            return state.catalog

    def reload_catalog(self) -> None:
        with self._state_lock:
            self._default_catalog = self._build_catalog()

    def active_mode(self, session_id: str | None = None) -> str:
        with self._state_lock:
            return "uploaded" if self._get_session_upload(session_id) else "default"

    def validate_columns(self, new_catalog: FootballCatalog) -> list[str]:
        available_columns = {
            str(item["column"]) for item in new_catalog.list_available_columns() if "column" in item
        }
        return sorted(self.required_columns - available_columns)

    def data_status(self, session_id: str | None = None) -> dict[str, Any]:
        with self._state_lock:
            state = self._get_session_upload(session_id)
            active_catalog = state.catalog if state else self._default_catalog
            uploaded_files = [state.uploaded_filename] if state else []
            if state:
                state.last_used_at = time.time()

            return {
                "mode": "uploaded" if state else "default",
                "uploaded_files": uploaded_files,
                "player_count": len(active_catalog._players),
            }

    def upload_html(
        self,
        filename: str,
        raw_content: bytes,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        if not filename.lower().endswith(".html"):
            raise HTTPException(status_code=400, detail="Only .html files are supported.")
        if not raw_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        with self._state_lock:
            destination = self._session_upload_path(session_id or "global")
            temp_destination = destination.with_suffix(".tmp.html")
            temp_destination.write_bytes(raw_content)

            new_catalog = FootballCatalog(players_html_path=temp_destination)
            if not new_catalog._players:
                temp_destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "No players could be parsed from this file. "
                        "Use an FM player-search HTML export."
                    ),
                )

            missing_columns = self.validate_columns(new_catalog)
            if missing_columns:
                temp_destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Uploaded HTML is missing required columns: " + ", ".join(missing_columns)
                    ),
                )

            destination.unlink(missing_ok=True)
            temp_destination.replace(destination)

            self._session_uploads[session_id or "global"] = SessionUploadState(
                catalog=new_catalog,
                file_path=destination,
                uploaded_filename=filename,
                last_used_at=time.time(),
            )

        return {
            "mode": "uploaded",
            "uploaded_files": [filename],
            "player_count": len(new_catalog._players),
        }

    def clear_data(self, session_id: str | None = None) -> dict[str, Any]:
        session_key = session_id or "global"
        with self._state_lock:
            state = self._session_uploads.pop(session_key, None)

        removed = 0
        if state is not None:
            removed = self.delete_files([state.file_path])

        active_catalog = self.get_catalog(session_id=session_id)
        return {
            "removed_files": removed,
            "mode": self.active_mode(session_id=session_id),
            "player_count": len(active_catalog._players),
        }

    def _auto_cleanup_uploaded_data(self) -> None:
        interval = max(self.auto_clear_uploads_interval_seconds, 60)
        while not self._cleanup_stop_event.wait(interval):
            now = time.time()
            stale_session_keys: list[str] = []

            with self._state_lock:
                for session_key, state in self._session_uploads.items():
                    if now - state.last_used_at >= interval:
                        stale_session_keys.append(session_key)

                stale_paths = [
                    self._session_uploads[key].file_path
                    for key in stale_session_keys
                    if key in self._session_uploads
                ]

                for key in stale_session_keys:
                    self._session_uploads.pop(key, None)

                managed_paths = {
                    state.file_path.resolve()
                    for state in self._session_uploads.values()
                    if state.file_path.exists()
                }
                orphan_paths = [
                    path
                    for path in self.uploaded_html_files()
                    if path.resolve() not in managed_paths
                    and now - path.stat().st_mtime >= interval
                ]

            removed = self.delete_files(stale_paths + orphan_paths)
            if removed > 0:
                self.logger.info("Auto-cleared %s stale uploaded file(s)", removed)

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
