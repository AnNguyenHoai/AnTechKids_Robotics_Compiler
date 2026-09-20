"""Registry of known RoboStudio hardware devices.

H25-A intentionally keeps the registry UI-agnostic. Future tabs, profiles and
macro generators consume this registry rather than duplicating device metadata.
The stable feature metadata is shared with packaged deployment tools so source
and EXE modes use one hardware contract.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from tools.hardware_feature_config import HARDWARE_FEATURES


@dataclass(frozen=True)
class DeviceDefinition:
    """Stable definition of one selectable hardware feature."""

    device_id: str
    display_name: str
    category: str
    default_enabled: bool = False
    description: str = ""


class DeviceRegistry:
    """Central registry for supported hardware features."""

    _DEVICES: Tuple[DeviceDefinition, ...] = tuple(
        DeviceDefinition(
            feature.device_id,
            feature.display_name,
            feature.category,
            feature.default_enabled,
            feature.description,
        )
        for feature in HARDWARE_FEATURES
    )
    _BY_ID: Dict[str, DeviceDefinition] = {d.device_id: d for d in _DEVICES}

    @classmethod
    def all(cls) -> Tuple[DeviceDefinition, ...]:
        return cls._DEVICES

    @classmethod
    def get(cls, device_id: str) -> Optional[DeviceDefinition]:
        return cls._BY_ID.get(device_id)

    @classmethod
    def require(cls, device_id: str) -> DeviceDefinition:
        device = cls.get(device_id)
        if device is None:
            raise KeyError(f"Unknown device: {device_id}")
        return device

    @classmethod
    def ids(cls) -> Tuple[str, ...]:
        return tuple(d.device_id for d in cls._DEVICES)

    @classmethod
    def by_category(cls, category: str) -> Tuple[DeviceDefinition, ...]:
        return tuple(d for d in cls._DEVICES if d.category == category)

    @classmethod
    def defaults(cls) -> Dict[str, bool]:
        return {d.device_id: d.default_enabled for d in cls._DEVICES}
