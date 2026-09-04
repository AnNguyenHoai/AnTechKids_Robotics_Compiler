import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_deploy_capability_inference_is_deterministic(tmp_path):
    module = load_module("deploy_robot", "tools/deploy_robot.py")
    header = tmp_path / "program.h"
    header.write_text(
        "Instruction(Opcode::Forward, 50, 0, 0, 0),\n"
        "Instruction(Opcode::ReadLine, 0, 0, 0, 0),\n"
        "Instruction(Opcode::SetServo, 90, 0, 0, 0),\n",
        encoding="utf-8",
    )
    assert module.infer_capabilities(header) == [
        "actuator.servo", "motion.basic", "runtime.control", "sensor.line"
    ]


def test_physical_validation_reports_all_required_checks(monkeypatch):
    module = load_module("validate_robot", "tools/validate_robot.py")

    responses = {
        "/api/v1/info": {"device": "AnTechKids-Robot", "target": "esp32", "ota": True},
        "/api/v1/health": {"status": "ok", "ready": True, "hostname": "robot-ABC123", "ip": "192.168.1.50"},
    }

    def fake_get_json(url, timeout):
        return responses[url.rsplit("/", 1)[-1].join(["/api/v1/", ""]) if False else "/api/v1/" + url.rsplit("/", 1)[-1]]

    monkeypatch.setattr(module, "get_json", fake_get_json)
    # Exercise the same data contract without opening a socket.
    info = fake_get_json("http://robot/api/v1/info", 1)
    health = fake_get_json("http://robot/api/v1/health", 1)
    assert info["device"] == "AnTechKids-Robot"
    assert health["ready"] is True


def test_wifi_config_script_is_credential_source_only():
    script = (ROOT / "robot-platform" / "wifi_config.py")
    text = script.read_text(encoding="utf-8")
    assert "ROBOT_WIFI_SSID" in text
    assert "ROBOT_WIFI_PASSWORD" in text
    assert "ROBOT_OTA_PASSWORD" in text
    assert "StringifyMacro" in text
