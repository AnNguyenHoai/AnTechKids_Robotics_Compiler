"""Windows-safe short paths for packaged PlatformIO dependencies.

ESP32's legacy Xtensa GCC and portions of the Arduino/PlatformIO build scripts
are sensitive to dependency paths containing whitespace or becoming too long.
The production artifact itself may be extracted anywhere and RoboStudio user
state may live below a Windows profile containing spaces, so dependency
junctions need a deterministic fallback that is independent of both paths.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

SHORT_ROOT_DIRECTORY = "RSC"
MAX_SAFE_ALIAS_BASE_LENGTH = 80


class PlatformIOShortPathError(RuntimeError):
    """Raised when no writable, whitespace-free Windows alias root is available."""


def _is_safe_alias_base(path: Path) -> bool:
    text = str(path)
    return (
        path.is_absolute()
        and len(text) <= MAX_SAFE_ALIAS_BASE_LENGTH
        and not any(char.isspace() for char in text)
    )


def select_windows_alias_base(
    state_root: Path,
    environment: Mapping[str, str],
) -> Path:
    """Return a short whitespace-free base directory for dependency junctions.

    Prefer RoboStudio state when it is already safe. This keeps temporary/test
    state self-contained. If the user profile contains spaces or is too long,
    fall back to the Windows Public profile (normally ``C:\\Users\\Public``),
    which is writable by ordinary users and independent of the account name.

    The function fails closed rather than silently returning the unsafe user
    path that caused first-flash compiler include failures on real machines.
    """
    state_candidate = Path(state_root).expanduser().resolve() / "p"
    if _is_safe_alias_base(state_candidate):
        state_candidate.mkdir(parents=True, exist_ok=True)
        return state_candidate

    public_value = str(environment.get("PUBLIC", "")).strip()
    if not public_value:
        raise PlatformIOShortPathError(
            "Windows PUBLIC profile is unavailable and RoboStudio state is not safe "
            "for the ESP32 PlatformIO dependency alias."
        )

    public_candidate = Path(public_value).expanduser().resolve() / SHORT_ROOT_DIRECTORY
    if not _is_safe_alias_base(public_candidate):
        raise PlatformIOShortPathError(
            "Windows PUBLIC profile is not a short whitespace-free path: "
            f"{public_candidate}"
        )
    try:
        public_candidate.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise PlatformIOShortPathError(
            f"Unable to create Windows PlatformIO short-path root {public_candidate}: {exc}"
        ) from exc
    return public_candidate
