"""Firmware macro generation for RoboStudio hardware configuration (H25-C)."""

from pathlib import Path

from tools.hardware_feature_config import macro_name, render_generated_header

from .hardware_config import HardwareConfig


class HardwareMacroGenerator:
    """Generate firmware feature macros from HardwareConfig.

    Rendering is delegated to the shared deployment/runtime contract so
    RoboStudio source mode, RoboStudio.exe, and deployment tools cannot drift on
    feature order, macro names, or defaults.
    """

    HEADER_GUARD = "ROBOT_PLATFORM_GENERATED_DEVICE_CONFIG_H"

    def macro_name(self, device_id: str) -> str:
        return macro_name(device_id)

    def render(self, config: HardwareConfig) -> str:
        return render_generated_header(
            {
                device_id: config.is_enabled(device_id)
                for device_id in config.devices
            }
        )

    def generate(self, config: HardwareConfig, output_path: Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.render(config), encoding="utf-8")
        return output_path

    @classmethod
    def default_output_path(cls) -> Path:
        """Return the immutable/default firmware-template header location.

        RoboStudio no longer writes mutable user hardware state here. The method
        remains for integrations that explicitly need the repository template.
        """
        workspace_root = Path(__file__).resolve().parent.parent.parent
        return (
            workspace_root
            / "robot-platform"
            / "main"
            / "include"
            / "generated"
            / "generated_device_config.h"
        )
