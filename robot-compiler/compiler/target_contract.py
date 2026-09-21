"""H33 target/capability/resource contract enforcement for the compiler."""
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Mapping

from .error import CompilerError

_CANONICAL_ISA = "canonical_isa.json"
_CAPABILITY_MODEL = "capability_model.json"
_TARGET_PROFILES = "target_profiles.json"
_REQUIRED_FILES = (_CANONICAL_ISA, _CAPABILITY_MODEL, _TARGET_PROFILES)


def _diagnostic_context(node: ast.AST | None, **extra: Any) -> dict[str, Any]:
    context = {key: value for key, value in extra.items() if value is not None}
    if node is not None:
        line = getattr(node, "lineno", None)
        column = getattr(node, "col_offset", None)
        if line is not None:
            context["line"] = line
        if column is not None:
            context["column"] = column + 1
    return context


def _contract_directory() -> Path:
    """Resolve canonical contracts in source and staged production layouts."""
    here = Path(__file__).resolve()

    # Production distribution:
    #   compiler/contracts/*.json
    #   compiler/compiler/target_contract.py
    packaged = here.parent.parent / "contracts"
    if all((packaged / name).is_file() for name in _REQUIRED_FILES):
        return packaged

    # Source checkout: walk upward until packages/robot-isa is found.
    for parent in here.parents:
        candidate = parent / "packages" / "robot-isa"
        if all((candidate / name).is_file() for name in _REQUIRED_FILES):
            return candidate

    raise CompilerError(
        "Canonical robot target contracts are not available in this runtime.",
        code="E_TARGET_PROFILE_INVALID",
        context={"required_files": list(_REQUIRED_FILES)},
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompilerError(
            f"Unable to load target contract '{path.name}': {exc}",
            code="E_TARGET_PROFILE_INVALID",
            context={"contract": path.name},
        ) from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise CompilerError(
            f"Target contract '{path.name}' must be a schema_version=1 object.",
            code="E_TARGET_PROFILE_INVALID",
            context={"contract": path.name},
        )
    return value


class TargetContract:
    """Resolve a compile target and enforce canonical capability/resource rules."""

    def __init__(self, target_id: str = "robosim"):
        if not isinstance(target_id, str) or not target_id.strip():
            raise CompilerError(
                "Compile target must be a non-empty string.",
                code="E_TARGET_UNKNOWN",
                context={"target": target_id},
            )
        self.target_id = target_id.strip()
        directory = _contract_directory()
        self._isa = _load_json(directory / _CANONICAL_ISA)
        self._capability_model = _load_json(directory / _CAPABILITY_MODEL)
        self._target_profiles = _load_json(directory / _TARGET_PROFILES)

        self._opcode_by_producer = self._build_opcode_index()
        self._capability_by_opcode, self._known_capabilities, required = self._build_capability_index()
        self._profiles = self._build_target_index(required)
        self._resources = self._build_resource_contracts()

        self.profile = self._profiles.get(self.target_id)
        if self.profile is None:
            raise CompilerError(
                f"Unknown compile target '{self.target_id}'.",
                code="E_TARGET_UNKNOWN",
                context={"target": self.target_id, "available_targets": sorted(self._profiles)},
            )
        self.capabilities = frozenset(self.profile["capabilities"])

    def _build_opcode_index(self) -> dict[str, int]:
        columns = self._isa.get("columns")
        rows = self._isa.get("rows")
        expected = ["id", "producer_name", "numeric_code", "category", "canonical_index"]
        if columns != expected or not isinstance(rows, list) or not rows:
            self._invalid("canonical_isa.json has an invalid row schema")
        result: dict[str, int] = {}
        for raw in rows:
            if not isinstance(raw, list) or len(raw) != len(expected):
                self._invalid("canonical_isa.json contains an invalid row")
            producer = raw[1]
            opcode = raw[2]
            if not isinstance(producer, str) or not isinstance(opcode, int) or producer in result:
                self._invalid("canonical_isa.json contains an invalid/duplicate producer")
            result[producer] = opcode
        return result

    def _build_capability_index(self) -> tuple[dict[int, str], set[str], set[str]]:
        raw = self._capability_model.get("capabilities")
        if not isinstance(raw, list) or not raw:
            self._invalid("capability_model.json must contain capabilities[]")
        owners: dict[int, str] = {}
        known: set[str] = set()
        required: set[str] = set()
        for item in raw:
            if not isinstance(item, dict):
                self._invalid("capability_model.json contains an invalid capability")
            capability_id = item.get("id")
            opcodes = item.get("opcodes")
            is_required = item.get("required")
            if (
                not isinstance(capability_id, str)
                or not capability_id
                or capability_id in known
                or not isinstance(opcodes, list)
                or any(not isinstance(code, int) for code in opcodes)
                or not isinstance(is_required, bool)
            ):
                self._invalid("capability_model.json contains invalid capability metadata")
            known.add(capability_id)
            if is_required:
                required.add(capability_id)
            for code in opcodes:
                if code in owners:
                    self._invalid(f"opcode {code} is assigned to multiple capabilities")
                owners[code] = capability_id

        missing = sorted(set(self._opcode_by_producer.values()) - set(owners))
        if missing:
            self._invalid(f"canonical opcodes without capability ownership: {missing}")
        return owners, known, required

    def _build_target_index(self, required: set[str]) -> dict[str, dict[str, Any]]:
        raw = self._target_profiles.get("profiles")
        if not isinstance(raw, list) or not raw:
            self._invalid("target_profiles.json must contain profiles[]")
        profiles: dict[str, dict[str, Any]] = {}
        for item in raw:
            if not isinstance(item, dict):
                self._invalid("target_profiles.json contains an invalid profile")
            profile_id = item.get("id")
            capabilities = item.get("capabilities")
            if (
                not isinstance(profile_id, str)
                or not profile_id
                or profile_id in profiles
                or not isinstance(capabilities, list)
                or any(not isinstance(value, str) for value in capabilities)
                or len(capabilities) != len(set(capabilities))
            ):
                self._invalid("target_profiles.json contains invalid profile metadata")
            unknown = sorted(set(capabilities) - self._known_capabilities)
            missing = sorted(required - set(capabilities))
            if unknown or missing:
                self._invalid(
                    f"target '{profile_id}' capability contract is invalid "
                    f"(unknown={unknown}, missing_required={missing})"
                )
            profiles[profile_id] = dict(item)
        return profiles

    def _build_resource_contracts(self) -> list[dict[str, Any]]:
        raw = self._target_profiles.get("resources", [])
        if not isinstance(raw, list):
            self._invalid("target_profiles.json resources must be a list")
        resources: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in raw:
            if not isinstance(item, dict):
                self._invalid("target_profiles.json contains an invalid resource contract")
            resource_id = item.get("id")
            capability = item.get("capability")
            bindings = item.get("bindings")
            targets = item.get("targets")
            if (
                not isinstance(resource_id, str)
                or not resource_id
                or resource_id in seen
                or capability not in self._known_capabilities
                or not isinstance(bindings, list)
                or not bindings
                or not isinstance(targets, dict)
            ):
                self._invalid("target_profiles.json contains invalid resource metadata")
            seen.add(resource_id)
            normalized_bindings: list[dict[str, Any]] = []
            for binding in bindings:
                if (
                    not isinstance(binding, dict)
                    or not isinstance(binding.get("api"), str)
                    or not isinstance(binding.get("argument_index"), int)
                    or binding["argument_index"] < 0
                ):
                    self._invalid(f"resource '{resource_id}' has an invalid API binding")
                normalized_bindings.append(dict(binding))
            normalized_targets: dict[str, dict[str, Any]] = {}
            for target_id, rule in targets.items():
                if target_id not in self._profiles or not isinstance(rule, dict):
                    self._invalid(f"resource '{resource_id}' references unknown/invalid target '{target_id}'")
                minimum = rule.get("min")
                maximum = rule.get("max")
                dynamic = rule.get("dynamic", "reject")
                if (
                    not isinstance(minimum, int)
                    or not isinstance(maximum, int)
                    or minimum > maximum
                    or dynamic not in {"reject", "runtime"}
                ):
                    self._invalid(f"resource '{resource_id}' has invalid bounds for target '{target_id}'")
                normalized_targets[target_id] = {
                    "min": minimum,
                    "max": maximum,
                    "dynamic": dynamic,
                }
            resources.append(
                {
                    "id": resource_id,
                    "capability": capability,
                    "bindings": normalized_bindings,
                    "targets": normalized_targets,
                }
            )
        return resources

    def validate_api_call(self, api_name: str, info: Mapping[str, Any], node: ast.Call) -> None:
        producer = info.get("opcode")
        if not isinstance(producer, str) or producer not in self._opcode_by_producer:
            raise CompilerError(
                f"Robot API '{api_name}()' is not present in the canonical ISA.",
                code="E_API_UNSUPPORTED",
                context=_diagnostic_context(
                    node,
                    api=api_name,
                    target=self.target_id,
                    producer=producer,
                ),
            )

        opcode = self._opcode_by_producer[producer]
        capability = self._capability_by_opcode.get(opcode)
        if capability is None:
            self._invalid(f"canonical opcode {opcode} has no capability owner")

        if capability not in self.capabilities:
            raise CompilerError(
                f"Robot API '{api_name}()' requires capability '{capability}', "
                f"which target '{self.target_id}' does not provide.",
                code="E_CAPABILITY_MISSING",
                context=_diagnostic_context(
                    node,
                    api=api_name,
                    target=self.target_id,
                    capability=capability,
                    opcode=opcode,
                ),
            )

        for resource in self._resources:
            if resource["capability"] != capability:
                continue
            rule = resource["targets"].get(self.target_id)
            if rule is None:
                continue
            for binding in resource["bindings"]:
                if binding["api"] != api_name:
                    continue
                self._validate_resource_argument(resource["id"], binding["argument_index"], rule, api_name, node)

    def _validate_resource_argument(
        self,
        resource_id: str,
        argument_index: int,
        rule: Mapping[str, Any],
        api_name: str,
        node: ast.Call,
    ) -> None:
        if argument_index >= len(node.args):
            self._invalid(
                f"resource '{resource_id}' binding for '{api_name}' references argument {argument_index}"
            )
        argument = node.args[argument_index]
        minimum = rule["min"]
        maximum = rule["max"]

        if isinstance(argument, ast.Constant) and type(argument.value) is int:
            value = argument.value
            if value < minimum or value > maximum:
                raise CompilerError(
                    f"Resource '{resource_id}' index {value} is outside "
                    f"target '{self.target_id}' range {minimum}..{maximum}.",
                    code="E_RESOURCE_OUT_OF_RANGE",
                    context=_diagnostic_context(
                        node,
                        api=api_name,
                        target=self.target_id,
                        resource=resource_id,
                        resource_value=value,
                        resource_min=minimum,
                        resource_max=maximum,
                    ),
                )
            return

        if rule.get("dynamic", "reject") == "reject":
            raise CompilerError(
                f"Robot API '{api_name}()' uses a dynamic '{resource_id}' index, but "
                f"target '{self.target_id}' has no proven runtime bounds contract.",
                code="E_DYNAMIC_RESOURCE_UNSAFE",
                context=_diagnostic_context(
                    node,
                    api=api_name,
                    target=self.target_id,
                    resource=resource_id,
                    resource_min=minimum,
                    resource_max=maximum,
                ),
            )

    @staticmethod
    def _invalid(message: str) -> None:
        raise CompilerError(
            message,
            code="E_TARGET_PROFILE_INVALID",
        )
