"""Persistence service for RoboStudio hardware.json."""

import json
from pathlib import Path
from typing import Optional

from .hardware_config import HardwareConfig


class HardwareConfigService:
    """Loads and saves the hardware configuration source of truth."""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).resolve().parent.parent / "config" / "hardware.json"
        self.config_path = Path(config_path)

    def load(self) -> HardwareConfig:
        if not self.config_path.exists():
            config = HardwareConfig.create_default()
            self.save(config)
            return config

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return HardwareConfig.from_dict(data)

    def save(self, config: HardwareConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            f.write("\n")
