"""
FirmwareService – manages firmware project path and opening
"""

import os
import subprocess
import sys
import json
from pathlib import Path
from typing import Optional


class FirmwareService:
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "config.json"
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "compiler_command": "robot",
                "firmware_project": ""
            }

    def _save_config(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def _find_firmware_file(self) -> Optional[Path]:
        """Auto‑detect main.ino or RobotVM.ino."""
        workspace_root = Path(__file__).parent.parent.parent
        candidates = [
            workspace_root / "robot-platform" / "main" / "main.ino",
            workspace_root / "robot-platform" / "RobotVM.ino",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def get_firmware_path(self) -> Optional[Path]:
        """Return configured path or auto‑detected path."""
        configured = self.config.get("firmware_project", "")
        if configured:
            p = Path(configured)
            if p.exists():
                return p
        return self._find_firmware_file()

    def set_firmware_path(self, path: Path):
        """Save the given path to config."""
        self.config["firmware_project"] = str(path)
        self._save_config()

    def open_firmware(self):
        """Open the firmware file with default application."""
        ino_file = self.get_firmware_path()
        if ino_file is None:
            raise FileNotFoundError(
                "Could not locate firmware project.\n"
                "Please select the main.ino or RobotVM.ino file."
            )

        # Open with default application
        if os.name == "nt":
            os.startfile(str(ino_file))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(ino_file)])
        else:
            subprocess.run(["xdg-open", str(ino_file)])