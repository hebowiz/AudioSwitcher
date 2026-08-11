"""Core Audio session enumeration and executable resolution."""

from __future__ import annotations

from dataclasses import dataclass

import winappaudiorouter as audio_router

from audio_switcher.platform.windows.processes import (
    executable_display_name,
    executable_matches,
    normalized_executable_path,
    process_executable_path,
)


@dataclass(frozen=True, slots=True)
class ResolvedAudioSession:
    process_id: int
    device_id: str


@dataclass(frozen=True, slots=True)
class RunningAudioApplication:
    executable_path: str
    name: str


class AudioSessionResolver:
    def list_running_applications(self) -> list[RunningAudioApplication]:
        applications: dict[str, RunningAudioApplication] = {}
        for session in audio_router.list_app_sessions():
            if session.process_id <= 0:
                continue
            executable_path = process_executable_path(session.process_id)
            if not executable_path:
                continue
            key = normalized_executable_path(executable_path)
            applications.setdefault(
                key,
                RunningAudioApplication(
                    executable_path=executable_path,
                    name=session.process_name or executable_display_name(executable_path),
                ),
            )
        return sorted(
            applications.values(), key=lambda item: (item.name.casefold(), item.executable_path)
        )

    def for_executable(self, executable_path: str) -> list[ResolvedAudioSession]:
        sessions: list[ResolvedAudioSession] = []
        seen: set[tuple[int, str]] = set()
        for session in audio_router.list_app_sessions():
            if session.process_id <= 0 or not executable_matches(
                session.process_id, executable_path
            ):
                continue
            key = (session.process_id, session.device_id.casefold())
            if key in seen:
                continue
            seen.add(key)
            sessions.append(
                ResolvedAudioSession(
                    process_id=session.process_id,
                    device_id=session.device_id,
                )
            )
        return sessions
