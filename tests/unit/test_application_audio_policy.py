from audio_switcher.platform.windows.application_audio_policy import (
    WindowsApplicationAudioPolicy,
)
from audio_switcher.platform.windows.audio_sessions import ResolvedAudioSession


class FakeSessions:
    def __init__(self, sessions: list[ResolvedAudioSession]) -> None:
        self.sessions = sessions

    def for_executable(self, executable_path: str) -> list[ResolvedAudioSession]:
        assert executable_path == "C:/Apps/player.exe"
        return self.sessions


def test_persisted_route_is_preferred(monkeypatch) -> None:
    sessions = FakeSessions([ResolvedAudioSession(process_id=42, device_id="actual")])
    monkeypatch.setattr(
        "audio_switcher.platform.windows.application_audio_policy."
        "audio_router.get_app_output_device",
        lambda process_id: {process_id: "persisted"},
    )
    policy = WindowsApplicationAudioPolicy(sessions)  # type: ignore[arg-type]

    assert policy.get_current_endpoint_id("C:/Apps/player.exe") == "persisted"


def test_actual_session_route_is_used_without_persisted_route(monkeypatch) -> None:
    sessions = FakeSessions([ResolvedAudioSession(process_id=42, device_id="actual")])
    monkeypatch.setattr(
        "audio_switcher.platform.windows.application_audio_policy."
        "audio_router.get_app_output_device",
        lambda process_id: {},
    )
    policy = WindowsApplicationAudioPolicy(sessions)  # type: ignore[arg-type]

    assert policy.get_current_endpoint_id("C:/Apps/player.exe") == "actual"


def test_set_route_updates_each_resolved_process(monkeypatch) -> None:
    sessions = FakeSessions(
        [
            ResolvedAudioSession(process_id=42, device_id="a"),
            ResolvedAudioSession(process_id=43, device_id="a"),
            ResolvedAudioSession(process_id=42, device_id="b"),
        ]
    )
    calls: list[tuple[int, str]] = []
    monkeypatch.setattr(
        "audio_switcher.platform.windows.application_audio_policy."
        "audio_router.set_app_output_device",
        lambda *, process_id, device: calls.append((process_id, device)),
    )
    policy = WindowsApplicationAudioPolicy(sessions)  # type: ignore[arg-type]

    policy.set_endpoint("C:/Apps/player.exe", "target")

    assert calls == [(42, "target"), (43, "target")]
