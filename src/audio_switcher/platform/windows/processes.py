"""Executable and process discovery."""

from __future__ import annotations

import os
from pathlib import Path

import psutil


def normalized_executable_path(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def process_executable_path(process_id: int) -> str | None:
    try:
        return psutil.Process(process_id).exe()
    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess, OSError):
        return None


def executable_matches(process_id: int, configured_path: str) -> bool:
    actual_path = process_executable_path(process_id)
    return actual_path is not None and normalized_executable_path(
        actual_path
    ) == normalized_executable_path(configured_path)


def executable_display_name(path: str) -> str:
    return Path(path).stem or Path(path).name
