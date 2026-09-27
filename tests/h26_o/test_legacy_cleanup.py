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
    lines = text.splitlines()
    # H26-O owns the production source boundary, not the names of isolated
    # qualification profiles. The production firmware root remains main/ and
    # includes only that canonical tree; diagnostic A/B profiles may explicitly
    # carry a "legacy" label without resurrecting retired production sources.
    assert "src_dir = main" in text
    assert "build_src_filter = +<*>" in text
    assert not any(line.strip().startswith("src_filter =") for line in lines)

    production_start = text.index("[env:esp32dev]")
    production_end = text.index("[env:esp32dev_ota]", production_start)
    production = text[production_start:production_end]
    assert "legacy" not in production.lower()
