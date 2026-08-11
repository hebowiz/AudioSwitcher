"""Isolated Windows Audio Policy API for per-application routing.

The underlying interface is undocumented and may change between Windows builds.
All calls to it are deliberately contained in this adapter.
"""

from __future__ import annotations

import winappaudiorouter as audio_router

from audio_switcher.platform.windows.audio_sessions import AudioSessionResolver


class ApplicationAudioPolicyError(RuntimeError):
    pass


class WindowsApplicationAudioPolicy:
    def __init__(self, sessions: AudioSessionResolver) -> None:
        self._sessions = sessions

    def get_current_endpoint_id(self, executable_path: str) -> str | None:
        sessions = self._sessions.for_executable(executable_path)
        if not sessions:
            raise ApplicationAudioPolicyError(
                "対象アプリのアクティブなAudio Sessionが見つかりません。"
            )

        persisted: list[str] = []
        for process_id in sorted({session.process_id for session in sessions}):
            routes = audio_router.get_app_output_device(process_id=process_id)
            route = routes.get(process_id)
            if route:
                persisted.append(route)

        if persisted:
            first = persisted[0]
            if all(route.casefold() == first.casefold() for route in persisted):
                return first

        # No explicit route means the actual session endpoint is the best current-state source.
        return sessions[0].device_id

    def set_endpoint(self, executable_path: str, device_id: str) -> None:
        sessions = self._sessions.for_executable(executable_path)
        process_ids = sorted({session.process_id for session in sessions})
        if not process_ids:
            raise ApplicationAudioPolicyError(
                "対象アプリのアクティブなAudio Sessionが見つかりません。"
            )
        for process_id in process_ids:
            audio_router.set_app_output_device(process_id=process_id, device=device_id)
