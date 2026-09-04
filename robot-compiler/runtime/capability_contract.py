"""Runtime capability contract enforcement.

H26-J makes the capability model an execution-boundary contract.  A runtime
may opt into enforcement by providing the capability IDs it actually exposes.
The existing VM behaviour is unchanged when no runtime capability set is
provided, preserving the Golden Path while making target validation explicit.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

_ROOT = Path(__file__).resolve().parents[2]
_MODEL = _ROOT / "packages" / "robot-isa" / "capability_model.json"


class CapabilityContractError(RuntimeError):
    """Raised when a program requires capabilities absent from the runtime."""


def load_capability_model(path: Path = _MODEL) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def capability_map(model: Mapping) -> dict[str, dict]:
    return {item["id"]: dict(item) for item in model["capabilities"]}


def capability_ids_for_opcodes(
    opcodes: Iterable[int], model: Mapping | None = None
) -> tuple[str, ...]:
    """Return the capability IDs needed by an opcode sequence."""
    current = model or load_capability_model()
    opcode_set = set(int(value) for value in opcodes)
    required: list[str] = []
    for item in current["capabilities"]:
        if opcode_set.intersection(item["opcodes"]):
            required.append(item["id"])
    return tuple(required)


def validate_capabilities(
    required: Iterable[str], supported: Iterable[str]
) -> None:
    """Enforce that every program capability is exposed by the runtime."""
    required_set = set(required)
    supported_set = set(supported)
    missing = sorted(required_set - supported_set)
    if missing:
        raise CapabilityContractError(
            "Runtime capability contract violation: "
            f"missing capabilities: {', '.join(missing)}"
        )


def validate_opcode_sequence(
    opcodes: Iterable[int], supported: Iterable[str], model: Mapping | None = None
) -> tuple[str, ...]:
    """Validate an opcode sequence and return its canonical requirements."""
    required = capability_ids_for_opcodes(opcodes, model)
    validate_capabilities(required, supported)
    return required
