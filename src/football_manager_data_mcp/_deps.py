"""FastAPI dependency providers that read from app.state at request time."""

from __future__ import annotations

import re
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Request, Response

from football_manager_data_mcp.catalog import FootballCatalog
from football_manager_data_mcp.data_lifecycle import DataLifecycleService
from football_manager_data_mcp.explanations import ExplanationSettings

SESSION_COOKIE_NAME = "fm_session_id"
_SESSION_ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")


def get_session_id(request: Request, response: Response) -> str:
    existing = request.cookies.get(SESSION_COOKIE_NAME, "").strip().lower()
    if _SESSION_ID_PATTERN.fullmatch(existing):
        return existing

    session_id = uuid4().hex
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return session_id


def get_catalog(
    request: Request,
    session_id: Annotated[str, Depends(get_session_id)],
) -> FootballCatalog:
    return request.app.state.data_lifecycle.get_catalog(session_id=session_id)


def get_data_lifecycle(request: Request) -> DataLifecycleService:
    return request.app.state.data_lifecycle


def get_explanation_settings(request: Request) -> ExplanationSettings:
    return request.app.state.explanation_settings
