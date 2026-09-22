"""Static production contract for the ESP32 USB first-flash payload.

Metadata/version closure is necessary but not sufficient: an interrupted or
incorrectly staged PlatformIO package can still carry ``package.json`` while
missing board/framework files that the compiler needs. PlatformIO also enables
several filesystem tools dynamically on the ESP32 USB upload path although they
are optional in the platform manifest. This module verifies both the physical
framework/toolchain files and every package RoboStudio expects to be available
offline before a release can be accepted.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


class FirstFlashRuntimeContractError(RuntimeError):
    """Raised when the packaged ESP32 first-flash runtime is incomplete."""


REQUIRED_RUNTIME_FILES: tuple[str, ...] = (
    "platforms/espressif32/boards/esp32dev.json",
    "packages/framework-arduinoespressif32/.piopm",
    "packages/framework-arduinoespressif32/cores/esp32/Arduino.h",
    "packages/framework-arduinoespressif32/variants/esp32/pins_arduino.h",
    "packages/toolchain-xtensa-esp32/.piopm",
    "packages/toolchain-xtensa-esp32/bin/xtensa-esp32-elf-g++.exe",
    "packages/tool-esptoolpy/.piopm",
    "packages/tool-esptoolpy/esptool.py",
    "packages/tool-scons/.piopm",
    "packages/tool-scons/package.json",
    "packages/tool-mkspiffs/.piopm",
    "packages/tool-mkspiffs/package.json",
    "packages/tool-mklittlefs/.piopm",
    "packages/tool-mklittlefs/package.json",
    "packages/tool-mkfatfs/.piopm",
    "packages/tool-mkfatfs/package.json",
)


def _json_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FirstFlashRuntimeContractError(f"Invalid {label}: {path}") from exc
    if not isinstance(value, dict):
        raise FirstFlashRuntimeContractError(f"Invalid {label}: expected JSON object: {path}")
    return value


def validate_esp32dev_first_flash_payload(runtime_platformio: Path) -> dict[str, object]:
    """Validate physical files used by the pinned ESP32 Arduino USB path."""
    runtime = Path(runtime_platformio).expanduser().resolve()
    missing = [relative for relative in REQUIRED_RUNTIME_FILES if not (runtime / relative).is_file()]
    if missing:
        raise FirstFlashRuntimeContractError(
            "Packaged ESP32 first-flash runtime is incomplete; missing: " + ", ".join(missing)
        )

    board = _json_object(
        runtime / "platforms" / "espressif32" / "boards" / "esp32dev.json",
        "esp32dev board manifest",
    )
    build = board.get("build")
    if not isinstance(build, dict):
        raise FirstFlashRuntimeContractError("esp32dev board manifest has no build object")
    variant = str(build.get("variant", "")).strip()
    if variant != "esp32":
        raise FirstFlashRuntimeContractError(
            f"esp32dev board variant changed unexpectedly: {variant!r}; compatibility review required"
        )

    pins = runtime / "packages" / "framework-arduinoespressif32" / "variants" / variant / "pins_arduino.h"
    if not pins.is_file():
        raise FirstFlashRuntimeContractError(
            f"Arduino board variant header is missing for esp32dev: {pins}"
        )

    return {
        "target": "esp32dev",
        "framework": "arduino",
        "variant": variant,
        "required_files": list(REQUIRED_RUNTIME_FILES),
        "required_file_count": len(REQUIRED_RUNTIME_FILES),
        "usb_upload_packages": [
            "tool-esptoolpy",
            "tool-mkspiffs",
            "tool-mklittlefs",
            "tool-mkfatfs",
            "tool-scons",
        ],
    }


def validate_archive_inventory(paths: Iterable[str]) -> None:
    """Require the same critical payload to survive final ZIP assembly."""
    archived = {str(path).replace("\\", "/") for path in paths}
    missing = [
        f"runtime/platformio/{relative}"
        for relative in REQUIRED_RUNTIME_FILES
        if f"runtime/platformio/{relative}" not in archived
    ]
    if missing:
        raise FirstFlashRuntimeContractError(
            "Production ZIP dropped ESP32 first-flash runtime files: " + ", ".join(missing)
        )
