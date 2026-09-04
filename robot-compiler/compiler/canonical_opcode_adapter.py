"""Thin adapter from the current producer opcodes to canonical ISA semantics.

The production compiler remains the owner of opcode emission. This module is
for diagnostics, analysis, tests, and future migration work only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ISA_PATH = Path(__file__).resolve().parents[2] / "packages" / "robot-isa" / "canonical_isa.json"


def load_manifest() -> dict[str, Any]:
    return json.loads(ISA_PATH.read_text(encoding="utf-8"))


def entries() -> list[dict[str, Any]]:
    manifest = load_manifest()
    columns = manifest["columns"]
    return [dict(zip(columns, row)) for row in manifest["rows"]]


def canonical_id_for_wire_code(code: int) -> str | None:
    for entry in entries():
        if entry["numeric_code"] == code:
            return entry["id"]
    return None


def canonical_id_for_producer_name(name: str) -> str | None:
    for entry in entries():
        if entry["producer_name"] == name:
            return entry["id"]
    return None


def legacy_aliases() -> list[dict[str, Any]]:
    return [
        {"name": name, "canonical_id": canonical_id, "status": "legacy"}
        for name, canonical_id in load_manifest().get("legacy_aliases", [])
    ]
