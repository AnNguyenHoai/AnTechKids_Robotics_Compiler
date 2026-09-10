"""Deterministic runtime paths and application-owned tool resolution.

RoboStudio must run from a packaged directory without depending on the
repository checkout, the current working directory, or executables installed
on the user's PATH. Source/development runs retain a small compatibility
fallback so existing developer workflows keep working.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


APPLICATION_HOME_ENV = "ROBOSTUDIO_HOME"
PORTABLE_DATA_ENV = "ROBOSTUDIO_PORTABLE_DATA"


class RuntimePathError(RuntimeError):
    """Raised when a packaged runtime resource/tool cannot be resolved."""


def is_frozen() -> bool:
    """Return whether RoboStudio is running as a packaged executable."""
    return bool(getattr(sys, "frozen", False))


def application_root() -> Path:
    """Return the immutable RoboStudio installation/application root.

    ``ROBOSTUDIO_HOME`` is an explicit override for integration tests and
    controlled deployments. A frozen build is rooted at the executable;
    source builds are rooted at the repository containing ``tools/``.
    """
    override = os.environ.get(APPLICATION_HOME_ENV)
    if override:
        return Path(override).expanduser().resolve()
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def user_data_root() -> Path:
    """Return the writable per-user RoboStudio data directory.

    Portable mode is explicit; normal installations use LOCALAPPDATA and do
    not need write permission beside the executable.
    """
    if os.environ.get(PORTABLE_DATA_ENV, "").strip().lower() in {"1", "true", "yes"}:
        return application_root() / "data"
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "RoboStudio"
    return Path.home() / ".robostudio"


def resolve_path(*parts: str | os.PathLike[str], writable: bool = False) -> Path:
    """Resolve an application-owned path without depending on CWD."""
    root = user_data_root() if writable else application_root()
    return root.joinpath(*(Path(part) for part in parts)).resolve()


def _tool_candidates(name: str) -> list[Path]:
    """Return deterministic locations for a bundled executable.

    The release contract is Windows-first, but the resolver intentionally
    recognizes Windows executable suffixes even when the test/build host is
    not Windows. This keeps the package layout contract independent of the
    host OS used to validate the distribution.
    """
    suffixes = [".exe", ".cmd", ".bat", ""]
    candidates: list[Path] = []
    for directory in ("runtime/bin", "runtime/tools"):
        for suffix in suffixes:
            candidates.append(application_root() / directory / f"{name}{suffix}")
    return candidates


def resolve_bundled_tool(name: str) -> Path | None:
    """Find a tool shipped inside the RoboStudio distribution."""
    if not name or Path(name).name != name:
        raise ValueError("Tool name must be a simple executable name.")
    for candidate in _tool_candidates(name):
        if candidate.is_file():
            return candidate
    return None


def python_command(*args: str) -> list[str]:
    """Build a Python command using the private packaged interpreter when present."""
    bundled = resolve_bundled_tool("python")
    if bundled:
        return [str(bundled), *args]
    if is_frozen():
        raise RuntimePathError(
            "RoboStudio packaged runtime is missing runtime/bin/python.exe."
        )
    return [sys.executable, *args]


def platformio_command(*args: str) -> list[str]:
    """Build a PlatformIO command without depending on PATH.

    A packaged Python runtime is preferred because a copied Windows virtual
    environment can retain an absolute interpreter reference and therefore is
    not a safe portable artifact. When the RoboStudio runtime contains Python,
    PlatformIO is launched as a module from that interpreter. A directly
    bundled PlatformIO executable remains supported as a compatibility option.
    """
    bundled_python = resolve_bundled_tool("python")
    if bundled_python:
        return [str(bundled_python), "-m", "platformio", *args]
    for name in ("pio", "platformio"):
        bundled = resolve_bundled_tool(name)
        if bundled:
            return [str(bundled), *args]
    if is_frozen():
        raise RuntimePathError(
            "RoboStudio packaged runtime is missing a deployment runtime: "
            "runtime/bin/python.exe with PlatformIO or runtime/bin/pio.exe."
        )
    return [sys.executable, "-m", "platformio", *args]


def require_bundled_tool(name: str) -> Path:
    """Resolve a mandatory packaged tool and fail with an actionable message."""
    tool = resolve_bundled_tool(name)
    if tool is None:
        raise RuntimePathError(
            f"Required RoboStudio runtime tool is not packaged: {name}"
        )
    return tool
