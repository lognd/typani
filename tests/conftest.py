"""Shared pytest fixtures (T-0010): records which Result/Option backend is active."""

from __future__ import annotations

import pytest

import typani


@pytest.fixture(scope="session")
def native_backend_active() -> bool:
    """Session-scoped snapshot of ``typani.native_active()`` for this test run."""
    return typani.native_active()
