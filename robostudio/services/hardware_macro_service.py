"""H25-C service for synchronizing hardware.json into firmware macros."""

from pathlib import Path
from typing import Optional

from ..domain.hardware_config_service import HardwareConfigService
from ..domain.hardware_macro_generator import HardwareMacroGenerator


class HardwareMacroService:
    """Loads the source-of-truth hardware config and generates firmware macros."""

    def __init__(
        self,
        config_service: Optional[HardwareConfigService] = None,
        generator: Optional[HardwareMacroGenerator] = None,
        output_path: Optional[Path] = None,
    ):
        self.config_service = config_service or HardwareConfigService()
        self.generator = generator or HardwareMacroGenerator()
        self.output_path = Path(output_path) if output_path else self.generator.default_output_path()

    def generate(self) -> Path:
        config = self.config_service.load()
        return self.generator.generate(config, self.output_path)
