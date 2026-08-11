from types import SimpleNamespace

from audio_switcher.platform.windows.audio_sessions import AudioSessionResolver


def test_running_applications_are_built_from_audio_sessions(monkeypatch) -> None:
    sessions = [
        SimpleNamespace(process_id=20, process_name="Beta.exe"),
        SimpleNamespace(process_id=10, process_name="Alpha.exe"),
        SimpleNamespace(process_id=10, process_name="Alpha.exe"),
        SimpleNamespace(process_id=0, process_name=None),
    ]
    paths = {10: "C:/Apps/Alpha.exe", 20: "C:/Apps/Beta.exe"}
    monkeypatch.setattr(
        "audio_switcher.platform.windows.audio_sessions.audio_router.list_app_sessions",
        lambda: sessions,
    )
    monkeypatch.setattr(
        "audio_switcher.platform.windows.audio_sessions.process_executable_path",
        paths.get,
    )

    applications = AudioSessionResolver().list_running_applications()

    assert [(item.name, item.executable_path) for item in applications] == [
        ("Alpha.exe", "C:/Apps/Alpha.exe"),
        ("Beta.exe", "C:/Apps/Beta.exe"),
    ]
