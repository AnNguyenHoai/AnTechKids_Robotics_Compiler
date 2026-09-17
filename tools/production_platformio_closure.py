"""RSD-28 production PlatformIO dependency-closure validation.

The production artifact owns the PlatformIO runtime. This module proves that
all PlatformIO dependencies declared by the packaged firmware environments are
present in that runtime and have concrete versions. It deliberately does not
resolve packages from the host machine or invoke PlatformIO during validation.
"""
from __future__ import annotations

import configparser
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "antechkids.robostudio.production-platformio-dependency-closure"
SCHEMA_VERSION = 1
ENVIRONMENTS = ("esp32dev", "esp32dev_bootstrap", "esp32dev_ota")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}(?:[-+][0-9A-Za-z.-]+)?$")


class ProductionPlatformIOClosureError(RuntimeError):
    """Raised when the packaged PlatformIO dependency closure is incomplete."""


def _read_ini(path: Path) -> configparser.ConfigParser:
    if not path.is_file():
        raise ProductionPlatformIOClosureError(f"Firmware platformio.ini is missing: {path}")
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(path, encoding="utf-8")
    except (OSError, configparser.Error) as exc:
        raise ProductionPlatformIOClosureError(f"Invalid platformio.ini: {path}") from exc
    return parser


def _exact_version(spec: str, label: str) -> str:
    value = str(spec).strip()
    if "@" not in value:
        raise ProductionPlatformIOClosureError(
            f"{label} must pin an exact version with '@', got: {value!r}"
        )
    _, version = value.rsplit("@", 1)
    version = version.strip()
    if not _VERSION_RE.fullmatch(version) or any(ch in version for ch in "^~<>=* "):
        raise ProductionPlatformIOClosureError(f"{label} must use an exact version, got: {value!r}")
    return version


def _json(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProductionPlatformIOClosureError(f"Invalid {label}: {path}") from exc
    if not isinstance(data, dict):
        raise ProductionPlatformIOClosureError(f"Invalid {label}: expected JSON object: {path}")
    return data


def _platform_metadata(runtime_root: Path, platform_name: str, expected_version: str) -> tuple[Path, dict[str, Any]]:
    candidates = sorted((runtime_root / "platforms").glob("*/platform.json"))
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in candidates:
        data = _json(path, "PlatformIO platform metadata")
        name = str(data.get("name", "")).strip()
        version = str(data.get("version", "")).strip()
        if name == platform_name and version == expected_version:
            matches.append((path, data))
    if len(matches) != 1:
        raise ProductionPlatformIOClosureError(
            f"Expected exactly one packaged platform {platform_name}@{expected_version}, found {len(matches)}"
        )
    return matches[0]


def _package_metadata(runtime_root: Path) -> dict[tuple[str, str], Path]:
    result: dict[tuple[str, str], Path] = {}
    for path in sorted((runtime_root / "packages").glob("*/package.json")):
        data = _json(path, "PlatformIO package metadata")
        name = str(data.get("name", "")).strip()
        version = str(data.get("version", "")).strip()
        if not name or not version:
            raise ProductionPlatformIOClosureError(f"PlatformIO package metadata lacks name/version: {path}")
        key = (name, version)
        if key in result:
            raise ProductionPlatformIOClosureError(f"Duplicate packaged PlatformIO package: {name}@{version}")
        result[key] = path
    return result


def _platform_packages(metadata: dict[str, Any]) -> dict[str, str]:
    packages = metadata.get("packages", {})
    if not isinstance(packages, dict):
        raise ProductionPlatformIOClosureError("Platform metadata 'packages' must be an object")
    required: dict[str, str] = {}
    for name, value in packages.items():
        if not isinstance(value, dict):
            raise ProductionPlatformIOClosureError(f"Invalid package declaration for {name!r}")
        if "version" not in value:
            raise ProductionPlatformIOClosureError(f"Platform package {name!r} has no version requirement")
        required[str(name)] = _exact_version(str(value["version"]), f"Platform package {name}")
    return required


def _declared_environments(parser: configparser.ConfigParser) -> dict[str, str]:
    result: dict[str, str] = {}
    for environment in ENVIRONMENTS:
        section = f"env:{environment}"
        if not parser.has_section(section):
            raise ProductionPlatformIOClosureError(f"Firmware project is missing required environment: {environment}")
        platform = parser.get(section, "platform", fallback="").strip()
        if not platform and environment != "esp32dev":
            platform = parser.get("env:esp32dev", "platform", fallback="").strip()
        result[environment] = platform
    return result


def validate_firmware_project(firmware_root: Path, runtime_root: Path) -> dict[str, Any]:
    firmware_root = Path(firmware_root).expanduser().resolve()
    runtime_root = Path(runtime_root).expanduser().resolve()
    parser = _read_ini(firmware_root / "platformio.ini")
    if not (runtime_root / "platforms").is_dir() or not (runtime_root / "packages").is_dir():
        raise ProductionPlatformIOClosureError("PlatformIO runtime must contain platforms/ and packages/")

    declared = _declared_environments(parser)
    platform_records: dict[str, Any] = {}
    all_packages: dict[str, str] = {}
    for environment, spec in declared.items():
        if environment != "esp32dev" and not spec:
            spec = declared["esp32dev"]
        version = _exact_version(spec, f"PlatformIO platform for {environment}")
        platform_name = spec.rsplit("@", 1)[0].strip()
        if not platform_name:
            raise ProductionPlatformIOClosureError(f"Invalid PlatformIO platform specification: {spec!r}")
        path, metadata = _platform_metadata(runtime_root, platform_name, version)
        platform_records[environment] = {
            "name": platform_name,
            "version": version,
            "metadata": path.relative_to(runtime_root).as_posix(),
        }
        for package, package_version in _platform_packages(metadata).items():
            previous = all_packages.get(package)
            if previous is not None and previous != package_version:
                raise ProductionPlatformIOClosureError(
                    f"PlatformIO environments require conflicting versions for {package}: {previous} vs {package_version}"
                )
            all_packages[package] = package_version

    packaged_packages = _package_metadata(runtime_root)
    package_records: list[dict[str, str]] = []
    for name, version in sorted(all_packages.items()):
        path = packaged_packages.get((name, version))
        if path is None:
            raise ProductionPlatformIOClosureError(f"Missing packaged PlatformIO dependency: {name}@{version}")
        package_records.append({"name": name, "version": version, "metadata": path.relative_to(runtime_root).as_posix()})

    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "environments": list(ENVIRONMENTS),
        "platforms": platform_records,
        "packages": package_records,
        "package_count": len(package_records),
        "host_resolution": False,
        "exact_versions_required": True,
    }


def validate_distribution(distribution_root: Path) -> dict[str, Any]:
    root = Path(distribution_root).expanduser().resolve()
    return validate_firmware_project(root / "firmware" / "robot-platform", root / "runtime" / "platformio")


def write_evidence(distribution_root: Path, output: Path | None = None) -> Path:
    root = Path(distribution_root).expanduser().resolve()
    evidence = validate_distribution(root)
    path = Path(output) if output is not None else root / "production-platformio-dependency-closure.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return path
