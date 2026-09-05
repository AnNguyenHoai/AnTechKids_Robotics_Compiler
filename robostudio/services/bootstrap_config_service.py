"""RoboStudio first-flash bootstrap configuration helpers."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class BootstrapConfigService:
    """Generate and validate local-only Wi-Fi/OTA bootstrap data."""

    def __init__(self, root: Path | None = None):
        self.root = root or ROOT

    def generate(self, ssid: str, wifi_password: str, ota_password: str,
                 output: Path | None = None) -> Path:
        if not ssid.strip():
            raise ValueError("Wi-Fi SSID is required.")
        if not ota_password:
            raise ValueError("OTA password is required for first-flash bootstrap.")
        output = output or (self.root / ".robostudio" / "bootstrap" / "robot_bootstrap.json")
        output.parent.mkdir(parents=True, exist_ok=True)

        command = [
            sys.executable,
            str(self.root / "tools" / "bootstrap_config.py"),
            "generate",
            "--ssid", ssid.strip(),
            "--password", wifi_password,
            "--ota-password", ota_password,
            "--output", str(output),
        ]
        completed = subprocess.run(
            command, cwd=self.root, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
        if completed.returncode != 0:
            raise RuntimeError(
                (completed.stdout or completed.stderr).strip()
                or "Unable to generate bootstrap config."
            )
        return output

    def validate(self, path: Path) -> bool:
        command = [
            sys.executable,
            str(self.root / "tools" / "bootstrap_config.py"),
            "validate",
            "--input", str(path.resolve()),
        ]
        completed = subprocess.run(
            command, cwd=self.root, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
        if completed.returncode != 0:
            raise ValueError(
                (completed.stdout or completed.stderr).strip()
                or "Invalid bootstrap config."
            )
        return True
