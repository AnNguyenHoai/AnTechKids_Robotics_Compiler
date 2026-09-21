#!/usr/bin/env python3
"""H34 contract traceability checker and evidence generator.

Builds a read-only trace graph across the canonical contract owners and the
runtime implementation boundary:

  Robot API -> compiler registry -> canonical opcode -> capability -> targets
            -> VM dispatch -> runtime endpoint

The checker fails closed when a public API becomes orphaned or contradictory.
It does not create a second source of truth; the emitted JSON is evidence only.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
API_PATH = ROOT / "robot-language" / "specification" / "api.yaml"
ISA_PATH = ROOT / "packages" / "robot-isa" / "canonical_isa.json"
CAPABILITY_PATH = ROOT / "packages" / "robot-isa" / "capability_model.json"
TARGET_PATH = ROOT / "packages" / "robot-isa" / "target_profiles.json"
REGISTRY_PATH = ROOT / "robot-compiler" / "compiler" / "generated" / "function_registry.py"
OPCODE_PATH = ROOT / "robot-compiler" / "compiler" / "generated" / "opcode.py"
VM_PATH = ROOT / "robot-platform" / "main" / "src" / "Services" / "VM" / "VM.cpp"
DEFAULT_OUTPUT = ROOT / ".build" / "h34" / "contract-traceability.json"


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected object in {path.relative_to(ROOT)}")
    return value


def _load_api() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load(API_PATH.read_text(encoding="utf-8"))
    result: dict[str, dict[str, Any]] = {}
    for category, spec in data.get("categories", {}).items():
        if category == "internal":
            continue
        for function in spec.get("functions", []):
            name = function["name"]
            if name in result:
                raise ValueError(f"Duplicate public API: {name}")
            result[name] = {
                "category": category,
                "opcode": function["opcode"],
                "opcode_id": int(function["opcode_id"]),
                "semantic": function.get("semantic"),
            }
    return result


def _parse_registry() -> dict[str, str]:
    text = REGISTRY_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        r'^\s{4}"([A-Za-z_][A-Za-z0-9_]*)"\s*:\s*\{(.*?)^\s{4}\},',
        re.MULTILINE | re.DOTALL,
    )
    result: dict[str, str] = {}
    for name, body in pattern.findall(text):
        match = re.search(r'"opcode"\s*:\s*"([A-Za-z_][A-Za-z0-9_]*)"', body)
        if match:
            result[name] = match.group(1)
    return result


def _parse_generated_opcodes() -> dict[str, int]:
    text = OPCODE_PATH.read_text(encoding="utf-8")
    return {
        name: int(value)
        for name, value in re.findall(
            r"^\s{4}([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(-?\d+)\s*$",
            text,
            re.MULTILINE,
        )
    }


def _parse_vm_dispatch() -> dict[str, list[str]]:
    text = VM_PATH.read_text(encoding="utf-8")
    matches = list(re.finditer(r"case\s+Opcode::([A-Za-z_][A-Za-z0-9_]*)\s*:", text))
    result: dict[str, list[str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else text.find("default:", match.end())
        if end < 0:
            end = len(text)
        block = text[match.end():end]
        endpoints = [f"RobotAPI::{name}" for name in re.findall(r"RobotAPI::([A-Za-z_][A-Za-z0-9_]*)", block)]
        endpoints += [
            f"CooperativeLineOperation::{name}"
            for name in re.findall(r"CooperativeLineOperation::([A-Za-z_][A-Za-z0-9_]*)", block)
        ]
        if not endpoints:
            endpoints = ["VM::ExecuteInstruction"]
        result[match.group(1)] = sorted(set(endpoints))
    return result


def build_traceability() -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    api = _load_api()
    isa = _load_json(ISA_PATH)
    capabilities = _load_json(CAPABILITY_PATH)
    targets = _load_json(TARGET_PATH)
    registry = _parse_registry()
    generated_opcodes = _parse_generated_opcodes()
    vm_dispatch = _parse_vm_dispatch()

    isa_by_name: dict[str, dict[str, Any]] = {}
    isa_by_code: dict[int, dict[str, Any]] = {}
    for row in isa.get("rows", []):
        canonical_id, producer_name, numeric_code, category, canonical_index = row
        item = {
            "canonical_id": canonical_id,
            "producer_name": producer_name,
            "opcode_id": int(numeric_code),
            "category": category,
            "canonical_index": int(canonical_index),
        }
        if producer_name in isa_by_name:
            errors.append(f"duplicate canonical producer: {producer_name}")
        if int(numeric_code) in isa_by_code:
            errors.append(f"duplicate canonical opcode id: {numeric_code}")
        isa_by_name[producer_name] = item
        isa_by_code[int(numeric_code)] = item

    capability_by_opcode: dict[int, str] = {}
    capability_ids: set[str] = set()
    for capability in capabilities.get("capabilities", []):
        cap_id = capability["id"]
        capability_ids.add(cap_id)
        for opcode_id in capability.get("opcodes", []):
            opcode_id = int(opcode_id)
            if opcode_id in capability_by_opcode:
                errors.append(
                    f"opcode {opcode_id} belongs to multiple capabilities: "
                    f"{capability_by_opcode[opcode_id]}, {cap_id}"
                )
            capability_by_opcode[opcode_id] = cap_id
            if opcode_id not in isa_by_code:
                errors.append(f"capability {cap_id} references unknown opcode {opcode_id}")

    profile_ids: set[str] = set()
    targets_by_capability: dict[str, list[str]] = {cap_id: [] for cap_id in capability_ids}
    for profile in targets.get("profiles", []):
        target_id = profile["id"]
        profile_ids.add(target_id)
        for cap_id in profile.get("capabilities", []):
            if cap_id not in capability_ids:
                errors.append(f"target {target_id} references unknown capability {cap_id}")
                continue
            targets_by_capability[cap_id].append(target_id)

    resource_by_api: dict[str, list[str]] = {}
    for resource in targets.get("resources", []):
        resource_id = resource["id"]
        cap_id = resource.get("capability")
        if cap_id not in capability_ids:
            errors.append(f"resource {resource_id} references unknown capability {cap_id}")
        resource_targets = set(resource.get("targets", {}))
        if resource_targets != profile_ids:
            errors.append(
                f"resource {resource_id} target coverage mismatch: "
                f"expected {sorted(profile_ids)}, got {sorted(resource_targets)}"
            )
        for binding in resource.get("bindings", []):
            api_name = binding.get("api")
            if api_name not in api:
                errors.append(f"resource {resource_id} references unknown public API {api_name}")
                continue
            resource_by_api.setdefault(api_name, []).append(resource_id)

    rows: list[dict[str, Any]] = []
    for api_name in sorted(api):
        api_spec = api[api_name]
        opcode_name = api_spec["opcode"]
        opcode_id = api_spec["opcode_id"]
        canonical = isa_by_name.get(opcode_name)
        registry_opcode = registry.get(api_name)
        generated_id = generated_opcodes.get(opcode_name)
        capability = capability_by_opcode.get(opcode_id)
        dispatch = vm_dispatch.get(opcode_name)

        if canonical is None:
            errors.append(f"API {api_name} opcode {opcode_name} missing from canonical ISA")
        else:
            if canonical["opcode_id"] != opcode_id:
                errors.append(
                    f"API {api_name} opcode id mismatch: api={opcode_id}, canonical={canonical['opcode_id']}"
                )
        if registry_opcode is None:
            errors.append(f"API {api_name} missing from generated compiler registry")
        elif registry_opcode != opcode_name:
            errors.append(
                f"API {api_name} registry opcode mismatch: api={opcode_name}, registry={registry_opcode}"
            )
        if generated_id is None:
            errors.append(f"API {api_name} opcode {opcode_name} missing from generated Opcode enum")
        elif generated_id != opcode_id:
            errors.append(
                f"API {api_name} generated opcode id mismatch: api={opcode_id}, generated={generated_id}"
            )
        if capability is None:
            errors.append(f"API {api_name} opcode {opcode_id} has no capability binding")
        if dispatch is None:
            errors.append(f"API {api_name} opcode {opcode_name} has no VM dispatch case")

        rows.append(
            {
                "api": api_name,
                "api_category": api_spec["category"],
                "semantic": api_spec["semantic"],
                "canonical_id": canonical["canonical_id"] if canonical else None,
                "opcode": opcode_name,
                "opcode_id": opcode_id,
                "compiler_registry": registry_opcode,
                "capability": capability,
                "targets": sorted(targets_by_capability.get(capability, [])) if capability else [],
                "resources": sorted(resource_by_api.get(api_name, [])),
                "vm_dispatch": dispatch or [],
            }
        )

    public_names = set(api)
    extra_registry = sorted(set(registry) - public_names)
    if extra_registry:
        errors.append(f"compiler registry exposes APIs absent from api.yaml: {extra_registry}")

    report = {
        "schema_version": 1,
        "task": "H34",
        "kind": "contract_traceability_evidence",
        "status": "PASS" if not errors else "FAIL",
        "source_of_truth": {
            "api": str(API_PATH.relative_to(ROOT)).replace("\\", "/"),
            "isa": str(ISA_PATH.relative_to(ROOT)).replace("\\", "/"),
            "capabilities": str(CAPABILITY_PATH.relative_to(ROOT)).replace("\\", "/"),
            "targets": str(TARGET_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
        "implementation_evidence": {
            "compiler_registry": str(REGISTRY_PATH.relative_to(ROOT)).replace("\\", "/"),
            "generated_opcode": str(OPCODE_PATH.relative_to(ROOT)).replace("\\", "/"),
            "vm_dispatch": str(VM_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
        "summary": {
            "public_api_count": len(api),
            "trace_row_count": len(rows),
            "canonical_opcode_count": len(isa_by_name),
            "capability_count": len(capability_ids),
            "target_count": len(profile_ids),
            "error_count": len(errors),
        },
        "rows": rows,
        "errors": errors,
    }
    return report, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="H34 contract traceability gate")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Trace evidence JSON output path")
    args = parser.parse_args()

    try:
        report, errors = build_traceability()
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"H34 ERROR: {exc}")
        return 2

    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = report["summary"]
    print(
        "H34 traceability: "
        f"APIs={summary['public_api_count']} "
        f"rows={summary['trace_row_count']} "
        f"capabilities={summary['capability_count']} "
        f"targets={summary['target_count']} "
        f"errors={summary['error_count']}"
    )
    for error in errors:
        print(f"ERROR: {error}")
    print(f"Evidence: {output}")
    print(f"H34 Contract Traceability + CI Gates: {report['status']}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
