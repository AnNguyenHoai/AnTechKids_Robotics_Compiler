"""Portable PlatformIO build workspace isolation for RoboStudio.

The packaged application owns the compiler/runtime binaries, while generated
PlatformIO state is writable user data.  A deployment build must never create
``.pio`` (or any other build cache) inside the RoboStudio source/install tree.

The public helpers in this module deliberately return absolute paths and do
not inspect the current working directory.  PlatformIO supports these
``PLATFORMIO_*`` directory variables, so the deployment layer can keep the
canonical robot-platform source tree read-only while still producing normal
PlatformIO artifacts.
"""
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
    # PlatformIO creates directories on Windows as well as POSIX. Reject
    # names that are unsafe on either platform so a portable project behaves
    # consistently when moved between machines.
    if re.fullmatch(r"(?i)(con|prn|aux|nul|com[0-9]|lpt[0-9])(?:\..*)?", value):
        raise BuildIsolationError(f"Build project name is reserved: {project_name!r}")
    return value


def build_root(project_name: str = DEFAULT_PROJECT_NAME) -> Path:
    """Return the per-project writable RoboStudio build root."""
    name = _validate_project_name(project_name)
    return runtime_paths.user_data_root() / BUILD_DATA_DIRECTORY / name


def build_workspace(project_name: str = DEFAULT_PROJECT_NAME) -> Path:
    """Return the PlatformIO workspace directory for one RoboStudio project."""
    return build_root(project_name) / "platformio"


def build_dir(project_name: str = DEFAULT_PROJECT_NAME) -> Path:
    """Return the PlatformIO per-environment build output directory."""
    return build_workspace(project_name) / "build"


def libdeps_dir(project_name: str = DEFAULT_PROJECT_NAME) -> Path:
    """Return the isolated PlatformIO library-dependency directory."""
    return build_workspace(project_name) / "libdeps"


def cache_dir(project_name: str = DEFAULT_PROJECT_NAME) -> Path:
    """Return the writable PlatformIO registry/cache directory."""
    return build_workspace(project_name) / "cache"


def build_cache_dir(project_name: str = DEFAULT_PROJECT_NAME) -> Path:
    """Return the isolated PlatformIO compiled-object cache directory."""
    return build_workspace(project_name) / "build-cache"


def shared_dir(project_name: str = DEFAULT_PROJECT_NAME) -> Path:
    """Return the isolated PlatformIO shared workspace directory."""
    return build_workspace(project_name) / "shared"


def prepare_build_workspace(project_name: str = DEFAULT_PROJECT_NAME) -> Path:
    """Create the writable workspace without touching the project source tree."""
    workspace = build_workspace(project_name)
    for directory in (
        workspace,
        build_dir(project_name),
        libdeps_dir(project_name),
        cache_dir(project_name),
        build_cache_dir(project_name),
        shared_dir(project_name),
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return workspace


def build_environment(
    project_name: str = DEFAULT_PROJECT_NAME,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return a subprocess environment with every writable build path isolated.

    Existing caller environment values are deliberately replaced for the
    PlatformIO build/workspace variables. This prevents a host's global
    ``PLATFORMIO_BUILD_DIR`` or workspace from silently defeating portability.
    PlatformIO's core/platform/package locations are left untouched here; the
    deployment runtime owns those separately and points them at the packaged
    runtime when RoboStudio is frozen.
    """
    env = dict(os.environ if base_env is None else base_env)
    name = _validate_project_name(project_name)
    paths = {
        PLATFORMIO_WORKSPACE_DIR_ENV: build_workspace(name),
        PLATFORMIO_BUILD_DIR_ENV: build_dir(name),
        PLATFORMIO_LIBDEPS_DIR_ENV: libdeps_dir(name),
        PLATFORMIO_CACHE_DIR_ENV: cache_dir(name),
        PLATFORMIO_BUILD_CACHE_DIR_ENV: build_cache_dir(name),
        PLATFORMIO_SHARED_DIR_ENV: shared_dir(name),
    }
    env.update({key: str(value) for key, value in paths.items()})
    return env


def firmware_path(
    project_name: str,
    environment: str,
    *,
    filename: str = "firmware.bin",
) -> Path:
    """Return a firmware artifact produced by an isolated PlatformIO build."""
    name = _validate_project_name(project_name)
    env_name = str(environment).strip()
    if not env_name or Path(env_name).name != env_name or "/" in env_name or "\\" in env_name:
        raise BuildIsolationError(f"Invalid PlatformIO environment name: {environment!r}")
    if not filename or Path(filename).name != filename or "/" in filename or "\\" in filename:
        raise BuildIsolationError(f"Invalid firmware filename: {filename!r}")
    return build_dir(name) / env_name / filename


def clean_build_workspace(project_name: str = DEFAULT_PROJECT_NAME) -> None:
    """Remove one isolated build workspace, never a source/install directory."""
    root = build_root(project_name)
    if root == runtime_paths.user_data_root() or root.parent != runtime_paths.user_data_root() / BUILD_DATA_DIRECTORY:
        raise BuildIsolationError(f"Refusing to clean unsafe build workspace: {root}")
    if root.exists():
        if not root.is_dir():
            raise BuildIsolationError(f"Build workspace is not a directory: {root}")
        shutil.rmtree(root)


# Explicit aliases make the contract easy to consume from UI/deployment code.
resolve_build_workspace = build_workspace
resolve_build_dir = build_dir
resolve_build_environment = build_environment
resolve_firmware_path = firmware_path
