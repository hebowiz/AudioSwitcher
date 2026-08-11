from audio_switcher.platform.windows import startup


class FakeKey:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


def test_startup_command_uses_gui_launcher(monkeypatch) -> None:
    monkeypatch.setattr(startup.sys, "argv", ["C:/Tools/audio-switcher.exe"])
    monkeypatch.delattr(startup.sys, "frozen", raising=False)

    command = startup.startup_command()

    assert command.lower().endswith("audio-switcher.exe")
    assert "-m audio_switcher" not in command


def test_enable_writes_current_user_run_value(monkeypatch) -> None:
    values: list[tuple[str, int, str]] = []
    monkeypatch.setattr(startup.winreg, "CreateKeyEx", lambda *_args: FakeKey())
    monkeypatch.setattr(
        startup.winreg,
        "SetValueEx",
        lambda _key, name, _reserved, value_type, value: values.append((name, value_type, value)),
    )
    monkeypatch.setattr(startup, "startup_command", lambda: "audio-switcher.exe")

    startup.WindowsStartupRegistration().set_enabled(True)

    assert values == [(startup.VALUE_NAME, startup.winreg.REG_SZ, "audio-switcher.exe")]


def test_missing_run_value_is_disabled(monkeypatch) -> None:
    def missing(*_args):
        raise FileNotFoundError

    monkeypatch.setattr(startup.winreg, "OpenKey", missing)

    assert not startup.WindowsStartupRegistration().is_enabled()
