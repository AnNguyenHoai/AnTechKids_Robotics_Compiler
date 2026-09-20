#!/usr/bin/env python3
"""Validate and consolidate the RoboStudio platform contract.

H32 deliberately keeps ownership in the existing canonical sources:

* ``robot-language/specification/api.yaml`` owns API names, arguments and semantics.
* ``packages/robot-isa/canonical_isa.json`` owns opcode identity and wire numbers.
* ``packages/robot-isa/capability_model.json`` owns opcode-to-capability assignment.
* ``packages/robot-isa/target_profiles.json`` owns target capability support.

``platform_contract.json`` is a generated read-only projection of those sources.
Production/compiler code must continue to consume the canonical source that owns
its concern rather than treating the projection as a new source of truth.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "robot-language" / "specification" / "api.yaml"
ISA_PATH = ROOT / "packages" / "robot-isa" / "canonical_isa.json"
CAPABILITY_PATH = ROOT / "packages" / "robot-isa" / "capability_model.json"
TARGET_PROFILES_PATH = ROOT / "packages" / "robot-isa" / "target_profiles.json"
PROJECTION_PATH = ROOT / "packages" / "robot-isa" / "platform_contract.json"

CONTRACT_TYPE = "antechkids.robot.platform-contract"
CONTRACT_SCHEMA_VERSION = 1


class PlatformContractError(RuntimeError):
    """Raised when canonical platform-contract sources disagree."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PlatformContractError(f"Unable to load JSON contract {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PlatformContractError(f"Contract root must be an object: {path}")
    return value


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PlatformContractError(f"Unable to load YAML contract {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PlatformContractError(f"Contract root must be a mapping: {path}")
    return value


def _expect_schema_one(data: dict[str, Any], path: Path) -> None:
    version = data.get("schema_version")
    if version != 1:
        raise PlatformContractError(
            f"Unsupported schema_version in {path}: expected 1, found {version!r}"
        )


def _unique(rows: list[dict[str, Any]], key: str, label: str) -> None:
    seen: dict[Any, int] = {}
    for index, row in enumerate(rows):
        value = row.get(key)
        if value in seen:
            raise PlatformContractError(
                f"Duplicate {label} {value!r} at rows {seen[value]} and {index}"
            )
        seen[value] = index


def _api_entries(api: dict[str, Any]) -> list[dict[str, Any]]:
    categories = api.get("categories")
    if not isinstance(categories, dict) or not categories:
        raise PlatformContractError("api.yaml must contain a non-empty categories mapping")

    rows: list[dict[str, Any]] = []
    for category_name, category in categories.items():
        if not isinstance(category_name, str) or not isinstance(category, dict):
            raise PlatformContractError("api.yaml category entries must be mappings")
        functions = category.get("functions")
        if not isinstance(functions, list):
            raise PlatformContractError(
                f"api.yaml category {category_name!r} must contain functions[]"
            )
        for function in functions:
            if not isinstance(function, dict):
                raise PlatformContractError(
                    f"api.yaml category {category_name!r} contains a non-object function"
                )
            name = function.get("name")
            opcode = function.get("opcode")
            opcode_id = function.get("opcode_id")
            args = function.get("args")
            if not isinstance(name, str) or not name:
                raise PlatformContractError(f"Invalid API function name in {category_name!r}")
            if not isinstance(opcode, str) or not opcode:
                raise PlatformContractError(f"API {category_name}.{name} has invalid opcode")
            if not isinstance(opcode_id, int):
                raise PlatformContractError(f"API {category_name}.{name} has invalid opcode_id")
            if not isinstance(args, list):
                raise PlatformContractError(f"API {category_name}.{name} must contain args[]")
            for argument in args:
                if (
                    not isinstance(argument, dict)
                    or not isinstance(argument.get("name"), str)
                    or not isinstance(argument.get("type"), str)
                ):
                    raise PlatformContractError(
                        f"API {category_name}.{name} contains an invalid argument"
                    )
            rows.append(
                {
                    "category": category_name,
                    "name": name,
                    "qualified_name": f"{category_name}.{name}",
                    "opcode": opcode,
                    "opcode_id": opcode_id,
                    "args": args,
                    "returns": function.get("returns", "none"),
                    "semantic": function.get("semantic"),
                    "priority": function.get("priority"),
                    "description": function.get("description", ""),
                    "public": category_name != "internal",
                }
            )

    _unique(rows, "qualified_name", "API qualified name")
    _unique(rows, "opcode", "API opcode producer name")
    _unique(rows, "opcode_id", "API opcode wire id")
    return rows


def _isa_entries(isa: dict[str, Any]) -> list[dict[str, Any]]:
    _expect_schema_one(isa, ISA_PATH)
    columns = isa.get("columns")
    raw_rows = isa.get("rows")
    required = ["id", "producer_name", "numeric_code", "category", "canonical_index"]
    if columns != required:
        raise PlatformContractError(
            f"canonical_isa columns changed: expected {required!r}, found {columns!r}"
        )
    if not isinstance(raw_rows, list) or not raw_rows:
        raise PlatformContractError("canonical_isa rows must be a non-empty list")

    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_rows):
        if not isinstance(raw, list) or len(raw) != len(columns):
            raise PlatformContractError(f"Invalid canonical ISA row at index {index}")
        row = dict(zip(columns, raw))
        if (
            not isinstance(row["id"], str)
            or not isinstance(row["producer_name"], str)
            or not isinstance(row["numeric_code"], int)
            or not isinstance(row["category"], str)
            or not isinstance(row["canonical_index"], int)
        ):
            raise PlatformContractError(f"Invalid canonical ISA values at index {index}")
        rows.append(row)

    for key, label in (
        ("id", "canonical opcode id"),
        ("producer_name", "canonical producer name"),
        ("numeric_code", "canonical numeric code"),
        ("canonical_index", "canonical index"),
    ):
        _unique(rows, key, label)
    expected_indices = list(range(len(rows)))
    actual_indices = [row["canonical_index"] for row in rows]
    if actual_indices != expected_indices:
        raise PlatformContractError(
            "canonical_index must be contiguous and match canonical row order"
        )
    return rows


def _capability_entries(data: dict[str, Any], isa_by_code: dict[int, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[int, str]]:
    _expect_schema_one(data, CAPABILITY_PATH)
    raw = data.get("capabilities")
    if not isinstance(raw, list) or not raw:
        raise PlatformContractError("capability_model capabilities must be a non-empty list")

    rows: list[dict[str, Any]] = []
    opcode_owner: dict[int, str] = {}
    for index, capability in enumerate(raw):
        if not isinstance(capability, dict):
            raise PlatformContractError(f"Invalid capability row at index {index}")
        capability_id = capability.get("id")
        category = capability.get("category")
        description = capability.get("description")
        opcodes = capability.get("opcodes")
        required = capability.get("required")
        if (
            not isinstance(capability_id, str)
            or not capability_id
            or not isinstance(category, str)
            or not isinstance(description, str)
            or not isinstance(opcodes, list)
            or not isinstance(required, bool)
        ):
            raise PlatformContractError(f"Invalid capability values at index {index}")
        local_seen: set[int] = set()
        for code in opcodes:
            if not isinstance(code, int):
                raise PlatformContractError(f"Capability {capability_id} contains non-integer opcode")
            if code not in isa_by_code:
                raise PlatformContractError(
                    f"Capability {capability_id} references unknown opcode {code}"
                )
            if code in local_seen:
                raise PlatformContractError(
                    f"Capability {capability_id} references opcode {code} more than once"
                )
            local_seen.add(code)
            previous = opcode_owner.get(code)
            if previous is not None:
                raise PlatformContractError(
                    f"Opcode {code} is assigned to both {previous} and {capability_id}"
                )
            opcode_owner[code] = capability_id
        rows.append(
            {
                "id": capability_id,
                "category": category,
                "description": description,
                "opcodes": list(opcodes),
                "required": required,
            }
        )
    _unique(rows, "id", "capability id")

    uncovered = sorted(set(isa_by_code) - set(opcode_owner))
    if uncovered:
        raise PlatformContractError(
            f"Canonical opcodes missing capability assignment: {uncovered}"
        )
    return rows, opcode_owner


def _target_profiles(data: dict[str, Any], capability_ids: set[str], required_ids: set[str]) -> list[dict[str, Any]]:
    _expect_schema_one(data, TARGET_PROFILES_PATH)
    raw = data.get("profiles")
    if not isinstance(raw, list) or not raw:
        raise PlatformContractError("target_profiles profiles must be a non-empty list")

    rows: list[dict[str, Any]] = []
    for index, profile in enumerate(raw):
        if not isinstance(profile, dict):
            raise PlatformContractError(f"Invalid target profile at index {index}")
        profile_id = profile.get("id")
        description = profile.get("description")
        capabilities = profile.get("capabilities")
        if (
            not isinstance(profile_id, str)
            or not profile_id
            or not isinstance(description, str)
            or not isinstance(capabilities, list)
            or any(not isinstance(value, str) for value in capabilities)
        ):
            raise PlatformContractError(f"Invalid target profile values at index {index}")
        if len(capabilities) != len(set(capabilities)):
            raise PlatformContractError(f"Target profile {profile_id} contains duplicate capabilities")
        unknown = sorted(set(capabilities) - capability_ids)
        if unknown:
            raise PlatformContractError(
                f"Target profile {profile_id} references unknown capabilities: {unknown}"
            )
        missing_required = sorted(required_ids - set(capabilities))
        if missing_required:
            raise PlatformContractError(
                f"Target profile {profile_id} omits required capabilities: {missing_required}"
            )
        rows.append(
            {
                "id": profile_id,
                "description": description,
                "capabilities": list(capabilities),
            }
        )
    _unique(rows, "id", "target profile id")
    return rows


def build_contract() -> dict[str, Any]:
    """Build and cross-validate the deterministic consolidated projection."""
    api_data = _load_yaml(API_PATH)
    isa_data = _load_json(ISA_PATH)
    capability_data = _load_json(CAPABILITY_PATH)
    target_data = _load_json(TARGET_PROFILES_PATH)

    api_rows = _api_entries(api_data)
    isa_rows = _isa_entries(isa_data)
    isa_by_name = {row["producer_name"]: row for row in isa_rows}
    isa_by_code = {row["numeric_code"]: row for row in isa_rows}

    api_by_opcode = {row["opcode"]: row for row in api_rows}
    missing_api = sorted(set(isa_by_name) - set(api_by_opcode))
    unknown_api = sorted(set(api_by_opcode) - set(isa_by_name))
    if missing_api or unknown_api:
        raise PlatformContractError(
            "API/ISA opcode coverage drift: "
            f"missing API entries={missing_api}, unknown API opcodes={unknown_api}"
        )
    for api in api_rows:
        isa = isa_by_name[api["opcode"]]
        if api["opcode_id"] != isa["numeric_code"]:
            raise PlatformContractError(
                f"Opcode wire-id drift for {api['qualified_name']}: "
                f"api.yaml={api['opcode_id']}, canonical_isa={isa['numeric_code']}"
            )

    capabilities, capability_by_code = _capability_entries(capability_data, isa_by_code)
    capability_ids = {row["id"] for row in capabilities}
    required_ids = {row["id"] for row in capabilities if row["required"]}
    profiles = _target_profiles(target_data, capability_ids, required_ids)
    profile_capabilities = {row["id"]: set(row["capabilities"]) for row in profiles}

    operations: list[dict[str, Any]] = []
    for isa in isa_rows:
        api = api_by_opcode[isa["producer_name"]]
        capability_id = capability_by_code[isa["numeric_code"]]
        supported_targets = [
            profile["id"]
            for profile in profiles
            if capability_id in profile_capabilities[profile["id"]]
        ]
        operations.append(
            {
                "id": isa["id"],
                "producer_name": isa["producer_name"],
                "numeric_code": isa["numeric_code"],
                "canonical_index": isa["canonical_index"],
                "isa_category": isa["category"],
                "api": {
                    "category": api["category"],
                    "name": api["name"],
                    "qualified_name": api["qualified_name"],
                    "args": api["args"],
                    "returns": api["returns"],
                    "semantic": api["semantic"],
                    "priority": api["priority"],
                    "description": api["description"],
                    "public": api["public"],
                },
                "capability": capability_id,
                "supported_targets": supported_targets,
            }
        )

    capability_projection: list[dict[str, Any]] = []
    for capability in capabilities:
        capability_projection.append(
            {
                **capability,
                "targets": [
                    profile["id"]
                    for profile in profiles
                    if capability["id"] in profile_capabilities[profile["id"]]
                ],
            }
        )

    language = api_data.get("language", {})
    return {
        "type": CONTRACT_TYPE,
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "generated": True,
        "language": {
            "name": language.get("name"),
            "version": language.get("version"),
        },
        "source_ownership": {
            "api_semantics": "robot-language/specification/api.yaml",
            "opcode_identity_and_wire_code": "packages/robot-isa/canonical_isa.json",
            "capability_assignment": "packages/robot-isa/capability_model.json",
            "target_support": "packages/robot-isa/target_profiles.json",
        },
        "operations": operations,
        "capabilities": capability_projection,
        "targets": profiles,
    }


def render_contract(contract: dict[str, Any] | None = None) -> str:
    return json.dumps(contract or build_contract(), indent=2, ensure_ascii=False) + "\n"


def write_contract(path: Path = PROJECTION_PATH) -> Path:
    output = Path(path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_contract(), encoding="utf-8")
    return output


def check_projection(path: Path = PROJECTION_PATH) -> None:
    expected = build_contract()
    actual = _load_json(Path(path))
    if actual != expected:
        raise PlatformContractError(
            f"Generated platform contract is stale: {path}. "
            "Run `python tools/platform_contract.py generate`."
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate/generate the H32 platform contract projection")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Cross-validate all canonical contract sources")
    generate = sub.add_parser("generate", help="Generate the consolidated JSON projection")
    generate.add_argument("--output", type=Path, default=PROJECTION_PATH)
    sub.add_parser("check", help="Fail if the checked-in projection is stale")
    sub.add_parser("print", help="Print the generated projection to stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            contract = build_contract()
            print(
                "H32 platform contract valid: "
                f"{len(contract['operations'])} opcodes, "
                f"{len(contract['capabilities'])} capabilities, "
                f"{len(contract['targets'])} targets"
            )
        elif args.command == "generate":
            path = write_contract(args.output)
            print(f"Generated platform contract: {path}")
        elif args.command == "check":
            check_projection()
            print("H32 platform contract projection is current")
        elif args.command == "print":
            sys.stdout.write(render_contract())
        return 0
    except PlatformContractError as exc:
        print(f"H32 PLATFORM CONTRACT ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
