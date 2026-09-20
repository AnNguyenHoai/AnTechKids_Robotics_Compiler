"""Prepare isolated, writable PlatformIO firmware projects."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from tools import build_isolation

FORBIDDEN_NAMES = frozenset(
    {".git", ".venv", ".pio", "penv", "__pycache__", ".pytest_cache"}
)
RUNS_DIRECTORY = "runs"
FIRMWARE_DIRECTORY = "firmware"


class FirmwareWorkspaceError(RuntimeError):
    pass


def _find_forbidden(root: Path) -> list[str]:
    """Return forbidden developer/build payload paths below ``root``."""
    return [
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if any(x.lower() in FORBIDDEN_NAMES for x in p.relative_to(root).parts)
    ]


def validate_firmware_template(root: Path) -> Path:
    """Validate the source firmware template's required project structure.

    Source/development checkouts may legitimately contain transient build payload
    such as ``.pio`` or ``__pycache__`` after a local PlatformIO/Python run. Those
    directories are not part of the firmware template contract and are filtered
    while staging. Rejecting them here makes otherwise valid local source trees
    unusable even though ``prepare_firmware_workspace`` never copies them.
    """
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise FirmwareWorkspaceError(f"Firmware project not found: {root}")
    for name in ("platformio.ini", "wifi_config.py"):
        if not (root / name).is_file():
            raise FirmwareWorkspaceError(f"Firmware project is missing {name}: {root}")
    if not (root / "main").is_dir():
        raise FirmwareWorkspaceError(f"Firmware project is missing main/: {root}")
    return root


def _runs_root(project_name: str) -> Path:
    """Return the per-project root that owns disposable firmware source copies."""
    return build_isolation.build_workspace(project_name) / RUNS_DIRECTORY


def prepare_firmware_workspace(template_root: Path, project_name: str) -> Path:
    """Create a fresh firmware source workspace for one deployment run.

    Older implementations reused ``<platformio>/firmware`` and deleted it before
    every run. On Windows, a PlatformIO/esptool descendant can briefly outlive
    its parent while keeping its current working directory or another handle
    inside that tree. Deleting the fixed workspace then fails with WinError 32.

    Every deployment now gets a new source workspace. Build/cache/libdeps paths
    remain governed by ``build_isolation`` and are therefore unchanged. A stale
    or locked source workspace from an earlier run cannot block a new run.
    """
    template = validate_firmware_template(template_root)
    runs_root = _runs_root(project_name)
    try:
        runs_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise FirmwareWorkspaceError(
            f"Unable to create firmware run workspace root {runs_root}: {exc}"
        ) from exc

    # uuid4 collisions are practically impossible, but retry a few times so the
    # function remains fail-closed if a fixture or filesystem injects one.
    last_error: OSError | None = None
    for _ in range(4):
        run_root = runs_root / uuid.uuid4().hex
        destination = run_root / FIRMWARE_DIRECTORY
        try:
            shutil.copytree(
                template,
                destination,
                ignore=shutil.ignore_patterns(*FORBIDDEN_NAMES),
            )
        except FileExistsError as exc:
            last_error = exc
            continue
        except OSError as exc:
            shutil.rmtree(run_root, ignore_errors=True)
            raise FirmwareWorkspaceError(
                f"Unable to prepare firmware workspace {destination}: {exc}"
            ) from exc

        # The source tree may contain transient local artifacts, but the staged
        # firmware workspace is a strict boundary: none of them may cross it.
        forbidden = _find_forbidden(destination)
        if forbidden:
            shutil.rmtree(run_root, ignore_errors=True)
            raise FirmwareWorkspaceError(
                "Staged firmware workspace contains forbidden developer/build payload: "
                + ", ".join(sorted(forbidden))
            )
        return destination

    raise FirmwareWorkspaceError(
        f"Unable to allocate a unique firmware workspace below {runs_root}: {last_error}"
    )


def cleanup_firmware_workspace(firmware_root: Path, project_name: str) -> bool:
    """Best-effort removal of one per-run firmware workspace.

    Cleanup is intentionally non-fatal. Windows may keep a directory handle open
    for a short time after PlatformIO/esptool exits. A cleanup failure must not
    turn an otherwise successful flash into an error, and because workspaces are
    per-run it cannot block the next deployment.

    Returns ``True`` when the run workspace is absent after cleanup, otherwise
    ``False`` when the OS still has it locked.
    """
    firmware = Path(firmware_root).expanduser().resolve()
    expected_runs = _runs_root(project_name).expanduser().resolve()
    run_root = firmware.parent
    if (
        firmware.name != FIRMWARE_DIRECTORY
        or run_root.parent != expected_runs
        or not run_root.name
    ):
        raise FirmwareWorkspaceError(
            f"Refusing to clean unsafe firmware workspace: {firmware}"
        )
    if not run_root.exists():
        return True
    if not run_root.is_dir():
        raise FirmwareWorkspaceError(
            f"Firmware run workspace is not a directory: {run_root}"
        )
    try:
        shutil.rmtree(run_root)
    except OSError:
        return False
    return not run_root.exists()


def _copy_generated_header(header: Path, destination: Path, *, label: str) -> Path:
    source = Path(header).expanduser().resolve()
    if not source.is_file():
        raise FirmwareWorkspaceError(f"{label} not found: {source}")
    destination = Path(destination).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def install_generated_header(header: Path, firmware_root: Path) -> Path:
    """Install the compiled student program into the writable firmware copy."""
    destination = (
        Path(firmware_root).resolve()
        / "main"
        / "src"
        / "Application"
        / "generated_program.h"
    )
    return _copy_generated_header(
        header, destination, label="Generated firmware header"
    )


def install_device_config_header(header: Path, firmware_root: Path) -> Path:
    """Overlay the user hardware feature header into the writable firmware copy.

    The immutable release template carries a default header. When RoboStudio has
    generated a user-specific header under external state, deployment overlays
    it only in the isolated build workspace and never writes back to the
    packaged template.
    """
    destination = (
        Path(firmware_root).resolve()
        / "main"
        / "include"
        / "generated"
        / "generated_device_config.h"
    )
    return _copy_generated_header(
        header, destination, label="Generated device configuration header"
    )
