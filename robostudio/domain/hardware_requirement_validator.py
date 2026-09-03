"""Static program validation against the active hardware configuration (H25-F)."""

import ast
from dataclasses import dataclass
from typing import List, Set, Tuple

from .hardware_config import HardwareConfig
from .hardware_requirements import HardwareRequirementRegistry


@dataclass(frozen=True)
class HardwareValidationIssue:
    line: int
    column: int
    api_name: str
    required_devices: Tuple[str, ...]
    disabled_devices: Tuple[str, ...]

    def format(self) -> str:
        required = ", ".join(self.required_devices)
        disabled = ", ".join(self.disabled_devices)
        return (
            f"Line {self.line}: {self.api_name} requires [{required}], "
            f"but disabled in Hardware Configuration: [{disabled}]"
        )


@dataclass(frozen=True)
class HardwareValidationResult:
    valid: bool
    issues: Tuple[HardwareValidationIssue, ...]

    def format_errors(self) -> str:
        if self.valid:
            return ""
        return "Hardware Configuration Error:\n" + "\n".join(
            f"- {issue.format()}" for issue in self.issues
        )


class HardwareRequirementValidator:
    """Checks direct calls such as rcu.line_follow(...) before compilation."""

    MODULE_ALIASES = frozenset(("rcu", "robot"))

    @classmethod
    def validate(cls, source: str, config: HardwareConfig) -> HardwareValidationResult:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            # Let the language compiler own syntax diagnostics.
            return HardwareValidationResult(True, ())

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

        issues: List[HardwareValidationIssue] = []
        seen = set()

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            api_name = cls._resolve_api_name(node.func, module_aliases, direct_imports)
            if not api_name:
                continue
            required = HardwareRequirementRegistry.required_devices(api_name)
            if not required:
                continue
            disabled = tuple(sorted(device for device in required if not config.is_enabled(device)))
            if not disabled:
                continue
            key = (node.lineno, getattr(node, "col_offset", 0), api_name, disabled)
            if key in seen:
                continue
            seen.add(key)
            issues.append(HardwareValidationIssue(
                line=node.lineno,
                column=getattr(node, "col_offset", 0),
                api_name=api_name,
                required_devices=tuple(sorted(required)),
                disabled_devices=disabled,
            ))

        issues.sort(key=lambda issue: (issue.line, issue.column, issue.api_name))
        return HardwareValidationResult(not issues, tuple(issues))

    @staticmethod
    def _resolve_api_name(func, module_aliases: Set[str], direct_imports: Set[str]):
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            if func.value.id in module_aliases:
                return func.attr
        elif isinstance(func, ast.Name) and func.id in direct_imports:
            return func.id
        return None
