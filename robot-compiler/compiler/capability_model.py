"""Capability contract adapter for compiler-side and tooling consumers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Mapping

_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST = _ROOT / "packages" / "robot-isa" / "capability_model.json"


def load_capability_model(path: Path = _MANIFEST) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def capability_map(model: Mapping) -> Dict[str, dict]:
    return {item["id"]: dict(item) for item in model["capabilities"]}


def capability_ids_for_opcode(opcode: int, model: Mapping | None = None) -> tuple[str, ...]:
    current = model or load_capability_model()
    return tuple(item["id"] for item in current["capabilities"] if opcode in item["opcodes"])


def supported_capabilities(opcodes: Iterable[int], model: Mapping | None = None) -> tuple[str, ...]:
    current = model or load_capability_model()
    available = set(opcodes)
    return tuple(item["id"] for item in current["capabilities"] if set(item["opcodes"]).issubset(available))
