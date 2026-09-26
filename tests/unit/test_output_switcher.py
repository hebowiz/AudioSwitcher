from dataclasses import dataclass

import pytest

from audio_switcher.domain.models import AudioDevice, Hotkey, SwitchTarget, TargetKind
from audio_switcher.services.output_switcher import OutputSwitcher, SwitchError


@dataclass
class FakeEndpoints:
    active: list[AudioDevice]
    default_id: str | None = None

    def list_active(self) -> list[AudioDevice]:
        return self.active

    def get_system_default_id(self) -> str | None:
        return self.default_id


@dataclass
class FakeApplicationPolicy:
    current_id: str | None = None
    changed_to: str | None = None

    def get_current_endpoint_id(self, executable_path: str) -> str | None:
        assert executable_path
        return self.current_id

    def set_endpoint(self, executable_path: str, device_id: str) -> None:
        assert executable_path
        self.changed_to = device_id


@dataclass
class FakeDefaultPolicy:
    changed_to: str | None = None

    def set_default_endpoint(self, device_id: str) -> None:
        self.changed_to = device_id


DEVICES = [AudioDevice("a", "A"), AudioDevice("b", "B"), AudioDevice("c", "C")]


def app_target() -> SwitchTarget:
    return SwitchTarget(
        kind=TargetKind.APPLICATION,
        name="Player",
        executable_path="C:/Apps/player.exe",
        hotkey=Hotkey("Ctrl+Alt+F9"),
        devices=list(DEVICES),
    )


def system_target() -> SwitchTarget:
    return SwitchTarget(
        kind=TargetKind.SYSTEM_DEFAULT,
        name="Windows全体",
        hotkey=Hotkey("Ctrl+Alt+F10"),
        devices=list(DEVICES),
    )


def test_application_cycles_from_current_endpoint() -> None:
    app_policy = FakeApplicationPolicy(current_id="b")
    switcher = OutputSwitcher(FakeEndpoints(list(DEVICES)), app_policy, FakeDefaultPolicy())

    result = switcher.switch(app_target())

    assert result.device.id == "c"
    assert app_policy.changed_to == "c"


def test_system_default_cycles_and_skips_disconnected() -> None:
    endpoints = FakeEndpoints([DEVICES[0], DEVICES[2]], default_id="a")
    default_policy = FakeDefaultPolicy()
    switcher = OutputSwitcher(endpoints, FakeApplicationPolicy(), default_policy)

    result = switcher.switch(system_target())

    assert result.device.id == "c"
    assert default_policy.changed_to == "c"


def test_unknown_current_endpoint_starts_at_first_active_device() -> None:
    endpoints = FakeEndpoints(list(DEVICES), default_id="outside")
    default_policy = FakeDefaultPolicy()
    switcher = OutputSwitcher(endpoints, FakeApplicationPolicy(), default_policy)

    result = switcher.switch(system_target())

    assert result.device.id == "a"


def test_no_registered_device_is_active() -> None:
    switcher = OutputSwitcher(FakeEndpoints([]), FakeApplicationPolicy(), FakeDefaultPolicy())

    with pytest.raises(SwitchError, match="接続されていません"):
        switcher.switch(app_target())


def test_changed_endpoint_ids_are_automatically_rebound_by_name() -> None:
    active = [AudioDevice("new-a", "A"), AudioDevice("new-b", "B")]
    app_policy = FakeApplicationPolicy(current_id="new-a")
    switcher = OutputSwitcher(FakeEndpoints(active), app_policy, FakeDefaultPolicy())

    result = switcher.switch(app_target())

    assert result.device.id == "new-b"
    assert app_policy.changed_to == "new-b"
