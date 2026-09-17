from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

import pytest

from tools import production_firmware_e2e as e2e


def make_artifact(tmp_path: Path, *, python_name: str = "python.exe") -> Path:
    root = tmp_path / "RoboStudio-1.0"
    (root / "firmware" / "robot-platform" / "main" / "src" / "Application").mkdir(parents=True)
    (root / "firmware" / "robot-platform" / "platformio.ini").write_text(
        "[platformio]\nsrc_dir = main\n\n[env:esp32dev]\nplatform = espressif32@6.12.0\nboard = esp32dev\nframework = arduino\n\n"
        "[env:esp32dev_bootstrap]\nextends = env:esp32dev\n\n[env:esp32dev_ota]\nextends = env:esp32dev\n",
        encoding="utf-8",
    )
    (root / "firmware" / "robot-platform" / "wifi_config.py").write_text("# fixture\n", encoding="utf-8")
    platform = root / "runtime" / "platformio" / "platforms" / "espressif32"
    platform.mkdir(parents=True)
    (platform / "platform.json").write_text(
        '{"name":"espressif32","version":"6.12.0","packages":{"toolchain":{"version":"1.0.0"}}}',
        encoding="utf-8",
    )
    package = root / "runtime" / "platformio" / "packages" / "toolchain"
    package.mkdir(parents=True)
    (package / "package.json").write_text('{"name":"toolchain","version":"1.0.0"}', encoding="utf-8")
    python = root / "runtime" / "bin" / python_name
    python.parent.mkdir(parents=True)
    python.write_bytes(b"fixture")
    artifact = tmp_path / "RoboStudio.zip"
    with zipfile.ZipFile(artifact, "w") as archive:
        for path in root.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(tmp_path))
    return artifact


def test_platformio_command_uses_bundled_python(tmp_path):
    python = tmp_path / "python.exe"
    python.write_bytes(b"fixture")
    assert e2e._platformio_command(python) == [str(python), "-m", "platformio", "run"]


def test_platformio_command_rejects_non_windows_runtime(tmp_path):
    python = tmp_path / "python"
    python.write_bytes(b"fixture")
    with pytest.raises(e2e.ProductionFirmwareE2EError, match="Windows Python"):
        e2e._platformio_command(python)


def test_build_environment_overrides_host_platformio_state(tmp_path):
    runtime = tmp_path / "runtime"
    workspace = tmp_path / "workspace"
    env = e2e._build_environment(runtime, workspace, {"PLATFORMIO_HOME": "host-home", "PATH": "host-path"})
    assert env["PLATFORMIO_CORE_DIR"] == str(runtime)
    assert env["PLATFORMIO_PLATFORMS_DIR"] == str(runtime / "platforms")
    assert env["PLATFORMIO_PACKAGES_DIR"] == str(runtime / "packages")
    assert "PLATFORMIO_HOME" not in env
    assert env["PATH"] == "host-path"


def test_safe_extract_rejects_zip_traversal(tmp_path):
    artifact = tmp_path / "bad.zip"
    with zipfile.ZipFile(artifact, "w") as archive:
        archive.writestr("../escape.txt", "bad")
    with pytest.raises(e2e.ProductionFirmwareE2EError, match="unsafe ZIP member"):
        e2e._safe_extract(artifact, tmp_path / "extract")


def test_e2e_requires_bundled_python_in_artifact(tmp_path):
    artifact = make_artifact(tmp_path, python_name="not-python")
    with pytest.raises(e2e.ProductionFirmwareE2EError, match="Bundled Python runtime"):
        e2e.build_production_firmware(artifact, timeout=1)


def test_success_records_firmware_evidence(tmp_path, monkeypatch):
    artifact = make_artifact(tmp_path)
    fake_binary = tmp_path / "fake-firmware.bin"
    fake_binary.write_bytes(b"firmware")

    def fake_run(command, *, cwd, env, timeout):
        output = cwd.parent / "pio-build" / "esp32dev" / "firmware.bin"
        output.parent.mkdir(parents=True)
        output.write_bytes(fake_binary.read_bytes())
        return subprocess.CompletedProcess(command, 0, "build ok", "")

    monkeypatch.setattr(e2e, "_run", fake_run)
    result = e2e.build_production_firmware(artifact, timeout=1)
    assert result.passed
    assert result.firmware_size == len(b"firmware")
    assert len(result.firmware_sha256) == 64
    assert result.evidence["host_python_used"] is False
    assert result.evidence["host_platformio_resolution"] is False
