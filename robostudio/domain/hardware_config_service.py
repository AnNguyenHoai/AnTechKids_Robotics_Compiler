"""Persistence service for RoboStudio hardware configuration.

Packaged hardware defaults are read-only application data. User changes are
mutable state and therefore live under RoboStudio's external user-data root.
"""

import json
from pathlib import Path
from typing import Optional

from tools.runtime_paths import application_root, user_data_root

from .hardware_config import HardwareConfig


class HardwareConfigService:
    """Load packaged defaults and persist user hardware configuration externally."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is not None:
            # Preserve the explicit-path contract used by tests and integrations.
            self.package_config_path = Path(config_path)
            self.user_config_path = Path(config_path)
            self.config_path = Path(config_path)
            return

        self.user_config_path = user_data_root() / "hardware.json"
        self.config_path = self.user_config_path

        # Source mode keeps the historical robostudio/config default. A frozen
        # distribution may stage the same read-only default at <app>/config.
        source_default = Path(__file__).resolve().parent.parent / "config" / "hardware.json"
        application_default = application_root() / "config" / "hardware.json"
        self.package_config_path = (
            application_default if application_default.is_file() else source_default
        )

    def load(self) -> HardwareConfig:
        """Load user state first, then immutable packaged defaults."""
        for path in (self.user_config_path, self.package_config_path):
            try:
                with open(path, "r", encoding="utf-8") as stream:
                    return HardwareConfig.from_dict(json.load(stream))
            except FileNotFoundError:
                continue
            except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
                # Invalid user state must not cause the package default to be
                # overwritten or mutated. Fall through to the next safe source.
                continue

        config = HardwareConfig.create_default()
        self.save(config)
        return config

    def save(self, config: HardwareConfig) -> None:
        """Persist only to the writable user-state location."""
        self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.user_config_path, "w", encoding="utf-8") as stream:
            json.dump(config.to_dict(), stream, indent=2, ensure_ascii=False)
            stream.write("\n")
