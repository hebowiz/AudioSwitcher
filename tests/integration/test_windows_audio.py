"""Opt-in smoke tests for the real Windows audio environment."""

import os

import pytest

from audio_switcher.platform.windows.audio_endpoints import WindowsAudioEndpoints

pytestmark = pytest.mark.skipif(
    os.environ.get("AUDIOSWITCHER_RUN_AUDIO_TESTS") != "1",
    reason="Set AUDIOSWITCHER_RUN_AUDIO_TESTS=1 to access real audio endpoints.",
)


def test_list_active_endpoints() -> None:
    endpoints = WindowsAudioEndpoints().list_active()

    assert endpoints
    assert all(device.id and device.name for device in endpoints)
