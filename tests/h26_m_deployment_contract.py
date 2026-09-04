import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.deployment_contract import DeploymentContractError, create_manifest, validate_manifest, write_manifest


def test_create_and_validate_manifest(tmp_path):
    build = tmp_path / "demo"
    build.mkdir()
    (build / "program.h").write_text("#pragma once\nconst int PROGRAM[] = {0};\n", encoding="utf-8")
    (build / "compile_report.json").write_text('{"instruction_count": 1}', encoding="utf-8")
    manifest = create_manifest(build, "esp32", ("motion.basic",), platformio_environment="esp32dev")
    path = write_manifest(manifest, build / "deployment_manifest.json")
    loaded = validate_manifest(path, expected_target="esp32")
    assert loaded["kind"] == "robot_deployment_manifest"
    assert loaded["required_capabilities"] == ["motion.basic"]
    assert loaded["platformio_environment"] == "esp32dev"
    assert loaded["artifacts"]["program_header"]["sha256"]


def test_validation_rejects_tampered_artifact(tmp_path):
    build = tmp_path / "demo"
    build.mkdir()
    header = build / "program.h"
    header.write_text("original", encoding="utf-8")
    path = write_manifest(create_manifest(build, "esp32", ("motion.basic",)), build / "deployment_manifest.json")
    header.write_text("tampered", encoding="utf-8")
    try:
        validate_manifest(path)
    except DeploymentContractError as exc:
        assert "checksum mismatch" in str(exc)
    else:
        raise AssertionError("tampered artifact must be rejected")


def test_validation_rejects_target_mismatch(tmp_path):
    build = tmp_path / "demo"
    build.mkdir()
    (build / "program.h").write_text("header", encoding="utf-8")
    path = write_manifest(create_manifest(build, "esp32", ("motion.basic",)), build / "deployment_manifest.json")
    try:
        validate_manifest(path, expected_target="arduino")
    except DeploymentContractError as exc:
        assert "target mismatch" in str(exc).lower()
    else:
        raise AssertionError("target mismatch must be rejected")


def test_create_rejects_unsupported_capability(tmp_path):
    build = tmp_path / "demo"
    build.mkdir()
    (build / "program.h").write_text("header", encoding="utf-8")
    try:
        create_manifest(build, "arduino", ("motion.encoder_angle",))
    except DeploymentContractError as exc:
        assert "missing capabilities" in str(exc)
    else:
        raise AssertionError("unsupported capability must be rejected")


def test_manifest_is_json_and_schema_stable(tmp_path):
    build = tmp_path / "demo"
    build.mkdir()
    (build / "program.h").write_text("header", encoding="utf-8")
    path = write_manifest(create_manifest(build, "esp32", ()), build / "deployment_manifest.json")
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    assert set(document) >= {"schema_version", "kind", "target", "required_capabilities", "artifacts"}
