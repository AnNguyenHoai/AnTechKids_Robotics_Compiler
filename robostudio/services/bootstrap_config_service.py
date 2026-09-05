"""RoboStudio first-flash bootstrap configuration helpers."""
from __future__ import annotations

import json
from pathlib import Path

import tools.bootstrap_config as bootstrap_config

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

        try:
            config = bootstrap_config.make_config(ssid, wifi_password, ota_password)
            output.write_text(
                json.dumps(config, indent=2) + "\n", encoding="utf-8"
            )
        except (OSError, ValueError) as exc:
            raise RuntimeError(
                str(exc) or "Unable to generate bootstrap config."
            ) from exc
        return output

    def validate(self, path: Path) -> bool:
        try:
            bootstrap_config.validate_config(path.resolve())
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        return True
