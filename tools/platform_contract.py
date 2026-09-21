#!/usr/bin/env python3
"""Validate and consolidate the RoboStudio platform contract.

Canonical ownership intentionally remains split by concern:

- ``robot-language/specification/api.yaml`` owns API signatures and semantics.
- ``packages/robot-isa/canonical_isa.json`` owns opcode identity/wire numbers.
- ``packages/robot-isa/capability_model.json`` owns opcode→capability assignment.
- ``packages/robot-isa/target_profiles.json`` owns target capability support.

H32 joins those sources into ``artifacts/platform_contract.json`` for CI/release
validation and human inspection. The generated projection is evidence only; it
is deliberately not checked into the canonical package and production layers
must not consume it as a source of truth.
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
PROJECTION_PATH = ROOT / "artifacts" / "platform_contract.json"

CONTRACT_TYPE = "antechkids.robot.platform-contract"
CONTRACT_SCHEMA_VERSION = 1


class PlatformContractError(RuntimeError):
    pass


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


def _require_schema_one(data: dict[str, Any], path: Path) -> None:
    if data.get("schema_version") != 1:
        raise PlatformContractError(
            f"Unsupported schema_version in {path}: {data.get('schema_version')!r}"
        )


def _assert_unique(rows: list[dict[str, Any]], key: str, label: str) -> None:
    seen: dict[Any, int] = {}
    for index, row in enumerate(rows):
        value = row[key]
        if value in seen:
            raise PlatformContractError(
                f"Duplicate {label} {value!r} at rows {seen[value]} and {index}"
            )
        seen[value] = index


def _read_api() -> list[dict[str, Any]]:
    data = _load_yaml(API_PATH)
    categories = data.get("categories")
    if not isinstance(categories, dict) or not categories:
        raise PlatformContractError("api.yaml must contain categories")

    rows: list[dict[str, Any]] = []
    for category_name, category in categories.items():
        if not isinstance(category_name, str) or not isinstance(category, dict):
            raise PlatformContractError("Invalid api.yaml category")
        functions = category.get("functions")
        if not isinstance(functions, list):
            raise PlatformContractError(f"Category {category_name} must contain functions[]")
        for function in functions:
            if not isinstance(function, dict):
                raise PlatformContractError(f"Invalid function in category {category_name}")
            name = function.get("name")
            opcode = function.get("opcode")
            opcode_id = function.get("opcode_id")
            args = function.get("args")
            if not isinstance(name, str) or not name:
                raise PlatformContractError(f"Invalid API name in category {category_name}")
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
    _assert_unique(rows, "qualified_name", "API qualified name")
    _assert_unique(rows, "opcode", "API opcode name")
    _assert_unique(rows, "opcode_id", "API opcode wire id")
    return rows


def _read_isa() -> list[dict[str, Any]]:
    data = _load_json(ISA_PATH)
    _require_schema_one(data, ISA_PATH)
    columns = data.get("columns")
    expected = ["id", "producer_name", "numeric_code", "category", "canonical_index"]
    if columns != expected:
        raise PlatformContractError(
            f"canonical_isa columns changed: expected {expected}, found {columns}"
        )
    raw_rows = data.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise PlatformContractError("canonical_isa rows must be non-empty")
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_rows):
        if not isinstance(raw, list) or len(raw) != len(expected):
            raise PlatformContractError(f"Invalid canonical ISA row {index}")
        row = dict(zip(expected, raw))
        if (
            not isinstance(row["id"], str)
            or not isinstance(row["producer_name"], str)
            or not isinstance(row["numeric_code"], int)
            or not isinstance(row["category"], str)
            or not isinstance(row["canonical_index"], int)
        ):
            raise PlatformContractError(f"Invalid canonical ISA values at row {index}")
        rows.append(row)
    for key, label in (
        ("id", "canonical opcode id"),
        ("producer_name", "canonical producer name"),
        ("numeric_code", "canonical wire code"),
        ("canonical_index", "canonical index"),
    ):
        _assert_unique(rows, key, label)
    if [row["canonical_index"] for row in rows] != list(range(len(rows))):
        raise PlatformContractError("canonical_index must be contiguous and match row order")
    return rows


def _read_capabilities(
    isa_by_code: dict[int, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[int, str]]:
    data = _load_json(CAPABILITY_PATH)
    _require_schema_one(data, CAPABILITY_PATH)
    raw = data.get("capabilities")
    if not isinstance(raw, list) or not raw:
        raise PlatformContractError("capability_model capabilities must be non-empty")

    rows: list[dict[str, Any]] = []
    owner: dict[int, str] = {}
    for index, capability in enumerate(raw):
        if not isinstance(capability, dict):
            raise PlatformContractError(f"Invalid capability at row {index}")
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
            raise PlatformContractError(f"Invalid capability values at row {index}")
        if len(opcodes) != len(set(opcodes)):
            raise PlatformContractError(f"Capability {capability_id} contains duplicate opcodes")
        for code in opcodes:
            if not isinstance(code, int) or code not in isa_by_code:
                raise PlatformContractError(
                    f"Capability {capability_id} references unknown opcode {code!r}"
                )
            if code in owner:
                raise PlatformContractError(
                    f"Opcode {code} belongs to both {owner[code]} and {capability_id}"
                )
            owner[code] = capability_id
        rows.append(
            {
                "id": capability_id,
                "category": category,
                "description": description,
                "opcodes": list(opcodes),
                "required": required,
            }
        )
    _assert_unique(rows, "id", "capability id")
    missing = sorted(set(isa_by_code) - set(owner))
    if missing:
        raise PlatformContractError(f"Canonical opcodes without capability: {missing}")
    return rows, owner


def _read_targets(capabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    data = _load_json(TARGET_PROFILES_PATH)
    _require_schema_one(data, TARGET_PROFILES_PATH)
    raw = data.get("profiles")
    if not isinstance(raw, list) or not raw:
        raise PlatformContractError("target_profiles profiles must be non-empty")
    known = {row["id"] for row in capabilities}
    required = {row["id"] for row in capabilities if row["required"]}
    rows: list[dict[str, Any]] = []
    for index, profile in enumerate(raw):
        if not isinstance(profile, dict):
            raise PlatformContractError(f"Invalid target profile at row {index}")
        profile_id = profile.get("id")
        description = profile.get("description")
        values = profile.get("capabilities")
        if (
            not isinstance(profile_id, str)
            or not profile_id
            or not isinstance(description, str)
            or not isinstance(values, list)
            or any(not isinstance(value, str) for value in values)
        ):
            raise PlatformContractError(f"Invalid target profile values at row {index}")
        if len(values) != len(set(values)):
            raise PlatformContractError(f"Target {profile_id} contains duplicate capabilities")
        unknown = sorted(set(values) - known)
        if unknown:
            raise PlatformContractError(f"Target {profile_id} has unknown capabilities: {unknown}")
        missing = sorted(required - set(values))
        if missing:
            raise PlatformContractError(f"Target {profile_id} omits required capabilities: {missing}")
        rows.append(
            {"id": profile_id, "description": description, "capabilities": list(values)}
        )
    _assert_unique(rows, "id", "target profile id")
    return rows


def build_contract() -> dict[str, Any]:
    api_data = _load_yaml(API_PATH)
    api_rows = _read_api()
    isa_rows = _read_isa()
    isa_by_name = {row["producer_name"]: row for row in isa_rows}
    isa_by_code = {row["numeric_code"]: row for row in isa_rows}
    api_by_opcode = {row["opcode"]: row for row in api_rows}

    missing_api = sorted(set(isa_by_name) - set(api_by_opcode))
    unknown_api = sorted(set(api_by_opcode) - set(isa_by_name))
    if missing_api or unknown_api:
        raise PlatformContractError(
            "API/ISA opcode coverage drift: "
            f"missing={missing_api}, unknown={unknown_api}"
        )
    for api in api_rows:
        canonical = isa_by_name[api["opcode"]]
        if api["opcode_id"] != canonical["numeric_code"]:
            raise PlatformContractError(
                f"Wire-id drift for {api['qualified_name']}: "
                f"api.yaml={api['opcode_id']}, canonical={canonical['numeric_code']}"
            )

    capabilities, capability_by_code = _read_capabilities(isa_by_code)
    targets = _read_targets(capabilities)
    target_caps = {row["id"]: set(row["capabilities"]) for row in targets}

    operations: list[dict[str, Any]] = []
    for canonical in isa_rows:
        api = api_by_opcode[canonical["producer_name"]]
        capability = capability_by_code[canonical["numeric_code"]]
        operations.append(
            {
                "id": canonical["id"],
                "producer_name": canonical["producer_name"],
                "numeric_code": canonical["numeric_code"],
                "canonical_index": canonical["canonical_index"],
                "isa_category": canonical["category"],
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
                "capability": capability,
                "supported_targets": [
                    target["id"]
                    for target in targets
                    if capability in target_caps[target["id"]]
                ],
            }
        )

    capability_projection = [
        {
            **capability,
            "targets": [
                target["id"]
                for target in targets
                if capability["id"] in target_caps[target["id"]]
            ],
        }
        for capability in capabilities
    ]
    language = api_data.get("language", {})
    return {
        "type": CONTRACT_TYPE,
        "schema_version": CONTRACT_SCHEMA_VERSION,
        "generated": True,
        "language": {"name": language.get("name"), "version": language.get("version")},
        "source_ownership": {
            "api_semantics": "robot-language/specification/api.yaml",
            "opcode_identity_and_wire_code": "packages/robot-isa/canonical_isa.json",
            "capability_assignment": "packages/robot-isa/capability_model.json",
            "target_support": "packages/robot-isa/target_profiles.json",
        },
        "operations": operations,
        "capabilities": capability_projection,
        "targets": targets,
    }


def render_contract(contract: dict[str, Any] | None = None) -> str:
    return json.dumps(contract or build_contract(), indent=2, ensure_ascii=False) + "\n"


def write_contract(path: Path = PROJECTION_PATH) -> Path:
    output = Path(path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_contract(), encoding="utf-8")
    return output


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate/generate the H32 platform contract evidence")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Cross-validate all canonical contract sources")
    generate = sub.add_parser("generate", help="Generate consolidated contract evidence")
    generate.add_argument("--output", type=Path, default=PROJECTION_PATH)
    sub.add_parser("print", help="Print the generated contract to stdout")
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
            print(f"Generated platform contract: {write_contract(args.output)}")
        elif args.command == "print":
            sys.stdout.write(render_contract())
        return 0
    except PlatformContractError as exc:
        print(f"H32 PLATFORM CONTRACT ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
