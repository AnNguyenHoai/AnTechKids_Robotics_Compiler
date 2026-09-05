"""RoboStudio first-flash bootstrap configuration helpers."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = ROOT / ".robostudio" / "bootstrap"


class BootstrapConfigService:
    """Generate local-only Wi-Fi/OTA bootstrap data for first-flash."""

    def __init__(self, root: Path | None = None):
        self.root = root or ROOT

    def generate(self, ssid: str, wifi_password: str, ota_password: str,
                 output: Path | None = None) -> Path:
        output = output or (self.root / ".robostudio" / "bootstrap" / "robot_bootstrap.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        # Import the canonical generator instead of duplicating validation or
        # artifact format in the UI layer.
        from tools.bootstrap_config import make_config
        import json

        config = make_config(ssid, wifi_password, ota_password)
        output.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        return output

    def validate(self, path: Path) -> bool:
        from tools.bootstrap_config import validate_config
        validate_config(path.resolve())
        return True

    def forget_local_artifact(self, path: Path) -> None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
