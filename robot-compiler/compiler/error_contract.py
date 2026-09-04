"""H26-D canonical Robot VM error contract adapter.

The JSON manifest is authoritative; this module intentionally contains no
independent numeric assignments.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_MANIFEST = Path(__file__).resolve().parents[2] / "packages" / "robot-isa" / "error_contract.json"


def _load() -> dict[str, Any]:
    with _MANIFEST.open("r", encoding="utf-8") as handle:
        return json.load(handle)


_CONTRACT = _load()
_BY_CODE = {int(entry["code"]): entry for entry in _CONTRACT["errors"]}
_BY_ID = {entry["id"]: entry for entry in _CONTRACT["errors"]}


class VMError:
    """Stable VM error value exposed to compiler/IDE-side Python tooling."""

    OK = 0
    INVALID_OPCODE = 1
    PROGRAM_OVERFLOW = 2
    INVALID_JUMP = 3
    STACK_OVERFLOW = 4
    INVALID_RETURN = 5
    DIVISION_BY_ZERO = 6
    MODULO_BY_ZERO = 7
    INVALID_OPERAND = 8
    INVALID_VARIABLE = 9
    UNKNOWN = int(_CONTRACT["unknown_code"])


def error_by_code(code: int) -> dict[str, Any] | None:
    """Return the canonical error entry for a numeric code."""
    return _BY_CODE.get(int(code))


def error_by_id(error_id: str) -> dict[str, Any] | None:
    """Return the canonical error entry for a semantic id."""
    return _BY_ID.get(error_id)


def message_for_code(code: int) -> str:
    """Return the canonical diagnostic message, with an unknown fallback."""
    entry = error_by_code(code)
    return entry["message"] if entry else f"Unknown VM error code {int(code)}."


def contract_version() -> int:
    return int(_CONTRACT["schema_version"])
