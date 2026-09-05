#!/usr/bin/env python3
"""H27-B0 Arduino IDE first-flash package contract tests."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    generator = ROOT / "tools" / "arduino_first_flash.py"
    service = ROOT / "robostudio" / "services" / "bootstrap_config_service.py"
    ui = ROOT / "robostudio" / "ui" / "robot_tab.py"

    for path in (generator, service, ui):
        assert path.is_file(), f"missing Arduino first-flash file: {path}"

    generator_text = generator.read_text(encoding="utf-8")
    assert "generate_package" in generator_text
    assert "FirstFlash.ino" in generator_text
    assert "bootstrap_secrets.h" in generator_text
    assert "ArduinoOTA" in generator_text
    assert "ANTECHKIDS_ROBOT_DISCOVER_V1" in generator_text

    service_text = service.read_text(encoding="utf-8")
    assert "generate_arduino_package" in service_text
    assert "tools.arduino_first_flash" in service_text

    ui_text = ui.read_text(encoding="utf-8")
    assert "Generate Arduino IDE Package" in ui_text
    assert "generate_arduino_package" in ui_text
    assert "FirstFlash.ino" in ui_text

    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "AnTechKidsFirstFlash"
        result = __import__("subprocess").run(
            [
                "python", str(generator),
                "--ssid", "Classroom-WiFi",
                "--password", "secret",
                "--ota-password", "ota-secret",
                "--output", str(output),
            ], cwd=ROOT, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert (output / "FirstFlash.ino").is_file()
        assert (output / "bootstrap_secrets.h").is_file()
        assert (output / "README.txt").is_file()

        secrets = (output / "bootstrap_secrets.h").read_text(encoding="utf-8")
        assert '#define ROBOT_WIFI_SSID "Classroom-WiFi"' in secrets
        assert '#define ROBOT_WIFI_PASSWORD "secret"' in secrets
        assert '#define ROBOT_OTA_PASSWORD "ota-secret"' in secrets

        sketch = (output / "FirstFlash.ino").read_text(encoding="utf-8")
        assert "WiFi.begin(ROBOT_WIFI_SSID, ROBOT_WIFI_PASSWORD)" in sketch
        assert "ArduinoOTA.setPassword(ROBOT_OTA_PASSWORD)" in sketch
        assert "udp.begin(DISCOVERY_PORT)" in sketch
        assert 'server.on("/api/v1/info"' in sketch

    print("H27-B0 Arduino PASS: Arduino IDE first-flash package")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
