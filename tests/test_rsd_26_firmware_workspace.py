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


def test_workspace_isolated_from_template(tmp_path, monkeypatch):
    template = make_template(tmp_path / "template")
    (template / "main" / "src" / "Application" / "original.h").write_text("original", encoding="utf-8")
    monkeypatch.setattr(firmware_workspace.build_isolation, "build_workspace", lambda name: tmp_path / "data" / name / "platformio")

    workspace = firmware_workspace.prepare_firmware_workspace(template, "student")
    generated = firmware_workspace.install_generated_header(
        tmp_path / "program.h", workspace
    ) if (tmp_path / "program.h").write_text("generated", encoding="utf-8") else None

    assert workspace != template
    assert generated is not None
    assert (workspace / "main" / "src" / "Application" / "generated_program.h").read_text(encoding="utf-8") == "generated"
    assert not (template / "main" / "src" / "Application" / "generated_program.h").exists()
    assert (template / "main" / "src" / "Application" / "original.h").read_text(encoding="utf-8") == "original"


def test_workspace_has_required_platformio_project(tmp_path, monkeypatch):
    template = make_template(tmp_path / "template")
    monkeypatch.setattr(firmware_workspace.build_isolation, "build_workspace", lambda name: tmp_path / "data" / name / "platformio")
    workspace = firmware_workspace.prepare_firmware_workspace(template, "bootstrap")
    assert (workspace / "platformio.ini").is_file()
    assert (workspace / "wifi_config.py").is_file()
    assert (workspace / "main").is_dir()
