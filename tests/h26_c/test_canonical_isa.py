from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "robot-compiler"))

from compiler import canonical_opcode_adapter as adapter


def parse_generated_opcodes() -> dict[str, int]:
    path = ROOT / "robot-compiler" / "compiler" / "generated" / "opcode.py"
    text = path.read_text(encoding="utf-8")
    matches = re.findall(
        r"^    ([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(-?\d+)\s*$",
        text,
        re.MULTILINE,
    )
    return {name: int(value) for name, value in matches}


class TestCanonicalIsa(unittest.TestCase):
    def test_manifest_is_valid_and_deterministic(self):
        manifest = adapter.load_manifest()
        entries = adapter.entries()
        indices = [entry["canonical_index"] for entry in entries]
        self.assertEqual(indices, list(range(len(entries))))
        self.assertEqual(len(entries), len({entry["id"] for entry in entries}))
        self.assertEqual(len(entries), len({entry["numeric_code"] for entry in entries}))
        self.assertEqual(len(manifest["rows"]), 60)

    def test_current_producer_is_covered_one_to_one(self):
        producer = parse_generated_opcodes()
        canonical = {entry["producer_name"]: entry["numeric_code"] for entry in adapter.entries()}
        self.assertEqual(producer, canonical)

    def test_wire_and_name_lookups_resolve_same_semantics(self):
        for entry in adapter.entries():
            self.assertEqual(
                adapter.canonical_id_for_wire_code(entry["numeric_code"]),
                entry["id"],
            )
            self.assertEqual(
                adapter.canonical_id_for_producer_name(entry["producer_name"]),
                entry["id"],
            )
        self.assertIsNone(adapter.canonical_id_for_wire_code(255))
        self.assertIsNone(adapter.canonical_id_for_producer_name("UNKNOWN"))

    def test_legacy_names_are_explicitly_isolated(self):
        current_names = {entry["producer_name"] for entry in adapter.entries()}
        legacy = adapter.legacy_aliases()
        self.assertEqual(len(legacy), 12)
        for entry in legacy:
            self.assertEqual(entry["status"], "legacy")
            self.assertNotIn(entry["name"], current_names)

    def test_cpp_adapter_is_derived_from_canonical_source(self):
        generator = ROOT / "tools" / "generate_canonical_opcode_adapter.py"
        target = ROOT / "packages" / "robot-isa" / "include" / "CanonicalOpcodeAdapter.h"
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "CanonicalOpcodeAdapter.h"
            subprocess.check_call([sys.executable, str(generator), "--output", str(output)])
            self.assertEqual(output.read_text(encoding="utf-8"), target.read_text(encoding="utf-8"))

    def test_canonical_ids_are_independent_from_wire_numbers(self):
        for entry in adapter.entries():
            self.assertIn(".", entry["id"])
            self.assertNotEqual(entry["id"], str(entry["numeric_code"]))


if __name__ == "__main__":
    unittest.main()
