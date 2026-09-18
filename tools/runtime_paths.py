"""Deterministic runtime paths and application-owned tool/state resolution.

RoboStudio must run from a packaged directory without depending on the
repository checkout, the current working directory, or executables installed
on the user's PATH.  The packaged application root is immutable: mutable
settings, caches and build state belong to an external per-user state root.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Mapping


APPLICATION_HOME_ENV = "ROBOSTUDIO_HOME"
STATE_ROOT_ENV = "ROBOSTUDIO_STATE_ROOT"
PORTABLE_DATA_ENV = "ROBOSTUDIO_PORTABLE_DATA"  # legacy source-mode switch
RUNTIME_MODE_ENV = "ROBOSTUDIO_RUNTIME_MODE"
DEPENDENCY_MODE_ENV = "ROBOSTUDIO_DEPENDENCY_MODE"


class RuntimePathError(RuntimeError):
    """Raised when a packaged runtime resource/tool/state path is unsafe."""


def is_frozen() -> bool:
    """Return whether RoboStudio is running as a packaged executable."""
    return bool(getattr(sys, "frozen", False))


def _packaged_mode(environment: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environment is None else environment
    return (
        is_frozen()
        or env.get(RUNTIME_MODE_ENV) == "packaged"
        or env.get(DEPENDENCY_MODE_ENV) == "artifact-closed"
    )


def _canonical(path: Path | str) -> Path:
    value = os.path.expanduser(str(path))
    return Path(os.path.normcase(os.path.realpath(os.path.abspath(value))))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


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


def runtime_root() -> Path:
    """Return the application-owned runtime directory."""
    return application_root() / "runtime"


def platformio_runtime_root() -> Path:
    """Return the immutable application-owned PlatformIO payload directory."""
    return runtime_root() / "platformio"


def _default_user_data_root(environment: Mapping[str, str]) -> Path:
    local_app_data = environment.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data).expanduser() / "RoboStudio"
    home = environment.get("USERPROFILE") or environment.get("HOME")
    if home:
        return Path(home).expanduser() / ".robostudio"
    return Path.home() / ".robostudio"


def validate_external_state_root(
    state_root: Path | str,
    *,
    application_root_override: Path | str | None = None,
) -> Path:
    """Require mutable state to live outside the immutable application tree."""
    candidate = _canonical(state_root)
    app = _canonical(application_root_override or application_root())
    if candidate == app or _is_relative_to(candidate, app):
        raise RuntimePathError(
            "RoboStudio mutable state must be outside the application/release root: "
            f"state={candidate}, application={app}"
        )
    return candidate


def user_data_root(
    *,
    base_env: Mapping[str, str] | None = None,
    application_root_override: Path | str | None = None,
    enforce_external: bool | None = None,
) -> Path:
    """Return the writable per-user RoboStudio state directory.

    Packaged/artifact-closed execution never stores mutable data beside the
    executable. ``ROBOSTUDIO_STATE_ROOT`` is the supported explicit override;
    it must be an absolute external path. The historical
    ``ROBOSTUDIO_PORTABLE_DATA`` in-install mode remains available only to
    source/development runs for compatibility and is rejected in production.
    """
    env = os.environ if base_env is None else base_env
    app = Path(application_root_override or application_root()).expanduser()
    packaged = _packaged_mode(env) if enforce_external is None else enforce_external

    explicit = str(env.get(STATE_ROOT_ENV, "")).strip()
    if explicit:
        candidate = Path(explicit).expanduser()
        if not candidate.is_absolute():
            raise RuntimePathError(
                f"{STATE_ROOT_ENV} must be an absolute path: {explicit!r}"
            )
    elif str(env.get(PORTABLE_DATA_ENV, "")).strip().lower() in {"1", "true", "yes"}:
        if packaged:
            raise RuntimePathError(
                f"{PORTABLE_DATA_ENV} cannot place mutable state inside a packaged "
                f"RoboStudio release; use {STATE_ROOT_ENV} with an external path."
            )
        candidate = app / "data"
    else:
        candidate = _default_user_data_root(env)

    candidate = _canonical(candidate)
    if packaged:
        candidate = validate_external_state_root(
            candidate, application_root_override=app
        )
    return candidate


def prepare_user_data_root(
    *,
    base_env: Mapping[str, str] | None = None,
    application_root_override: Path | str | None = None,
    enforce_external: bool | None = None,
) -> Path:
    """Create and verify the writable external state root, failing fast."""
    root = user_data_root(
        base_env=base_env,
        application_root_override=application_root_override,
        enforce_external=enforce_external,
    )
    try:
        root.mkdir(parents=True, exist_ok=True)
        if not root.is_dir():
            raise OSError("state root exists but is not a directory")
        probe = root / f".robostudio-write-probe-{os.getpid()}-{uuid.uuid4().hex}"
        probe.write_bytes(b"state-write-probe")
        probe.unlink()
    except OSError as exc:
        raise RuntimePathError(
            f"RoboStudio state root is not writable: {root}: {exc}"
        ) from exc
    return root


def resolve_path(*parts: str | os.PathLike[str], writable: bool = False) -> Path:
    """Resolve a path without depending on the caller's current directory.

    Read-only resources are rooted in the application. Writable paths are
    rooted in external user state for packaged execution.
    """
    if writable:
        root = user_data_root()
    elif os.environ.get(APPLICATION_HOME_ENV):
        root = Path(os.environ[APPLICATION_HOME_ENV]).expanduser()
    else:
        root = application_root()
    return root.joinpath(*(Path(part) for part in parts))


def _tool_root() -> Path:
    """Return the application-owned root used for bundled artifact identity."""
    override = os.environ.get(APPLICATION_HOME_ENV)
    if override:
        return Path(override).expanduser()
    return application_root()


def _tool_candidates(name: str) -> list[Path]:
    """Return supported locations for a bundled executable."""
    suffixes = [""]
    if os.name == "nt":
        suffixes = [".exe", ".cmd", ".bat", ""]
    root = _tool_root()
    return [
        root / "runtime" / "bin" / f"{name}{suffix}"
        for suffix in suffixes
    ] + [
        root / "runtime" / "tools" / f"{name}{suffix}"
        for suffix in suffixes
    ]


def resolve_bundled_tool(name: str) -> Path | None:
    """Find a tool shipped inside the RoboStudio distribution without PATH."""
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
    """Build a PlatformIO command without depending on PATH."""
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
