#!/usr/bin/env python3
"""Replay frozen compatibility fixtures against compiler and firmware ISA."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPILER_ROOT = ROOT / "robot-compiler"
if str(COMPILER_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPILER_ROOT))

from compiler.compiler import RobotCompiler  # noqa: E402
from compiler.generated.opcode import Opcode  # noqa: E402

FIXTURE = Path(__file__).with_name("fixtures") / "compatibility_replay_v1.json"
CANONICAL = ROOT / "packages" / "robot-isa" / "canonical_isa.json"
FIRMWARE_OPCODE = ROOT / "robot-platform" / "main" / "include" / "generated" / "opcode.h"
EXAMPLES = COMPILER_ROOT / "examples"


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def main() -> int:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    firmware = FIRMWARE_OPCODE.read_text(encoding="utf-8")

    expected = {str(k): int(v) for k, v in fixture["opcodes"].items()}
    canonical_map = {str(row[1]): int(row[2]) for row in canonical["rows"]}
    compiler_map = {name: int(member.value) for name, member in Opcode.__members__.items()}

    check("frozen compatibility generation remains v1", fixture["compatibility_generation"] == 1)
    check("canonical opcode count matches frozen generation", len(canonical_map) == fixture["canonical_opcode_count"])
    check("canonical ISA exactly replays frozen opcode map", canonical_map == expected)
    check("compiler generated opcode map exactly replays fixture", compiler_map == expected)

    firmware_map: dict[str, int] = {}
    for match in re.finditer(r"^\s*(\w+)\s*=\s*(\d+)\s*,\s*$", firmware, re.MULTILINE):
        firmware_map[match.group(1)] = int(match.group(2))
    check("firmware generated opcode map exactly replays fixture", firmware_map == expected)

    compiler = RobotCompiler()
    for filename, expected_program in fixture["programs"].items():
        program = compiler.compile(EXAMPLES / filename)
        actual = [
            [Opcode(ins.opcode).name, int(ins.p1), int(ins.p2), int(ins.p3)]
            for ins in program.instructions
        ]
        check(f"compiler replay stable: {filename}", actual == expected_program)

    print("VM-RT compatibility fixture replay: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
