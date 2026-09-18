"""H25-C service for synchronizing hardware.json into firmware macros.

In a packaged RoboStudio build the application tree is immutable. Generated
hardware feature headers therefore live under the external RoboStudio state
root and are overlaid onto an isolated firmware workspace during deployment.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from tools import runtime_paths

# RoboStudio historically supports two import layouts: the packaged namespace
# (``robostudio.services``) used by integration tests and the top-level
# ``services`` package used by the desktop entry point. Support both without
# requiring a source-tree PYTHONPATH in production.
try:  # package import: robostudio.services.hardware_macro_service
    from ..domain.hardware_config_service import HardwareConfigService
    from ..domain.hardware_macro_generator import HardwareMacroGenerator
except ImportError:  # desktop import: services.hardware_macro_service
    from domain.hardware_config_service import HardwareConfigService
    from domain.hardware_macro_generator import HardwareMacroGenerator


class HardwareMacroService:
    """Load hardware state and generate the firmware feature header safely."""

    def __init__(
        self,
        config_service: Optional[HardwareConfigService] = None,
        generator: Optional[HardwareMacroGenerator] = None,
        output_path: Optional[Path] = None,
    ):
        self.config_service = config_service or HardwareConfigService()
        self.generator = generator or HardwareMacroGenerator()
        self.output_path = (
            Path(output_path).expanduser()
            if output_path is not None
            else self.default_output_path()
        )
        self._validate_output_path(self.output_path)

    @staticmethod
    def _packaged_mode() -> bool:
        return (
            runtime_paths.is_frozen()
            or os.environ.get(runtime_paths.RUNTIME_MODE_ENV) == "packaged"
            or os.environ.get(runtime_paths.DEPENDENCY_MODE_ENV) == "artifact-closed"
        )

    @classmethod
    def default_output_path(cls) -> Path:
        """Return the canonical generated header path for the current mode."""
        if cls._packaged_mode() or os.environ.get(runtime_paths.STATE_ROOT_ENV):
            return (
                runtime_paths.user_data_root(
                    application_root_override=runtime_paths.application_root(),
                    enforce_external=cls._packaged_mode(),
                )
                / "generated"
                / "generated_device_config.h"
            )
        # Preserve the source-development workflow. Production never reaches
        # this repository-relative path.
        return HardwareMacroGenerator.default_output_path()

    @classmethod
    def _validate_output_path(cls, output_path: Path) -> Path:
        """Require packaged generated output to remain inside external state."""
        candidate = Path(output_path).expanduser().resolve()
        if not cls._packaged_mode():
            return candidate

        state = runtime_paths.user_data_root(
            application_root_override=runtime_paths.application_root(),
            enforce_external=True,
        ).resolve()
        try:
            candidate.relative_to(state)
        except ValueError as exc:
            raise runtime_paths.RuntimePathError(
                "Generated hardware macro must live under ROBOSTUDIO_STATE_ROOT: "
                f"output={candidate}, state={state}"
            ) from exc
        return candidate

    def generate(self) -> Path:
        config = self.config_service.load()
        output = self._validate_output_path(self.output_path)
        return self.generator.generate(config, output)
