"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _auto_enable_custom_integrations(
    enable_custom_integrations: object,
) -> None:
    """Load custom_components/ into HA's registry for every test."""


@pytest.fixture
def mock_bluetooth(enable_bluetooth: object) -> Generator[None]:
    """Enable HA's Bluetooth component without touching real adapters."""
    with patch(
        "homeassistant.components.bluetooth.async_register_callback",
        return_value=lambda: None,
    ):
        yield
