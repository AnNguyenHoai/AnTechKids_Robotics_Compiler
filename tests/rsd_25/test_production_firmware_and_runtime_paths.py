from __future__ import annotations

import json
from pathlib import Path


def test_target_profiles_use_application_owned_runtime(monkeypatch, tmp_path):
    root = tmp_path / "release"
    profile = root / "runtime" / "resources" / "robot-isa" / "target_profiles.json"
    profile.parent.mkdir(parents=True)
    profile.write_text(json.dumps({"kind": "robot_target_capability_profiles", "schema_version": 1, "profiles": [{"id": "esp32", "description": "ESP32", "capabilities": ["motion.basic"]}]}), encoding="utf-8")
    monkeypatch.setenv("ROBOSTUDIO_HOME", str(root))

    from robostudio.domain.target_capability_view import TargetCapabilityService

    service = TargetCapabilityService.load()
    assert service.target_ids() == ("esp32",)
    assert service.describe("esp32") == "ESP32"


def test_production_distribution_requires_firmware_inputs(tmp_path):
    from tools.production_distribution import ProductionDistributionError, ProductionDistributionInputs, validate_inputs

    exe = tmp_path / "RoboStudio.exe"
    exe.write_bytes(b"MZ")
    resources = tmp_path / "resources"
    resources.mkdir()
    version = tmp_path / "VERSION"
    version.write_text("test", encoding="utf-8")
    runtime_bin = tmp_path / "bin"
    (runtime_bin / "Lib" / "site-packages" / "platformio").mkdir(parents=True)
    (runtime_bin / "python.exe").write_bytes(b"python")
    (runtime_bin / "Lib" / "site-packages" / "platformio" / "__init__.py").write_text("", encoding="utf-8")
    runtime_platformio = tmp_path / "platformio"
    (runtime_platformio / "platforms").mkdir(parents=True)
    (runtime_platformio / "packages").mkdir(parents=True)
    compiler = tmp_path / "compiler"
    (compiler / "compiler").mkdir(parents=True)
    (compiler / "main.py").write_text("", encoding="utf-8")
    (compiler / "robostudio_bridge.py").write_text("", encoding="utf-8")
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "__init__.py").write_text("", encoding="utf-8")
    (frontend / "rewriter.py").write_text("", encoding="utf-8")
    firmware = tmp_path / "firmware"

    inputs = ProductionDistributionInputs(exe, resources, version, runtime_bin, runtime_platformio, compiler, frontend, firmware)
    try:
        validate_inputs(inputs, tmp_path / "out")
    except ProductionDistributionError as exc:
        assert "firmware" in str(exc).lower()
    else:
        raise AssertionError("Missing production firmware project must fail closed")
