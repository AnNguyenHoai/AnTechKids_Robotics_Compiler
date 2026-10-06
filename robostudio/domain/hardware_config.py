"""Hardware configuration aggregate for RoboStudio (H25-A)."""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable

from tools.hardware_feature_config import (
    HARDWARE_CONFIG_VERSION,
    LEGACY_HARDWARE_CONFIG_VERSION,
    V2_BOARD_PROFILE,
)

from .device_registry import DeviceRegistry

DEVICE_CONFIG_VERSION = HARDWARE_CONFIG_VERSION
BOARD_PROFILE = V2_BOARD_PROFILE


@dataclass(frozen=True)
class DeviceConfig:
    """Configuration state of one registered device."""

    device_id: str
    enabled: bool

    def to_dict(self) -> Dict[str, bool]:
        return {"enabled": bool(self.enabled)}


@dataclass
class HardwareConfig:
    """Aggregate root and serializable source of truth for device selection."""

    version: int = DEVICE_CONFIG_VERSION
    board_profile: str = BOARD_PROFILE
    devices: Dict[str, DeviceConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.version = int(self.version)
        if self.version != DEVICE_CONFIG_VERSION:
            raise ValueError(f"Unsupported hardware configuration version: {self.version}")
        self.board_profile = str(self.board_profile).strip()
        if self.board_profile != BOARD_PROFILE:
            raise ValueError(f"Unsupported board profile: {self.board_profile}")
        if not self.devices:
            self.devices = {
                device_id: DeviceConfig(device_id, enabled)
                for device_id, enabled in DeviceRegistry.defaults().items()
            }
        self._normalize_known_devices()

    @classmethod
    def create_default(cls) -> "HardwareConfig":
        return cls()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HardwareConfig":
        if not isinstance(data, dict):
            raise ValueError("Hardware configuration must be a JSON object")

        version = data.get("version", LEGACY_HARDWARE_CONFIG_VERSION)
        try:
            version = int(version)
        except (TypeError, ValueError) as exc:
            raise ValueError("Hardware configuration version must be an integer") from exc

        if version == LEGACY_HARDWARE_CONFIG_VERSION:
            # Deterministic V1 migration: V1 never persisted physical board
            # identity, so legacy AnTechKids config is assigned to the frozen
            # V2 board profile while preserving every device selection.
            board_profile = BOARD_PROFILE
        elif version == DEVICE_CONFIG_VERSION:
            board_profile = str(data.get("board_profile", "")).strip()
            if board_profile != BOARD_PROFILE:
                raise ValueError(f"Unsupported board profile: {board_profile or '<missing>'}")
        else:
            raise ValueError(f"Unsupported hardware configuration version: {version}")

        raw_devices = data.get("devices", {})
        if not isinstance(raw_devices, dict):
            raise ValueError("'devices' must be an object")

        devices: Dict[str, DeviceConfig] = {}
        for device_id, raw in raw_devices.items():
            DeviceRegistry.require(device_id)
            if isinstance(raw, bool):
                enabled = raw
            elif isinstance(raw, dict) and "enabled" in raw:
                enabled = bool(raw["enabled"])
            else:
                raise ValueError(
                    f"Device '{device_id}' must be a boolean or object with 'enabled'"
                )
            devices[device_id] = DeviceConfig(device_id, enabled)

        return cls(
            version=DEVICE_CONFIG_VERSION,
            board_profile=board_profile,
            devices=devices,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "board_profile": self.board_profile,
            "devices": {
                device_id: config.enabled
                for device_id, config in self.devices.items()
            },
        }

    def is_enabled(self, device_id: str) -> bool:
        DeviceRegistry.require(device_id)
        return self.devices[device_id].enabled

    def set_enabled(self, device_id: str, enabled: bool) -> None:
        DeviceRegistry.require(device_id)
        self.devices[device_id] = DeviceConfig(device_id, bool(enabled))

    def enabled_devices(self) -> Iterable[str]:
        return tuple(
            device_id
            for device_id, config in self.devices.items()
            if config.enabled
        )

    def disabled_devices(self) -> Iterable[str]:
        return tuple(
            device_id
            for device_id, config in self.devices.items()
            if not config.enabled
        )

    def _normalize_known_devices(self) -> None:
        # All registered devices must always have an explicit state. This keeps
        # generated configs deterministic when the registry grows.
        for device_id, default_enabled in DeviceRegistry.defaults().items():
            if device_id not in self.devices:
                self.devices[device_id] = DeviceConfig(device_id, default_enabled)
