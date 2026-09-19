#!/usr/bin/env python3
"""B2.7 regression: firmware source transients must not cross release boundary."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import distribution_package, production_distribution


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_valid_firmware(root: Path) -> None:
    (root / "main").mkdir(parents=True)
    (root / "main" / "main.cpp").write_text(
        "void setup(){}\nvoid loop(){}\n",
        encoding="utf-8",
    )
    (root / "platformio.ini").write_text(
        "[env:esp32dev]\nplatform=espressif32@6.12.0\n",
        encoding="utf-8",
    )
    (root / "wifi_config.py").write_text("Import('env')\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="b27-firmware-source-") as td:
        base = Path(td)
        firmware = base / "robot-platform"
        _write_valid_firmware(firmware)

        # Reproduce the operator failure: a legitimate development/build run has
        # already left transient state in the source firmware workspace.
        (firmware / ".pio" / "build" / "esp32dev").mkdir(parents=True)
        (firmware / ".pio" / "build" / "esp32dev" / "firmware.bin").write_bytes(b"bin")
        (firmware / "main" / "__pycache__").mkdir(parents=True)
        (firmware / "main" / "__pycache__" / "helper.pyc").write_bytes(b"pyc")
        (firmware / "penv" / "Scripts").mkdir(parents=True)
        (firmware / "penv" / "Scripts" / "python.exe").write_bytes(b"exe")

        # Source validation must verify the firmware contract, not require a
        # pristine developer workspace. PlatformIO can create .pio before the
        # production assembler consumes this same source tree.
        production_distribution._validate_firmware(firmware)

        packaged = base / "packaged-firmware"
        distribution_package._copy_firmware(firmware, packaged)

        require((packaged / "platformio.ini").is_file(), "packaged firmware must keep platformio.ini")
        require((packaged / "wifi_config.py").is_file(), "packaged firmware must keep wifi_config.py")
        require((packaged / "main" / "main.cpp").is_file(), "packaged firmware must keep main sources")

        leaked = [
            path.relative_to(packaged).as_posix()
            for path in packaged.rglob("*")
            if any(
                part.lower() in distribution_package.DEVELOPER_PAYLOAD_NAMES
                for part in path.relative_to(packaged).parts
            )
        ]
        require(not leaked, f"developer payload leaked into packaged firmware: {leaked}")
        require(not (packaged / ".pio").exists(), ".pio must be removed at distribution boundary")
        require(not (packaged / "penv").exists(), "penv must be removed at distribution boundary")
        require(not (packaged / "main" / "__pycache__").exists(), "__pycache__ must be removed at distribution boundary")

        # Required firmware markers remain fail-closed even though transient
        # source payload is tolerated.
        (firmware / "platformio.ini").unlink()
        try:
            production_distribution._validate_firmware(firmware)
        except production_distribution.ProductionDistributionError as exc:
            require("platformio.ini" in str(exc), "missing platformio.ini must fail clearly")
        else:
            raise AssertionError("missing platformio.ini unexpectedly passed firmware validation")

    print("B2.7 firmware source transient boundary: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
