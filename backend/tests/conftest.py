"""Shared fixtures for all tests."""

import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure backend/ is on path so 'app' imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load .env before importing app
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    """Async HTTP client bound to the FastAPI app (no real server needed)."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
