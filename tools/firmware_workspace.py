"""Prepare an isolated, writable PlatformIO firmware project."""
from __future__ import annotations

import shutil
from pathlib import Path

from tools import build_isolation

FORBIDDEN_NAMES = frozenset(
    {".git", ".venv", ".pio", "penv", "__pycache__", ".pytest_cache"}
)


class FirmwareWorkspaceError(RuntimeError):
    pass


def validate_firmware_template(root: Path) -> Path:
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise FirmwareWorkspaceError(f"Firmware project not found: {root}")
    for name in ("platformio.ini", "wifi_config.py"):
        if not (root / name).is_file():
            raise FirmwareWorkspaceError(f"Firmware project is missing {name}: {root}")
    if not (root / "main").is_dir():
        raise FirmwareWorkspaceError(f"Firmware project is missing main/: {root}")
    forbidden = [
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if any(x.lower() in FORBIDDEN_NAMES for x in p.relative_to(root).parts)
    ]
    if forbidden:
        raise FirmwareWorkspaceError(
            "Firmware template contains forbidden developer/build payload: "
            + ", ".join(sorted(forbidden))
        )
    return root


def prepare_firmware_workspace(template_root: Path, project_name: str) -> Path:
    template = validate_firmware_template(template_root)
    destination = build_isolation.build_workspace(project_name) / "firmware"
    if destination.exists():
        if not destination.is_dir():
            raise FirmwareWorkspaceError(
                f"Firmware workspace is not a directory: {destination}"
            )
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        template,
        destination,
        ignore=shutil.ignore_patterns(*FORBIDDEN_NAMES),
    )
    return destination


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
