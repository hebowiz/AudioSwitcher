"""Domain models shared by the UI, storage, and switching service."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from uuid import uuid4


class TargetKind(StrEnum):
    APPLICATION = "application"
    SYSTEM_DEFAULT = "system_default"


@dataclass(frozen=True, slots=True)
class AudioDevice:
    id: str
    name: str

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "name": self.name}

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> AudioDevice:
        return cls(id=str(value["id"]), name=str(value["name"]))


@dataclass(frozen=True, slots=True)
class Hotkey:
    sequence: str

    def __post_init__(self) -> None:
        normalized = self.sequence.strip()
        if not normalized:
            raise ValueError("ショートカットを設定してください。")
        object.__setattr__(self, "sequence", normalized)


@dataclass(slots=True)
class SwitchTarget:
    kind: TargetKind
    name: str
    hotkey: Hotkey
    devices: list[AudioDevice]
    executable_path: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("対象名を入力してください。")
        if self.kind is TargetKind.APPLICATION:
            if not self.executable_path:
                raise ValueError("対象exeを選択してください。")
            self.executable_path = str(Path(self.executable_path).resolve())
        else:
            self.executable_path = None
        if len(self.devices) < 2:
            raise ValueError("出力デバイスを2つ以上登録してください。")
        if len({device.id.casefold() for device in self.devices}) != len(self.devices):
            raise ValueError("同じ出力デバイスを重複して登録できません。")

    @property
    def display_name(self) -> str:
        return self.name

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "name": self.name,
            "executable_path": self.executable_path,
            "hotkey": self.hotkey.sequence,
            "devices": [device.to_dict() for device in self.devices],
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> SwitchTarget:
        raw_devices = value.get("devices", [])
        if not isinstance(raw_devices, list):
            raise TypeError("devices must be a list")
        return cls(
            id=str(value.get("id") or uuid4()),
            kind=TargetKind(str(value["kind"])),
            name=str(value["name"]),
            executable_path=(
                str(value["executable_path"]) if value.get("executable_path") else None
            ),
            hotkey=Hotkey(str(value["hotkey"])),
            devices=[AudioDevice.from_dict(item) for item in raw_devices if isinstance(item, dict)],
        )


@dataclass(slots=True)
class AppSettings:
    targets: list[SwitchTarget] = field(default_factory=list)
    version: int = 1

    def __post_init__(self) -> None:
        system_targets = [
            target for target in self.targets if target.kind is TargetKind.SYSTEM_DEFAULT
        ]
        if len(system_targets) > 1:
            raise ValueError("Windows全体の設定は1件だけ登録できます。")
        sequences = [target.hotkey.sequence.casefold() for target in self.targets]
        if len(set(sequences)) != len(sequences):
            raise ValueError("同じショートカットを複数の対象へ登録できません。")

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "targets": [target.to_dict() for target in self.targets],
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> AppSettings:
        raw_targets = value.get("targets", [])
        if not isinstance(raw_targets, list):
            raise TypeError("targets must be a list")
        return cls(
            version=int(value.get("version", 1)),
            targets=[
                SwitchTarget.from_dict(item) for item in raw_targets if isinstance(item, dict)
            ],
        )
