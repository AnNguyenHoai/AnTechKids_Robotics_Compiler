"""Hardware device configuration domain for RoboStudio."""

from .hardware_config import (
    DEVICE_CONFIG_VERSION,
    DeviceConfig,
    HardwareConfig,
)
from .device_registry import DeviceDefinition, DeviceRegistry
from .hardware_config_service import HardwareConfigService
from .hardware_macro_generator import HardwareMacroGenerator

__all__ = [
    "DEVICE_CONFIG_VERSION",
    "DeviceConfig",
    "HardwareConfig",
    "DeviceDefinition",
    "DeviceRegistry",
    "HardwareConfigService",
    "HardwareMacroGenerator",
]
