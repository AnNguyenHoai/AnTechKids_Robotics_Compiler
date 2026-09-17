import json
from pathlib import Path

import pytest

from tools.production_platformio_closure import ProductionPlatformIOClosureError, validate_firmware_project


def make_fixture(
    root: Path,
    *,
    platform="espressif32@6.12.0",
    platform_version="6.12.0",
    package_version="1.2.3",
    package_requirement="~1.2.0",
    framework="arduino",
    include_framework=True,
    include_optional=True,
    transitive_dependency=False,
    custom_platform_package=None,
):
    firmware = root / "firmware"
    runtime = root / "runtime" / "platformio"
    (firmware / "main").mkdir(parents=True)
    (runtime / "platforms" / "espressif32").mkdir(parents=True)
    (runtime / "packages" / "toolchain").mkdir(parents=True)
    (runtime / "packages" / "uploader").mkdir(parents=True)
    if include_framework:
        (runtime / "packages" / "framework").mkdir(parents=True)
    if include_optional:
        (runtime / "packages" / "optional").mkdir(parents=True)
    if transitive_dependency:
        (runtime / "packages" / "transitive").mkdir(parents=True)

    platform_packages = ""
    if custom_platform_package:
        platform_packages = f"platform_packages =\n    {custom_platform_package}\n"

    firmware_ini = (
        "[platformio]\nsrc_dir = main\n\n"
        f"[env:esp32dev]\nplatform = {platform}\nboard = esp32dev\nframework = {framework}\n"
        f"{platform_packages}\n"
        "[env:esp32dev_bootstrap]\nextends = env:esp32dev\n\n"
        "[env:esp32dev_ota]\nextends = env:esp32dev\n"
    )
    (firmware / "platformio.ini").write_text(firmware_ini, encoding="utf-8")

    packages = {
        "toolchain": {"type": "toolchain", "version": package_version},
        "uploader": {"type": "uploader", "version": package_version},
        "framework": {"type": "framework", "version": package_version},
        "optional": {"type": "debugger", "version": package_version},
    }
    if transitive_dependency:
        packages["toolchain"]["dependencies"] = {"transitive": "~2.0.0"}
        packages["transitive"] = {"type": "tool", "version": "2.0.4"}

    for name, metadata in packages.items():
        if name == "framework" and not include_framework:
            continue
        if name == "optional" and not include_optional:
            continue
        package_dir = runtime / "packages" / name
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "package.json").write_text(json.dumps({"name": name, **metadata}), encoding="utf-8")

    platform_metadata = {
        "name": "espressif32",
        "version": platform_version,
        "frameworks": {"arduino": {"package": "framework", "script": "builder/frameworks/arduino.py"}},
        "packages": {
            "toolchain": {"type": "toolchain", "version": package_requirement},
            "uploader": {"type": "uploader", "version": package_requirement},
            "framework": {"type": "framework", "optional": True, "version": package_requirement},
            "optional": {"type": "debugger", "optional": True, "version": package_requirement},
        },
    }
    (runtime / "platforms" / "espressif32" / "platform.json").write_text(
        json.dumps(platform_metadata), encoding="utf-8"
    )
    return firmware, runtime


def test_all_supported_environments_share_and_validate_effective_platform_and_framework(tmp_path):
    firmware, runtime = make_fixture(tmp_path)
    evidence = validate_firmware_project(firmware, runtime)
    assert evidence["status"] == "PASS"
    assert evidence["package_count"] == 3
    assert evidence["platforms"]["esp32dev"]["version"] == "6.12.0"
    assert evidence["platforms"]["esp32dev"]["framework"] == "arduino"
    assert set(evidence["environments"]) == {"esp32dev", "esp32dev_bootstrap", "esp32dev_ota"}
    assert {item["name"] for item in evidence["packages"]} == {"toolchain", "uploader", "framework"}


def test_package_requirement_range_resolves_to_concrete_packaged_version(tmp_path):
    firmware, runtime = make_fixture(tmp_path, package_version="1.2.3", package_requirement="~1.2.0")
    evidence = validate_firmware_project(firmware, runtime)
    framework = next(item for item in evidence["packages"] if item["name"] == "framework")
    assert framework["version"] == "1.2.3"
    assert framework["requirements"] == "~1.2.0"


def test_optional_platform_packages_are_not_required(tmp_path):
    firmware, runtime = make_fixture(tmp_path, include_optional=False)
    evidence = validate_firmware_project(firmware, runtime)
    assert "optional" not in {item["name"] for item in evidence["packages"]}


def test_selected_framework_package_is_required_even_when_platform_marks_it_optional(tmp_path):
    firmware, runtime = make_fixture(tmp_path, include_framework=False)
    with pytest.raises(ProductionPlatformIOClosureError, match="framework"):
        validate_firmware_project(firmware, runtime)


def test_transitive_package_dependencies_are_required(tmp_path):
    firmware, runtime = make_fixture(tmp_path, transitive_dependency=True)
    evidence = validate_firmware_project(firmware, runtime)
    assert "transitive" in {item["name"] for item in evidence["packages"]}
    assert evidence["transitive_package_dependencies_validated"] is True


def test_custom_platform_package_is_part_of_closure(tmp_path):
    firmware, runtime = make_fixture(tmp_path, custom_platform_package="custom-tool@~3.1.0")
    custom_dir = runtime / "packages" / "custom-tool"
    custom_dir.mkdir(parents=True)
    (custom_dir / "package.json").write_text(
        json.dumps({"name": "custom-tool", "version": "3.1.4"}), encoding="utf-8"
    )
    evidence = validate_firmware_project(firmware, runtime)
    assert "custom-tool" in {item["name"] for item in evidence["packages"]}


def test_unpinned_platform_fails_closed(tmp_path):
    firmware, runtime = make_fixture(tmp_path, platform="espressif32")
    with pytest.raises(ProductionPlatformIOClosureError, match="exact version"):
        validate_firmware_project(firmware, runtime)


def test_missing_required_platform_package_fails_closed(tmp_path):
    firmware, runtime = make_fixture(tmp_path)
    (runtime / "packages" / "uploader" / "package.json").unlink()
    with pytest.raises(ProductionPlatformIOClosureError, match="uploader"):
        validate_firmware_project(firmware, runtime)


def test_platform_version_mismatch_fails_closed(tmp_path):
    firmware, runtime = make_fixture(tmp_path, platform_version="6.11.0")
    with pytest.raises(ProductionPlatformIOClosureError, match="found 0"):
        validate_firmware_project(firmware, runtime)


def test_package_requirement_not_satisfied_fails_closed(tmp_path):
    firmware, runtime = make_fixture(tmp_path, package_version="1.0.0", package_requirement="~2.0.0")
    with pytest.raises(ProductionPlatformIOClosureError, match="dependency satisfying"):
        validate_firmware_project(firmware, runtime)


def test_unsupported_remote_custom_package_source_fails_closed(tmp_path):
    firmware, runtime = make_fixture(
        tmp_path,
        custom_platform_package="custom-tool@https://example.invalid/tool.zip",
    )
    with pytest.raises(ProductionPlatformIOClosureError, match="remote/local custom package source"):
        validate_firmware_project(firmware, runtime)


def test_not_equal_version_constraints_are_supported(tmp_path):
    firmware, runtime = make_fixture(
        tmp_path,
        package_version="1.2.3",
        package_requirement=">=1.0.0,!=1.2.0,<2.0.0",
    )
    evidence = validate_firmware_project(firmware, runtime)
    assert evidence["package_count"] == 3
