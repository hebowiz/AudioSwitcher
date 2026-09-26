"""Resolve persisted audio devices against the endpoints currently exposed by Windows."""

from __future__ import annotations

from collections.abc import Iterable

from audio_switcher.domain.models import AudioDevice


def normalized_device_name(name: str) -> str:
    """Normalize harmless display-name differences without guessing across real renames."""
    return " ".join(name.split()).casefold()


def resolve_device(
    configured: AudioDevice,
    active_devices: Iterable[AudioDevice],
) -> AudioDevice | None:
    """Resolve by stable ID first, then by a unique exact display-name match."""
    active = list(active_devices)
    configured_id = configured.id.casefold()
    for device in active:
        if device.id.casefold() == configured_id:
            return device

    configured_name = normalized_device_name(configured.name)
    name_matches = [
        device for device in active if normalized_device_name(device.name) == configured_name
    ]
    return name_matches[0] if len(name_matches) == 1 else None


def resolve_devices(
    configured_devices: Iterable[AudioDevice],
    active_devices: Iterable[AudioDevice],
) -> list[AudioDevice]:
    """Resolve in configured order and never return the same live endpoint twice."""
    active = list(active_devices)
    resolved: list[AudioDevice] = []
    resolved_ids: set[str] = set()
    for configured in configured_devices:
        device = resolve_device(configured, active)
        if device is None or device.id.casefold() in resolved_ids:
            continue
        resolved.append(device)
        resolved_ids.add(device.id.casefold())
    return resolved
