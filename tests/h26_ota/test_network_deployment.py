import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_deploy_capability_inference_is_deterministic(tmp_path=None):
    with tempfile.TemporaryDirectory() as owned_tmp:
        root = Path(owned_tmp) if tmp_path is None else Path(tmp_path)
        module = load_module("deploy_robot", "tools/deploy_robot.py")
        header = root / "program.h"
        header.write_text(
            "Instruction(Opcode::Forward, 50, 0, 0, 0),\n"
            "Instruction(Opcode::ReadLine, 0, 0, 0, 0),\n"
            "Instruction(Opcode::SetServo, 90, 0, 0, 0),\n",
            encoding="utf-8",
        )
        assert module.infer_capabilities(header) == [
            "actuator.servo", "motion.basic", "runtime.control", "sensor.line"
        ]


def test_physical_validation_reports_all_required_checks():
    module = load_module("validate_robot", "tools/validate_robot.py")

    responses = {
        "/api/v1/info": {"device": "AnTechKids-Robot", "target": "esp32", "ota": True},
        "/api/v1/health": {"status": "ok", "ready": True, "hostname": "robot-ABC123", "ip": "192.168.1.50"},
    }

    def fake_get_json(url, timeout):
        endpoint = "/api/v1/" + url.rstrip("/").rsplit("/", 1)[-1]
        return responses[endpoint]

    module.get_json = fake_get_json
    info = fake_get_json("http://robot/api/v1/info", 1)
    health = fake_get_json("http://robot/api/v1/health", 1)
    assert info["device"] == "AnTechKids-Robot"
    assert health["ready"] is True


def test_wifi_config_script_is_credential_source_only():
    script = ROOT / "robot-platform" / "wifi_config.py"
    text = script.read_text(encoding="utf-8")
    assert "ROBOT_WIFI_SSID" in text
    assert "ROBOT_WIFI_PASSWORD" in text
    assert "ROBOT_OTA_PASSWORD" in text
    assert "StringifyMacro" in text
