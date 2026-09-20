"""H25-C service for synchronizing hardware.json into firmware macros.

Mutable hardware state has one contract in both source-development and packaged
RoboStudio: generated user headers live under ``ROBOSTUDIO_STATE_ROOT`` (or the
platform default user-data root) and are later overlaid into an isolated
firmware workspace. The repository/release firmware header is only a read-only
default template.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from tools import runtime_paths
from tools.hardware_feature_config import generated_header_path

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
        """Return the canonical mutable generated-header path for every mode."""
        return generated_header_path()

    @classmethod
    def _validate_output_path(cls, output_path: Path) -> Path:
        """Require packaged generated output to remain inside external state.

        Source/integration callers may still supply an explicit temporary output
        path. Normal source-mode usage reaches ``default_output_path`` and thus
        uses the exact same user-state location as RoboStudio.exe.
        """
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
