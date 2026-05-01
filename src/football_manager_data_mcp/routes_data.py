"""Routes for data lifecycle management: upload, status, clear, FM views download."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from football_manager_data_mcp._deps import get_data_lifecycle, get_session_id
from football_manager_data_mcp.data_lifecycle import DataLifecycleService

router = APIRouter()

_package_root_dir = Path(__file__).resolve().parent
_project_root_dir = Path(__file__).resolve().parents[2]
_frontend_dir = _package_root_dir / "frontend"
_fm_views_dirs = [
    _project_root_dir / "fm_views",
    _package_root_dir / "fm_views",
]
_required_view_files = [
    "General Metrics search.fmf",
    "General Metrics scouted.fmf",
]


def _resolve_required_view_file(filename: str) -> Path | None:
    for base_dir in _fm_views_dirs:
        candidate = base_dir / filename
        if candidate.is_file():
            return candidate
    return None


@router.get("/")
def index() -> FileResponse:
    return FileResponse(_frontend_dir / "index.html")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/api/data-status")
def api_data_status(
    data_lifecycle: Annotated[DataLifecycleService, Depends(get_data_lifecycle)],
    session_id: Annotated[str, Depends(get_session_id)],
) -> dict[str, Any]:
    return data_lifecycle.data_status(session_id=session_id)


@router.get("/api/download-required-views")
def api_download_required_views() -> Response:
    resolved_files = {name: _resolve_required_view_file(name) for name in _required_view_files}
    missing_files = [name for name, path in resolved_files.items() if path is None]
    if missing_files:
        raise HTTPException(
            status_code=404,
            detail=("Required FM view files are missing: " + ", ".join(sorted(missing_files))),
        )

    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in _required_view_files:
            archive.write(resolved_files[filename], arcname=filename)

    return Response(
        content=archive_buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": 'attachment; filename="fm-required-views.zip"',
        },
    )


@router.post("/api/upload")
async def api_upload(
    data_lifecycle: Annotated[DataLifecycleService, Depends(get_data_lifecycle)],
    session_id: Annotated[str, Depends(get_session_id)],
    file: Annotated[UploadFile, File(...)],
) -> dict[str, Any]:
    filename = file.filename or "upload.html"
    raw_content = await file.read()
    return data_lifecycle.upload_html(
        filename=filename,
        raw_content=raw_content,
        session_id=session_id,
    )


@router.post("/api/clear-data")
def api_clear_data(
    data_lifecycle: Annotated[DataLifecycleService, Depends(get_data_lifecycle)],
    session_id: Annotated[str, Depends(get_session_id)],
) -> dict[str, Any]:
    return data_lifecycle.clear_data(session_id=session_id)
