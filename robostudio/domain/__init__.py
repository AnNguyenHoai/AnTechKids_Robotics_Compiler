"""Hardware device configuration domain for RoboStudio."""

from .hardware_config import (
    DEVICE_CONFIG_VERSION,
    DeviceConfig,
    HardwareConfig,
)
from .device_registry import DeviceDefinition, DeviceRegistry
from .hardware_config_service import HardwareConfigService
from .hardware_macro_generator import HardwareMacroGenerator
from .hardware_requirement_validator import HardwareRequirementValidator

__all__ = [
    "DEVICE_CONFIG_VERSION",
    "DeviceConfig",
    "HardwareConfig",
    "DeviceDefinition",
    "DeviceRegistry",
    "HardwareConfigService",
    "HardwareMacroGenerator",
    "HardwareRequirementValidator",
]
from .program_capabilities import ProgramCapabilityAnalysis, ProgramCapabilityAnalyzer
