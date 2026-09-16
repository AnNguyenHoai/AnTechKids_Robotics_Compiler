import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from tools.deployment_contract import DeploymentContractError, create_manifest, validate_manifest, write_manifest


def _build_dir(tmp_path: Path, program: str = "#pragma once\nconst int PROGRAM[] = {0};\n") -> Path:
    build = tmp_path / "demo"
    build.mkdir()
    (build / "program.h").write_text(program, encoding="utf-8")
    return build


def test_create_and_validate_manifest(tmp_path=None):
    with tempfile.TemporaryDirectory() as owned_tmp:
        root = Path(owned_tmp) if tmp_path is None else Path(tmp_path)
        build = _build_dir(root)
        (build / "compile_report.json").write_text('{"instruction_count": 1}', encoding="utf-8")
        manifest = create_manifest(build, "esp32", ("motion.basic",), platformio_environment="esp32dev")
        path = write_manifest(manifest, build / "deployment_manifest.json")
        loaded = validate_manifest(path, expected_target="esp32")
        assert loaded["kind"] == "robot_deployment_manifest"
        assert loaded["required_capabilities"] == ["motion.basic"]
        assert loaded["platformio_environment"] == "esp32dev"
        assert loaded["artifacts"]["program_header"]["sha256"]


def test_validation_rejects_tampered_artifact(tmp_path=None):
    with tempfile.TemporaryDirectory() as owned_tmp:
        root = Path(owned_tmp) if tmp_path is None else Path(tmp_path)
        build = _build_dir(root, "original")
        path = write_manifest(create_manifest(build, "esp32", ("motion.basic",)), build / "deployment_manifest.json")
        (build / "program.h").write_text("tampered", encoding="utf-8")
        try:
            validate_manifest(path)
        except DeploymentContractError as exc:
            assert "checksum mismatch" in str(exc)
        else:
            raise AssertionError("tampered artifact must be rejected")


def test_validation_rejects_target_mismatch(tmp_path=None):
    with tempfile.TemporaryDirectory() as owned_tmp:
        root = Path(owned_tmp) if tmp_path is None else Path(tmp_path)
        build = _build_dir(root, "header")
        path = write_manifest(create_manifest(build, "esp32", ("motion.basic",)), build / "deployment_manifest.json")
        try:
            validate_manifest(path, expected_target="arduino")
        except DeploymentContractError as exc:
            assert "target mismatch" in str(exc).lower()
        else:
            raise AssertionError("target mismatch must be rejected")


def test_create_rejects_unsupported_capability(tmp_path=None):
    with tempfile.TemporaryDirectory() as owned_tmp:
        root = Path(owned_tmp) if tmp_path is None else Path(tmp_path)
        build = _build_dir(root, "header")
        try:
            create_manifest(build, "arduino", ("motion.encoder_angle",))
        except DeploymentContractError as exc:
            assert "missing capabilities" in str(exc)
        else:
            raise AssertionError("unsupported capability must be rejected")


def test_manifest_is_json_and_schema_stable(tmp_path=None):
    with tempfile.TemporaryDirectory() as owned_tmp:
        root = Path(owned_tmp) if tmp_path is None else Path(tmp_path)
        build = _build_dir(root, "header")
        path = write_manifest(create_manifest(build, "esp32", ()), build / "deployment_manifest.json")
        document = json.loads(path.read_text(encoding="utf-8"))
        assert document["schema_version"] == 1
        assert set(document) >= {"schema_version", "kind", "target", "required_capabilities", "artifacts"}
