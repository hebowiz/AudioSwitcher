"""Core Audio endpoint enumeration and lookup."""

from __future__ import annotations

import winappaudiorouter as audio_router

from audio_switcher.domain.models import AudioDevice


class WindowsAudioEndpoints:
    def list_active(self) -> list[AudioDevice]:
        return [
            AudioDevice(id=device.id, name=device.name or device.id)
            for device in audio_router.list_output_devices()
        ]

    def get_system_default_id(self) -> str | None:
        for device in audio_router.list_output_devices():
            if device.is_default:
                return device.id
        return None
