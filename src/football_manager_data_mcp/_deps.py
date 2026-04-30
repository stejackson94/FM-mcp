"""FastAPI dependency providers that read from app.state at request time."""

from __future__ import annotations

from fastapi import Request

from football_manager_data_mcp.catalog import FootballCatalog
from football_manager_data_mcp.data_lifecycle import DataLifecycleService
from football_manager_data_mcp.explanations import ExplanationSettings


def get_catalog(request: Request) -> FootballCatalog:
    return request.app.state.data_lifecycle.catalog


def get_data_lifecycle(request: Request) -> DataLifecycleService:
    return request.app.state.data_lifecycle


def get_explanation_settings(request: Request) -> ExplanationSettings:
    return request.app.state.explanation_settings
