"""
FirmwareService – manages firmware project path and opening
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from tools.runtime_paths import application_root, user_data_root


class FirmwareService:
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is not None:
            # Explicit paths are retained for tests/integration callers and
            # preserve the historical service contract.
            self.package_config_path = Path(config_path)
            self.user_config_path = Path(config_path)
            self.config_path = Path(config_path)
        else:
            self.package_config_path = application_root() / "config" / "config.json"
            self.user_config_path = user_data_root() / "config.json"
            self.config_path = self.user_config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        # User settings are writable and machine-specific. Packaged defaults
        # remain read-only application data and are used only when no user
        # configuration exists yet.
        for path in (self.user_config_path, self.package_config_path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
        return {"compiler_command": "robot", "firmware_project": ""}

    def _save_config(self):
        self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.user_config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def _find_firmware_file(self) -> Optional[Path]:
        """Auto-detect firmware from the application-owned distribution root."""
        workspace_root = application_root()
        candidates = [
            workspace_root / "firmware" / "main" / "main.ino",
            workspace_root / "firmware" / "RobotVM.ino",
            workspace_root / "robot-platform" / "main" / "main.ino",
            workspace_root / "robot-platform" / "RobotVM.ino",
        ]
        for path in candidates:
            if path.is_file():
                return path
        return None

    def get_firmware_path(self) -> Optional[Path]:
        """Return configured path or auto-detected application firmware path."""
        configured = str(self.config.get("firmware_project", "")).strip()
        if configured:
            path = Path(configured)
            if not path.is_absolute():
                path = application_root() / path
            if path.is_file():
                return path
        return self._find_firmware_file()

    def set_firmware_path(self, path: Path):
        """Save a relocatable application-relative path when possible."""
        path = Path(path).expanduser()
        root = application_root()
        try:
            relative = path.resolve().relative_to(root.resolve())
        except ValueError:
            self.config["firmware_project"] = str(path.resolve())
        else:
            self.config["firmware_project"] = relative.as_posix()
        self._save_config()

    def open_firmware(self):
        """Open the firmware file with the default application."""
        ino_file = self.get_firmware_path()
        if ino_file is None:
            raise FileNotFoundError(
                "Could not locate firmware project.\n"
                "Please select the main.ino or RobotVM.ino file."
            )

        if os.name == "nt":
            os.startfile(str(ino_file))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(ino_file)], check=False)
        else:
            subprocess.run(["xdg-open", str(ino_file)], check=False)
