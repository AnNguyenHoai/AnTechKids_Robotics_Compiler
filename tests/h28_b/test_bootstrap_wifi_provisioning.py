#!/usr/bin/env python3
"""Static contract checks for first-flash Wi-Fi provisioning precedence."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WIFI = (ROOT / "robot-platform" / "main" / "src" / "Communication" / "RobotWiFiConfig.cpp").read_text(encoding="utf-8")
WIFI_CONFIG = (ROOT / "robot-platform" / "wifi_config.py").read_text(encoding="utf-8")


def test_bootstrap_build_forces_generated_credentials_before_nvs_fallback():
    bootstrap_guard = WIFI.index("#ifdef ROBOT_BOOTSTRAP_PROVISIONED")
    stored_fallback = WIFI.index("if (loadStored())")
    bootstrap_save = WIFI.index("Bootstrap Wi-Fi configuration forced into NVS")

    assert bootstrap_guard < stored_fallback
    assert bootstrap_save > bootstrap_guard
    assert "g_ssid = ROBOT_WIFI_SSID;" in WIFI[bootstrap_guard:stored_fallback]
    assert "g_password = ROBOT_WIFI_PASSWORD;" in WIFI[bootstrap_guard:stored_fallback]
    assert "g_otaPassword = ROBOT_OTA_PASSWORD;" in WIFI[bootstrap_guard:stored_fallback]
    assert "save(g_ssid.c_str(), g_password.c_str(), g_otaPassword.c_str())" in WIFI[bootstrap_guard:stored_fallback]


def test_platformio_bootstrap_defines_provisioning_mode():
    assert 'env.Append(CPPDEFINES=[("ROBOT_BOOTSTRAP_PROVISIONED", "1")])' in WIFI_CONFIG


def main() -> int:
    test_bootstrap_build_forces_generated_credentials_before_nvs_fallback()
    test_platformio_bootstrap_defines_provisioning_mode()
    print("Bootstrap Wi-Fi provisioning contract: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
