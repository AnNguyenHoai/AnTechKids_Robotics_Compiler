import tempfile
import unittest
from pathlib import Path

from domain import DeviceRegistry, HardwareConfig, HardwareConfigService


class HardwareConfigTests(unittest.TestCase):
    def test_default_contains_all_registered_devices(self):
        config = HardwareConfig.create_default()
        self.assertEqual(set(config.devices), set(DeviceRegistry.ids()))
        self.assertTrue(config.is_enabled("motor"))
        self.assertFalse(config.is_enabled("imu"))

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

    def test_unknown_device_rejected(self):
        with self.assertRaises(KeyError):
            HardwareConfig.from_dict({"version": 1, "devices": {"unknown": True}})


if __name__ == "__main__":
    unittest.main()
