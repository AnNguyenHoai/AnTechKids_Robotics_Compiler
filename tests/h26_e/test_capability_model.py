import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "packages" / "robot-isa" / "capability_model.json"
ISA = ROOT / "packages" / "robot-isa" / "canonical_isa.json"
CPP = ROOT / "packages" / "robot-isa" / "include" / "CapabilityModel.h"
PY_ADAPTER = ROOT / "robot-compiler" / "compiler" / "capability_model.py"


class CapabilityModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.isa = json.loads(ISA.read_text(encoding="utf-8"))

    def test_schema_and_ids_are_unique(self):
        self.assertEqual(self.model["schema_version"], 1)
        caps = self.model["capabilities"]
        self.assertEqual(len(caps), 16)
        ids = [c["id"] for c in caps]
        self.assertEqual(len(ids), len(set(ids)))
        for c in caps:
            self.assertTrue(re.fullmatch(r"[a-z0-9]+(?:\.[a-z0-9_]+)+", c["id"]))
            self.assertIn(c["category"], {"motion", "sensor", "actuator", "line", "peripheral", "gui", "runtime"})
            self.assertIsInstance(c["required"], bool)

    def test_opcode_membership_is_current_isa_only(self):
        current_codes = {row[2] for row in self.isa["rows"]}
        covered = set()
        for cap in self.model["capabilities"]:
            self.assertTrue(cap["opcodes"])
            for code in cap["opcodes"]:
                self.assertIn(code, current_codes)
                covered.add(code)
        self.assertEqual(covered, current_codes)

    def test_required_baseline(self):
        required = {c["id"] for c in self.model["capabilities"] if c["required"]}
        self.assertEqual(required, {"motion.basic", "runtime.control"})

    def test_python_adapter_exposes_contract(self):
        text = PY_ADAPTER.read_text(encoding="utf-8")
        self.assertIn("capability_ids_for_opcode", text)
        self.assertIn("supported_capabilities", text)
        self.assertIn("capability_map", text)

    def test_cpp_adapter_matches_manifest_ids_and_opcode_lists(self):
        text = CPP.read_text(encoding="utf-8")
        for cap in self.model["capabilities"]:
            self.assertIn('"' + cap["id"] + '"', text)
            for code in cap["opcodes"]:
                self.assertIn(str(code), text)
        self.assertIn("inline bool supports", text)

    def test_no_capability_renumbers_opcode(self):
        self.assertEqual([row[2] for row in self.isa["rows"]], [
            2,3,4,5,35,52,53,7,6,30,31,32,33,34,42,43,44,54,
            37,38,36,55,56,57,58,39,47,48,49,59,40,50,51,60,41,61,
            62,63,1,8,9,10,11,12,13,14,15,16,17,20,21,22,23,24,25,26,27,28,29,64
        ])


if __name__ == "__main__":
    unittest.main()
