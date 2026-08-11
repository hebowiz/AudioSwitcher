"""Isolated Windows policy API for the system default output endpoint.

IPolicyConfig is undocumented. This module intentionally contains the CLSID,
IID, and vtable index so a future Windows compatibility fix stays local.
"""

from __future__ import annotations

import ctypes
from collections.abc import Iterator
from contextlib import contextmanager
from ctypes import wintypes

import comtypes
from comtypes import GUID

CLSID_POLICY_CONFIG_CLIENT = GUID("{870AF99C-171D-4F9E-AF0D-E63DF40C2BC9}")
IID_POLICY_CONFIG = GUID("{F8679F50-850A-41CF-9C72-430F290290C8}")
CLSCTX_ALL = 23
VTABLE_RELEASE = 2
VTABLE_SET_DEFAULT_ENDPOINT = 13
E_CONSOLE = 0
E_MULTIMEDIA = 1


class DefaultAudioPolicyError(RuntimeError):
    pass


@contextmanager
def _policy_config_pointer() -> Iterator[ctypes.c_void_p]:
    comtypes.CoInitialize()
    pointer = ctypes.c_void_p()
    try:
        result = ctypes.windll.ole32.CoCreateInstance(
            ctypes.byref(CLSID_POLICY_CONFIG_CLIENT),
            None,
            CLSCTX_ALL,
            ctypes.byref(IID_POLICY_CONFIG),
            ctypes.byref(pointer),
        )
        if result < 0:
            raise DefaultAudioPolicyError(
                f"IPolicyConfigを作成できません (HRESULT 0x{result & 0xFFFFFFFF:08X})"
            )
        yield pointer
    finally:
        if pointer:
            vtable = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            release = ctypes.WINFUNCTYPE(wintypes.ULONG, ctypes.c_void_p)(vtable[VTABLE_RELEASE])
            release(pointer)
        comtypes.CoUninitialize()


class WindowsDefaultAudioPolicy:
    """Set eConsole and eMultimedia together; communications is left unchanged."""

    def set_default_endpoint(self, device_id: str) -> None:
        with _policy_config_pointer() as pointer:
            vtable = ctypes.cast(pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            set_default = ctypes.WINFUNCTYPE(
                ctypes.c_long,
                ctypes.c_void_p,
                wintypes.LPCWSTR,
                ctypes.c_int,
            )(vtable[VTABLE_SET_DEFAULT_ENDPOINT])
            for role in (E_CONSOLE, E_MULTIMEDIA):
                result = int(set_default(pointer, device_id, role))
                if result < 0:
                    raise DefaultAudioPolicyError(
                        "既定の出力デバイスを変更できません "
                        f"(role={role}, HRESULT 0x{result & 0xFFFFFFFF:08X})"
                    )
