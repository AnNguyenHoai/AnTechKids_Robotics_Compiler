"""Program-level hardware capability analysis for RoboStudio (H25-J)."""

import ast
from dataclasses import dataclass
from typing import Set, Tuple

from .hardware_config import HardwareConfig
from .hardware_requirements import HardwareRequirementRegistry


@dataclass(frozen=True)
class ProgramCapabilityAnalysis:
    """Hardware capabilities referenced by a RoboSim program."""

    required_devices: Tuple[str, ...] = ()
    api_names: Tuple[str, ...] = ()
    syntax_error: bool = False

    def missing_devices(self, config: HardwareConfig) -> Tuple[str, ...]:
        return tuple(
            device_id
            for device_id in self.required_devices
            if not config.is_enabled(device_id)
        )

    @property
    def has_requirements(self) -> bool:
        return bool(self.required_devices)


class ProgramCapabilityAnalyzer:
    """Extract required hardware capabilities from RoboSim source code.

    The analyzer deliberately consumes the same ``HardwareRequirementRegistry``
    used by H25-F validation. This keeps the editor's capability view and the
    build-time validator on one API -> hardware contract.
    """

    MODULE_ALIASES = frozenset(("rcu", "robot"))

    @classmethod
    def analyze(cls, source: str) -> ProgramCapabilityAnalysis:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            # Syntax diagnostics remain the compiler's responsibility. The UI
            # simply avoids making a hardware claim for incomplete Python.
            return ProgramCapabilityAnalysis(syntax_error=True)

        module_aliases: Set[str] = set(cls.MODULE_ALIASES)
        direct_imports: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in cls.MODULE_ALIASES:
                        module_aliases.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module in cls.MODULE_ALIASES:
                for alias in node.names:
                    direct_imports.add(alias.asname or alias.name)

        required: Set[str] = set()
        apis: Set[str] = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            api_name = cls._resolve_api_name(node.func, module_aliases, direct_imports)
            if not api_name:
                continue
            devices = HardwareRequirementRegistry.required_devices(api_name)
            if devices:
                apis.add(api_name)
                required.update(devices)

        return ProgramCapabilityAnalysis(
            required_devices=tuple(sorted(required)),
            api_names=tuple(sorted(apis)),
        )

    @staticmethod
    def _resolve_api_name(func, module_aliases: Set[str], direct_imports: Set[str]):
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id in module_aliases:
                return func.attr
        elif isinstance(func, ast.Name) and func.id in direct_imports:
            return func.id
        return None
