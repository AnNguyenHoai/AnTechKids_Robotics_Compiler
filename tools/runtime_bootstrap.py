"""Portable RoboStudio application launch and environment bootstrap.

This module is the single startup boundary for RoboStudio. It separates three
locations that must not be confused:

* the application root: the directory containing the distributed executable;
* the frozen bundle root: PyInstaller's import/resource area;
* the user data root: writable per-user state.

The bootstrap never changes the current working directory and never searches
PATH for RoboStudio-owned runtime components. Frozen mode also prepares an
application-owned PlatformIO environment before any deployment subprocess is
started.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from tools import runtime_paths

RUNTIME_MODE_ENV = "ROBOSTUDIO_RUNTIME_MODE"
RUNTIME_MODE_SOURCE = "source"
RUNTIME_MODE_FROZEN = "packaged"
PLATFORMIO_CORE_DIR_ENV = "PLATFORMIO_CORE_DIR"
PLATFORMIO_PLATFORMS_DIR_ENV = "PLATFORMIO_PLATFORMS_DIR"
PLATFORMIO_PACKAGES_DIR_ENV = "PLATFORMIO_PACKAGES_DIR"
PLATFORMIO_CACHE_DIR_ENV = "PLATFORMIO_CACHE_DIR"
PLATFORMIO_BUILD_CACHE_DIR_ENV = "PLATFORMIO_BUILD_CACHE_DIR"
PLATFORMIO_WORKSPACE_DIR_ENV = "PLATFORMIO_WORKSPACE_DIR"
PLATFORMIO_DISABLE_UPGRADE_CHECK_ENV = "PLATFORMIO_DISABLE_UPGRADE_CHECK"
PLATFORMIO_DISABLE_PROGRESSBAR_ENV = "PLATFORMIO_DISABLE_PROGRESSBAR"
PLATFORMIO_NO_ANSI_ENV = "PLATFORMIO_NO_ANSI"


class RuntimeBootstrapError(RuntimeError):
    """Raised when the application bootstrap contract cannot be satisfied."""


@dataclass(frozen=True)
class RuntimeContext:
    """Resolved launch locations and the environment prepared for children."""

    application_root: Path
    bundle_root: Path
    user_data_root: Path
    frozen: bool
    environment: dict[str, str]


def is_frozen() -> bool:
    """Return whether the current process is a frozen RoboStudio executable."""
    return bool(getattr(sys, "frozen", False))


def application_root() -> Path:
    """Return the directory owned by the installed RoboStudio application."""
    override = os.environ.get(runtime_paths.APPLICATION_HOME_ENV)
    if override:
        return Path(override).expanduser().resolve()
    if is_frozen():
        # In a frozen process sys.executable is the executable the user launched;
        # __file__ may instead point inside PyInstaller's _internal/_MEIPASS area.
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def bundle_root() -> Path:
    """Return the import/resource root of the running application bundle."""
    if is_frozen():
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass).resolve()
    return Path(__file__).resolve().parents[1]


def _runtime_environment(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Create a deterministic child-process environment."""
    env = dict(os.environ if base_env is None else base_env)
    if not is_frozen():
        return env

    root = application_root()
    core = root / "runtime" / "platformio"
    env.setdefault(runtime_paths.APPLICATION_HOME_ENV, str(root))
    env[RUNTIME_MODE_ENV] = RUNTIME_MODE_FROZEN
    env.update(
        {
            PLATFORMIO_CORE_DIR_ENV: str(core),
            PLATFORMIO_PLATFORMS_DIR_ENV: str(core / "platforms"),
            PLATFORMIO_PACKAGES_DIR_ENV: str(core / "packages"),
            PLATFORMIO_CACHE_DIR_ENV: str(core / ".cache"),
            PLATFORMIO_BUILD_CACHE_DIR_ENV: str(core / "build-cache"),
            PLATFORMIO_WORKSPACE_DIR_ENV: str(core / "workspace"),
            PLATFORMIO_DISABLE_UPGRADE_CHECK_ENV: "true",
            PLATFORMIO_DISABLE_PROGRESSBAR_ENV: "true",
            PLATFORMIO_NO_ANSI_ENV: "true",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    return env


def bootstrap_environment(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return the environment that RoboStudio should give to child processes."""
    return _runtime_environment(base_env)


def bootstrap_import_path() -> list[Path]:
    """Make bundled modules and application-owned source modules importable."""
    roots = [bundle_root()]
    if application_root() != bundle_root():
        roots.append(application_root())
    for root in reversed(roots):
        value = str(root)
        if value not in sys.path:
            sys.path.insert(0, value)
    return roots


def bootstrap(*, apply: bool = True, validate_runtime: bool = False) -> RuntimeContext:
    """Bootstrap RoboStudio before the GUI or deployment services are imported.

    ``apply=False`` is useful for deterministic tests: it resolves the same
    contract without mutating process environment or ``sys.path``.

    ``validate_runtime=True`` performs the strict RSD-06 packaged-distribution
    preflight. The check is only meaningful in frozen mode; source development
    remains intentionally compatible with the existing repository workflow.
    """
    roots = bootstrap_import_path() if apply else [bundle_root(), application_root()]
    env = bootstrap_environment()
    if apply:
        os.environ.update(env)
    root = application_root()
    frozen = is_frozen()
    if validate_runtime and frozen:
        from tools.runtime_preflight import validate_distribution

        try:
            validate_distribution(root)
        except Exception as exc:
            raise RuntimeBootstrapError(
                "RoboStudio packaged runtime preflight failed: "
                f"{exc}"
            ) from exc
    return RuntimeContext(
        application_root=root,
        bundle_root=roots[0],
        user_data_root=runtime_paths.user_data_root(),
        frozen=frozen,
        environment=env,
    )


bootstrap_application = bootstrap


if __name__ == "__main__":
    context = bootstrap()
    print(f"RoboStudio runtime mode: {RUNTIME_MODE_FROZEN if context.frozen else RUNTIME_MODE_SOURCE}")
    print(f"Application root: {context.application_root}")
    print(f"Bundle root: {context.bundle_root}")
    print(f"User data root: {context.user_data_root}")
