"""Pydantic models and constants for the Automations module."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


VALID_ACTION_TYPES = [
    "backup_db",
    "cleanup_temp",
    "reindex_documents",
    "health_check",
    "custom_script",
]


class TaskCreateModel(BaseModel):
    name: str
    schedule_cron: Optional[str] = None
    action_type: str
    action_config: Optional[dict] = None
    enabled: bool = True
    timeout_seconds: int = 300
    max_retries: int = 1


class TaskUpdateModel(BaseModel):
    name: Optional[str] = None
    schedule_cron: Optional[str] = None
    action_type: Optional[str] = None
    action_config: Optional[dict] = None
    enabled: Optional[bool] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None


class ShortcutCreate(BaseModel):
    name: str
    icon: str = "Zap"
    color: str = "#3b82f6"
    url_or_action: str
    sort_order: int = 0


class ShortcutUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    url_or_action: Optional[str] = None
    sort_order: Optional[int] = None


class MonitorCreate(BaseModel):
    name: str
    url: str
    interval_seconds: int = 300
    enabled: bool = True


class MonitorUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    interval_seconds: Optional[int] = None
    enabled: Optional[bool] = None


class NotifyRequest(BaseModel):
    """Internal notification request from any module."""
    source: str
    title: str
    message: str
    severity: str = "info"


class ApiTestRequest(BaseModel):
    method: str = "GET"
    url: str
    headers: Optional[dict] = None
    body: Optional[str] = None


class ApiTestSave(BaseModel):
    name: str
    method: str = "GET"
    url: str
    headers: Optional[dict] = None
    body: Optional[str] = None


class NotificationCreate(BaseModel):
    title: str
    message: str
    type: str = "info"
    source: str | None = None
    link: str | None = None


def row_dict(row) -> dict:
    """Convert an aiosqlite.Row to a plain dict."""
    return dict(row)
