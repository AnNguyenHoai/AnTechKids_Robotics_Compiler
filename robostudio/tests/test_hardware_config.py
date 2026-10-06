import tempfile
import unittest
from pathlib import Path

from domain import DeviceRegistry, HardwareConfig, HardwareConfigService
from domain.hardware_config import BOARD_PROFILE, DEVICE_CONFIG_VERSION


class HardwareConfigTests(unittest.TestCase):
    def test_default_contains_all_registered_devices(self):
        config = HardwareConfig.create_default()
        self.assertEqual(set(config.devices), set(DeviceRegistry.ids()))
        self.assertTrue(config.is_enabled("motor"))
        self.assertFalse(config.is_enabled("imu"))
        self.assertEqual(config.version, DEVICE_CONFIG_VERSION)
        self.assertEqual(config.board_profile, BOARD_PROFILE)

    def test_toggle_device(self):
        config = HardwareConfig.create_default()
        config.set_enabled("imu", True)
        self.assertTrue(config.is_enabled("imu"))

    def test_json_round_trip(self):
        config = HardwareConfig.create_default()
        config.set_enabled("encoder", True)
        restored = HardwareConfig.from_dict(config.to_dict())
        self.assertTrue(restored.is_enabled("encoder"))

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "hardware.json"
            service = HardwareConfigService(path)
            config = HardwareConfig.create_default()
            config.set_enabled("imu", True)
            service.save(config)
            loaded = service.load()
            self.assertTrue(loaded.is_enabled("imu"))

    def test_v1_migrates_without_losing_device_selection(self):
        config = HardwareConfig.from_dict({
            "version": 1,
            "devices": {
                "motor": False,
                "encoder": True,
                "servo": True,
            },
        })
        self.assertEqual(config.version, 2)
        self.assertEqual(config.board_profile, "antech_robot_v2")
        self.assertFalse(config.is_enabled("motor"))
        self.assertTrue(config.is_enabled("encoder"))
        self.assertTrue(config.is_enabled("servo"))
        self.assertEqual(config.to_dict()["version"], 2)
        self.assertEqual(config.to_dict()["board_profile"], "antech_robot_v2")

    def test_unknown_board_profile_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported board profile"):
            HardwareConfig.from_dict({
                "version": 2,
                "board_profile": "unknown_robot",
                "devices": {},
            })

    def test_v2_missing_board_profile_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported board profile"):
            HardwareConfig.from_dict({"version": 2, "devices": {}})

    def test_unknown_device_rejected(self):
        with self.assertRaises(KeyError):
            HardwareConfig.from_dict({
                "version": 2,
                "board_profile": "antech_robot_v2",
                "devices": {"unknown": True},
            })


if __name__ == "__main__":
    unittest.main()
