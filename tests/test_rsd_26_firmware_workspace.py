from pathlib import Path

import pytest

from tools import firmware_workspace


def make_template(root: Path) -> Path:
    (root / "main" / "src" / "Application").mkdir(parents=True)
    (root / "platformio.ini").write_text("[env:esp32dev]\n", encoding="utf-8")
    (root / "wifi_config.py").write_text("", encoding="utf-8")
    return root


def test_template_rejects_development_payload(tmp_path):
    template = make_template(tmp_path / "template")
    (template / ".pio").mkdir()

    with pytest.raises(firmware_workspace.FirmwareWorkspaceError, match="forbidden"):
        firmware_workspace.validate_firmware_template(template)


def test_template_requires_platformio_project_files(tmp_path):
    template = tmp_path / "template"
    template.mkdir()
    (template / "main").mkdir()

    with pytest.raises(firmware_workspace.FirmwareWorkspaceError, match="platformio.ini"):
        firmware_workspace.validate_firmware_template(template)


def test_workspace_isolated_from_template(tmp_path, monkeypatch):
    template = make_template(tmp_path / "template")
    original = template / "main" / "src" / "Application" / "original.h"
    original.write_text("original", encoding="utf-8")
    monkeypatch.setattr(
        firmware_workspace.build_isolation,
        "build_workspace",
        lambda name: tmp_path / "data" / name / "platformio",
    )

    program_header = tmp_path / "program.h"
    program_header.write_text("generated", encoding="utf-8")

    workspace = firmware_workspace.prepare_firmware_workspace(template, "student")
    generated = firmware_workspace.install_generated_header(program_header, workspace)

    assert workspace != template
    assert generated == workspace / "main" / "src" / "Application" / "generated_program.h"
    assert generated.read_text(encoding="utf-8") == "generated"
    assert not (template / "main" / "src" / "Application" / "generated_program.h").exists()
    assert original.read_text(encoding="utf-8") == "original"


def test_workspace_excludes_forbidden_payload_from_copy(tmp_path, monkeypatch):
    template = make_template(tmp_path / "template")
    (template / "main" / "__pycache__").mkdir()
    (template / "main" / "__pycache__" / "stale.pyc").write_bytes(b"stale")
    monkeypatch.setattr(
        firmware_workspace.build_isolation,
        "build_workspace",
        lambda name: tmp_path / "data" / name / "platformio",
    )

    workspace = firmware_workspace.prepare_firmware_workspace(template, "student")

    assert not (workspace / "main" / "__pycache__").exists()
    assert (workspace / "platformio.ini").is_file()
    assert (workspace / "wifi_config.py").is_file()
    assert (workspace / "main").is_dir()


def test_generated_header_missing_fails_closed(tmp_path):
    template = make_template(tmp_path / "template")

    with pytest.raises(firmware_workspace.FirmwareWorkspaceError, match="Generated header"):
        firmware_workspace.install_generated_header(tmp_path / "missing.h", template)
