import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
COMPILER_ROOT = ROOT / "robot-compiler"
if str(COMPILER_ROOT) not in sys.path:
    sys.path.insert(0, str(COMPILER_ROOT))

from runtime.target_profile import TargetCapabilityRegistry, TargetProfileError


class TargetCapabilityProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = TargetCapabilityRegistry.load()

    def test_builtin_targets_are_registered(self):
        self.assertEqual(self.registry.ids(), ("robosim", "esp32", "arduino"))

    def test_profile_is_immutable_and_contains_unique_capabilities(self):
        profile = self.registry.get("esp32")
        self.assertEqual(profile.target_id, "esp32")
        self.assertEqual(len(profile.capabilities), len(set(profile.capabilities)))
        self.assertTrue(profile.supports("runtime.control"))

    def test_profile_accepts_supported_program_requirements(self):
        self.registry.validate_program(
            "esp32",
            ("runtime.control", "motion.basic", "sensor.ultrasonic"),
        )

    def test_profile_rejects_unsupported_program_requirement(self):
        with self.assertRaisesRegex(TargetProfileError, "motion.encoder_angle"):
            self.registry.validate_program(
                "arduino",
                ("runtime.control", "motion.encoder_angle"),
            )

    def test_unknown_target_is_rejected(self):
        with self.assertRaisesRegex(TargetProfileError, "Unknown target profile"):
            self.registry.get("unknown-target")

    def test_unknown_profile_capabilities_are_not_silently_added(self):
        with self.assertRaisesRegex(TargetProfileError, "duplicate capabilities"):
            TargetCapabilityRegistry.load(
                Path(__file__).with_name("invalid_duplicate_profiles.json")
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
