"""Portable PlatformIO build workspace isolation for RoboStudio."""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Mapping

from tools import runtime_paths

PLATFORMIO_WORKSPACE_DIR_ENV = "PLATFORMIO_WORKSPACE_DIR"
PLATFORMIO_BUILD_DIR_ENV = "PLATFORMIO_BUILD_DIR"
PLATFORMIO_LIBDEPS_DIR_ENV = "PLATFORMIO_LIBDEPS_DIR"
PLATFORMIO_CACHE_DIR_ENV = "PLATFORMIO_CACHE_DIR"
PLATFORMIO_BUILD_CACHE_DIR_ENV = "PLATFORMIO_BUILD_CACHE_DIR"
PLATFORMIO_SHARED_DIR_ENV = "PLATFORMIO_SHARED_DIR"

BUILD_DATA_DIRECTORY = "build"
DEFAULT_PROJECT_NAME = "robostudio"


class BuildIsolationError(RuntimeError):
    """Raised when an isolated build workspace cannot be safely resolved."""


def _validate_project_name(project_name: str) -> str:
    value = str(project_name).strip()
    if not value or value in {".", ".."}:
        raise BuildIsolationError("Build project name must not be empty or relative.")
    if Path(value).name != value or "/" in value or "\\" in value:
        raise BuildIsolationError(
            f"Build project name must be a single path component: {project_name!r}"
        )
    if any(ord(char) < 32 for char in value):
        raise BuildIsolationError("Build project name contains control characters.")
    if re.fullmatch(r"(?i)(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\..*)?", value):
        raise BuildIsolationError(f"Build project name is reserved: {project_name!r}")
    return value


def _state_root(base_env: Mapping[str, str] | None = None) -> Path:
    return runtime_paths.user_data_root(base_env=base_env)


def build_root(
    project_name: str = DEFAULT_PROJECT_NAME,
    *,
    base_env: Mapping[str, str] | None = None,
) -> Path:
    name = _validate_project_name(project_name)
    return _state_root(base_env) / BUILD_DATA_DIRECTORY / name


def build_workspace(project_name: str = DEFAULT_PROJECT_NAME, *, base_env: Mapping[str, str] | None = None) -> Path:
    return build_root(project_name, base_env=base_env) / "platformio"


def build_dir(project_name: str = DEFAULT_PROJECT_NAME, *, base_env: Mapping[str, str] | None = None) -> Path:
    return build_workspace(project_name, base_env=base_env) / "build"


def libdeps_dir(project_name: str = DEFAULT_PROJECT_NAME, *, base_env: Mapping[str, str] | None = None) -> Path:
    return build_workspace(project_name, base_env=base_env) / "libdeps"


def cache_dir(project_name: str = DEFAULT_PROJECT_NAME, *, base_env: Mapping[str, str] | None = None) -> Path:
    return build_workspace(project_name, base_env=base_env) / "cache"


def build_cache_dir(project_name: str = DEFAULT_PROJECT_NAME, *, base_env: Mapping[str, str] | None = None) -> Path:
    return build_workspace(project_name, base_env=base_env) / "build-cache"


def shared_dir(project_name: str = DEFAULT_PROJECT_NAME, *, base_env: Mapping[str, str] | None = None) -> Path:
    return build_workspace(project_name, base_env=base_env) / "shared"


def prepare_build_workspace(
    project_name: str = DEFAULT_PROJECT_NAME,
    *,
    base_env: Mapping[str, str] | None = None,
) -> Path:
    """Create a writable workspace after fail-fast state-root validation."""
    env = os.environ if base_env is None else base_env
    try:
        runtime_paths.prepare_user_data_root(base_env=env)
    except runtime_paths.RuntimePathError as exc:
        raise BuildIsolationError(f"Unable to prepare RoboStudio build state: {exc}") from exc

    workspace = build_workspace(project_name, base_env=env)
    directories = (
        workspace,
        build_dir(project_name, base_env=env),
        libdeps_dir(project_name, base_env=env),
        cache_dir(project_name, base_env=env),
        build_cache_dir(project_name, base_env=env),
        shared_dir(project_name, base_env=env),
    )
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise BuildIsolationError(
                f"Unable to create isolated build directory {directory}: {exc}"
            ) from exc
    return workspace


def build_environment(
    project_name: str = DEFAULT_PROJECT_NAME,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return one environment snapshot with all writable build paths isolated."""
    env = dict(os.environ if base_env is None else base_env)
    name = _validate_project_name(project_name)
    paths = {
        PLATFORMIO_WORKSPACE_DIR_ENV: build_workspace(name, base_env=env),
        PLATFORMIO_BUILD_DIR_ENV: build_dir(name, base_env=env),
        PLATFORMIO_LIBDEPS_DIR_ENV: libdeps_dir(name, base_env=env),
        PLATFORMIO_CACHE_DIR_ENV: cache_dir(name, base_env=env),
        PLATFORMIO_BUILD_CACHE_DIR_ENV: build_cache_dir(name, base_env=env),
        PLATFORMIO_SHARED_DIR_ENV: shared_dir(name, base_env=env),
    }
    env.update({key: str(value) for key, value in paths.items()})
    return env


def firmware_path(
    project_name: str,
    environment: str,
    *,
    filename: str = "firmware.bin",
    base_env: Mapping[str, str] | None = None,
) -> Path:
    name = _validate_project_name(project_name)
    env_name = str(environment).strip()
    if not env_name or Path(env_name).name != env_name or "/" in env_name or "\\" in env_name:
        raise BuildIsolationError(f"Invalid PlatformIO environment name: {environment!r}")
    if not filename or Path(filename).name != filename or "/" in filename or "\\" in filename:
        raise BuildIsolationError(f"Invalid firmware filename: {filename!r}")
    return build_dir(name, base_env=base_env) / env_name / filename


def clean_build_workspace(
    project_name: str = DEFAULT_PROJECT_NAME,
    *,
    base_env: Mapping[str, str] | None = None,
) -> None:
    root = build_root(project_name, base_env=base_env)
    data_root = _state_root(base_env)
    if root == data_root or root.parent != data_root / BUILD_DATA_DIRECTORY:
        raise BuildIsolationError(f"Refusing to clean unsafe build workspace: {root}")
    if root.exists():
        if not root.is_dir():
            raise BuildIsolationError(f"Build workspace is not a directory: {root}")
        shutil.rmtree(root)


resolve_build_workspace = build_workspace
resolve_build_dir = build_dir
resolve_build_environment = build_environment
resolve_firmware_path = firmware_path
