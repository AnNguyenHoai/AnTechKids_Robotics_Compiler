from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_retired_runtime_and_deployment_scripts_are_absent():
    retired = (
        ROOT / "robot-platform" / "legacy" / "runtime_cpp_prototype",
        ROOT / "robot-platform" / "legacy" / "README.md",
        ROOT / "robot-platform" / "deploy.py",
        ROOT / "robot-platform" / "deploy_program.py",
    )
    assert all(not path.exists() for path in retired)


def test_canonical_deployment_entry_point_exists():
    deploy = ROOT / "tools" / "deploy_robot.py"
    assert deploy.is_file()
    text = deploy.read_text(encoding="utf-8")
    assert "deployment_contract" in text
    assert "esp32dev_ota" in text


def test_production_firmware_source_filter_excludes_legacy():
    platformio = ROOT / "robot-platform" / "platformio.ini"
    text = platformio.read_text(encoding="utf-8")
    assert "src_filter = +<src/*>" in text
    assert "legacy" not in text
