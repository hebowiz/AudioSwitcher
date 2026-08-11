"""Ordered output-device switching use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from audio_switcher.domain.models import AudioDevice, SwitchTarget, TargetKind


class SwitchError(RuntimeError):
    """A user-facing switching failure."""


class EndpointProvider(Protocol):
    def list_active(self) -> list[AudioDevice]: ...

    def get_system_default_id(self) -> str | None: ...


class ApplicationRoutingPolicy(Protocol):
    def get_current_endpoint_id(self, executable_path: str) -> str | None: ...

    def set_endpoint(self, executable_path: str, device_id: str) -> None: ...


class DefaultRoutingPolicy(Protocol):
    def set_default_endpoint(self, device_id: str) -> None: ...


@dataclass(frozen=True, slots=True)
class SwitchResult:
    target_name: str
    device: AudioDevice


class OutputSwitcher:
    def __init__(
        self,
        endpoints: EndpointProvider,
        application_policy: ApplicationRoutingPolicy,
        default_policy: DefaultRoutingPolicy,
    ) -> None:
        self._endpoints = endpoints
        self._application_policy = application_policy
        self._default_policy = default_policy

    def switch(self, target: SwitchTarget) -> SwitchResult:
        active_by_id = {device.id.casefold(): device for device in self._endpoints.list_active()}
        candidates = [
            active_by_id[configured.id.casefold()]
            for configured in target.devices
            if configured.id.casefold() in active_by_id
        ]
        if not candidates:
            raise SwitchError("登録された出力デバイスが接続されていません。")

        current_id = self._current_endpoint_id(target)
        next_device = self._next_device(candidates, current_id)

        try:
            if target.kind is TargetKind.SYSTEM_DEFAULT:
                self._default_policy.set_default_endpoint(next_device.id)
            else:
                if target.executable_path is None:
                    raise SwitchError("対象exeが設定されていません。")
                self._application_policy.set_endpoint(target.executable_path, next_device.id)
        except SwitchError:
            raise
        except Exception as error:
            raise SwitchError(f"出力先を変更できません: {error}") from error

        return SwitchResult(target_name=target.display_name, device=next_device)

    def _current_endpoint_id(self, target: SwitchTarget) -> str | None:
        try:
            if target.kind is TargetKind.SYSTEM_DEFAULT:
                return self._endpoints.get_system_default_id()
            if target.executable_path is None:
                return None
            return self._application_policy.get_current_endpoint_id(target.executable_path)
        except Exception as error:
            raise SwitchError(f"現在の出力先を取得できません: {error}") from error

    @staticmethod
    def _next_device(candidates: list[AudioDevice], current_id: str | None) -> AudioDevice:
        if current_id is None:
            return candidates[0]
        current_key = current_id.casefold()
        for index, device in enumerate(candidates):
            if device.id.casefold() == current_key:
                return candidates[(index + 1) % len(candidates)]
        return candidates[0]
