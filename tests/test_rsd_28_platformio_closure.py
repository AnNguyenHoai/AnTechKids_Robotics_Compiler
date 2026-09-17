import json
from pathlib import Path

import pytest

from tools.production_platformio_closure import ProductionPlatformIOClosureError, validate_firmware_project


def make_fixture(root: Path, *, platform="espressif32@6.12.0", platform_version="6.12.0", package_version="1.0.0"):
    firmware = root / "firmware"
    runtime = root / "runtime" / "platformio"
    (firmware / "main").mkdir(parents=True)
    (runtime / "platforms" / "espressif32").mkdir(parents=True)
    (runtime / "packages" / "toolchain").mkdir(parents=True)
    (firmware / "platformio.ini").write_text(
        "[platformio]\nsrc_dir = main\n\n"
        "[env:esp32dev]\nplatform = " + platform + "\nboard = esp32dev\nframework = arduino\n\n"
        "[env:esp32dev_bootstrap]\nextends = env:esp32dev\n\n"
        "[env:esp32dev_ota]\nextends = env:esp32dev\n",
        encoding="utf-8",
    )
    platform_metadata = {
        "name": "espressif32",
        "version": platform_version,
        "packages": {"toolchain": {"version": package_version}},
    }
    (runtime / "platforms" / "espressif32" / "platform.json").write_text(json.dumps(platform_metadata), encoding="utf-8")
    (runtime / "packages" / "toolchain" / "package.json").write_text(
        json.dumps({"name": "toolchain", "version": package_version}), encoding="utf-8"
    )
    return firmware, runtime


def test_all_supported_environments_share_and_validate_exact_platform(tmp_path):
    firmware, runtime = make_fixture(tmp_path)
    evidence = validate_firmware_project(firmware, runtime)
    assert evidence["status"] == "PASS"
    assert evidence["package_count"] == 1
    assert evidence["platforms"]["esp32dev"]["version"] == "6.12.0"
    assert set(evidence["environments"]) == {"esp32dev", "esp32dev_bootstrap", "esp32dev_ota"}


def test_unpinned_platform_fails_closed(tmp_path):
    firmware, runtime = make_fixture(tmp_path, platform="espressif32")
    with pytest.raises(ProductionPlatformIOClosureError, match="exact version"):
        validate_firmware_project(firmware, runtime)


def test_missing_transitive_platform_package_fails_closed(tmp_path):
    firmware, runtime = make_fixture(tmp_path)
    (runtime / "packages" / "toolchain" / "package.json").unlink()
    with pytest.raises(ProductionPlatformIOClosureError, match="Missing packaged PlatformIO dependency"):
        validate_firmware_project(firmware, runtime)


def test_platform_version_mismatch_fails_closed(tmp_path):
    firmware, runtime = make_fixture(tmp_path, platform_version="6.11.0")
    with pytest.raises(ProductionPlatformIOClosureError, match="found 0"):
        validate_firmware_project(firmware, runtime)


def test_conflicting_environment_dependency_versions_fail_closed(tmp_path):
    firmware, runtime = make_fixture(tmp_path)
    platform = runtime / "platforms" / "espressif32" / "platform.json"
    data = json.loads(platform.read_text(encoding="utf-8"))
    data["packages"]["toolchain"]["version"] = "2.0.0"
    platform.write_text(json.dumps(data), encoding="utf-8")
    # The validator sees the same platform for all inherited environments;
    # this fixture confirms that the package metadata mismatch is detected.
    with pytest.raises(ProductionPlatformIOClosureError, match="Missing packaged PlatformIO dependency"):
        validate_firmware_project(firmware, runtime)
