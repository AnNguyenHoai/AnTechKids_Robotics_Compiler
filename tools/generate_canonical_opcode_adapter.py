#!/usr/bin/env python3
"""Generate the C++ canonical opcode adapter from the single ISA manifest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ISA_PATH = ROOT / "packages" / "robot-isa" / "canonical_isa.json"
DEFAULT_OUTPUT = ROOT / "packages" / "robot-isa" / "include" / "CanonicalOpcodeAdapter.h"


def enum_name(semantic_id: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[._-]+", semantic_id))


def load_entries():
    data = json.loads(ISA_PATH.read_text(encoding="utf-8"))
    columns = data["columns"]
    return [dict(zip(columns, row)) for row in data["rows"]]


def render(entries) -> str:
    lines = [
        "#pragma once",
        "#include <cstdint>",
        "",
        "// AUTO-GENERATED FROM packages/robot-isa/canonical_isa.json.",
        "// This is an adapter boundary; do not define ISA semantics here.",
        "namespace robot_isa {",
        "",
        "enum class CanonicalOpcode : uint8_t {",
        "    Invalid = 0xFF,",
    ]
    for entry in entries:
        lines.append(f"    {enum_name(entry['id'])} = {entry['canonical_index']},")
    lines += [
        "};",
        "",
        "constexpr CanonicalOpcode fromCurrentWireCode(uint8_t code) {",
        "    switch (code) {",
    ]
    for entry in entries:
        lines.append(f"        case {entry['numeric_code']}: return CanonicalOpcode::{enum_name(entry['id'])};")
    lines += [
        "        default: return CanonicalOpcode::Invalid;",
        "    }",
        "}",
        "",
        "constexpr bool isKnownCurrentWireCode(uint8_t code) {",
        "    return fromCurrentWireCode(code) != CanonicalOpcode::Invalid;",
        "}",
        "",
        "} // namespace robot_isa",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(load_entries()), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
