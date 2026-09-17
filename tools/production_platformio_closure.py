"""RSD-29 production PlatformIO dependency-closure validation.

The production artifact owns the PlatformIO runtime. This module validates the
*effective* dependencies selected by each supported PlatformIO environment,
including selected frameworks, custom platform packages, and transitive package
dependencies. It never invokes PlatformIO or consults host state.
"""
from __future__ import annotations

import configparser
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "antechkids.robostudio.production-platformio-dependency-closure"
SCHEMA_VERSION = 2
ENVIRONMENTS = ("esp32dev", "esp32dev_bootstrap", "esp32dev_ota")
_VERSION_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-+][0-9A-Za-z.-]+)?$")
_PACKAGE_SPEC_RE = re.compile(r"^(?:(?:[^@/\s]+/)?([^@\s]+))@(.+)$")


class ProductionPlatformIOClosureError(RuntimeError):
    """Raised when the packaged PlatformIO dependency closure is incomplete."""


def _read_ini(path: Path) -> configparser.ConfigParser:
    if not path.is_file():
        raise ProductionPlatformIOClosureError(f"Firmware platformio.ini is missing: {path}")
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        parser.read(path, encoding="utf-8")
    except (OSError, configparser.Error) as exc:
        raise ProductionPlatformIOClosureError(f"Invalid platformio.ini: {path}") from exc
    return parser


def _parse_version(value: str, label: str) -> tuple[int, int, int]:
    match = _VERSION_RE.fullmatch(str(value).strip())
    if not match:
        raise ProductionPlatformIOClosureError(f"{label} has an invalid version: {value!r}")
    return tuple(int(part or 0) for part in match.groups())


def _exact_version(spec: str, label: str) -> str:
    value = str(spec).strip()
    if "@" not in value:
        raise ProductionPlatformIOClosureError(
            f"{label} must pin an exact version with '@', got: {value!r}"
        )
    _, version = value.rsplit("@", 1)
    version = version.strip()
    _parse_version(version, label)
    if any(ch in version for ch in "^~<>=*! ,"):
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


def _platform_metadata(
    runtime_root: Path, platform_name: str, expected_version: str
) -> tuple[Path, dict[str, Any]]:
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


def _package_metadata(runtime_root: Path) -> dict[str, list[tuple[str, Path, dict[str, Any]]]]:
    result: dict[str, list[tuple[str, Path, dict[str, Any]]]] = {}
    package_root = runtime_root / "packages"
    for path in sorted(package_root.glob("*/package.json")):
        data = _json(path, "PlatformIO package metadata")
        name = str(data.get("name", "")).strip()
        version = str(data.get("version", "")).strip()
        if not name or not version:
            raise ProductionPlatformIOClosureError(
                f"PlatformIO package metadata lacks name/version: {path}"
            )
        _parse_version(version, f"PlatformIO package {name}")
        result.setdefault(name, []).append((version, path, data))
    return result


def _version_satisfies(version: str, requirement: str, label: str) -> bool:
    actual = _parse_version(version, label)
    requirement = str(requirement).strip()
    if not requirement:
        raise ProductionPlatformIOClosureError(f"{label} has an empty version requirement")

    if requirement.startswith("~"):
        base = _parse_version(requirement[1:], label)
        return actual >= base and actual < (base[0], base[1] + 1, 0)

    if requirement.startswith("^"):
        base = _parse_version(requirement[1:], label)
        if base[0] > 0:
            upper = (base[0] + 1, 0, 0)
        elif base[1] > 0:
            upper = (0, base[1] + 1, 0)
        else:
            upper = (0, 0, base[2] + 1)
        return actual >= base and actual < upper

    if "," in requirement:
        return all(
            _version_satisfies(version, part.strip(), label)
            for part in requirement.split(",")
            if part.strip()
        )

    match = re.fullmatch(r"(>=|<=|!=|>|<)\s*(.+)", requirement)
    if match:
        base = _parse_version(match.group(2), label)
        op = match.group(1)
        return {
            ">=": actual >= base,
            "<=": actual <= base,
            "!=": actual != base,
            ">": actual > base,
            "<": actual < base,
        }[op]

    return actual == _parse_version(requirement, label)


def _platform_packages(metadata: dict[str, Any], framework: str) -> dict[str, str]:
    packages = metadata.get("packages", {})
    if not isinstance(packages, dict):
        raise ProductionPlatformIOClosureError("Platform metadata 'packages' must be an object")

    required: dict[str, str] = {}
    for name, value in packages.items():
        if not isinstance(value, dict) or "version" not in value:
            raise ProductionPlatformIOClosureError(
                f"Platform package {name!r} has no version requirement"
            )
        # PlatformIO marks framework packages and many board-specific tools as
        # optional in the platform manifest. They become required when the
        # project selects that framework; other optional packages stay optional.
        if not bool(value.get("optional", False)):
            required[str(name)] = str(value["version"]).strip()

    frameworks = metadata.get("frameworks", {})
    if not isinstance(frameworks, dict):
        raise ProductionPlatformIOClosureError("Platform metadata 'frameworks' must be an object")
    framework_spec = frameworks.get(framework)
    if not isinstance(framework_spec, dict):
        raise ProductionPlatformIOClosureError(
            f"Selected framework {framework!r} is not declared by the platform"
        )
    framework_package = str(framework_spec.get("package", "")).strip()
    if not framework_package:
        raise ProductionPlatformIOClosureError(
            f"Selected framework {framework!r} does not declare a package"
        )
    package_metadata = packages.get(framework_package)
    if not isinstance(package_metadata, dict) or "version" not in package_metadata:
        raise ProductionPlatformIOClosureError(
            f"Selected framework package {framework_package!r} is missing from platform packages"
        )
    required[framework_package] = str(package_metadata["version"]).strip()
    return required


def _section_value(
    parser: configparser.ConfigParser,
    section: str,
    key: str,
    seen: set[str] | None = None,
) -> str:
    if seen is None:
        seen = set()
    if section in seen:
        raise ProductionPlatformIOClosureError(f"Circular PlatformIO extends chain at {section}")
    seen.add(section)
    if parser.has_option(section, key):
        return parser.get(section, key).strip()
    extends = parser.get(section, "extends", fallback="").strip()
    if not extends:
        return ""
    for parent in (item.strip() for item in extends.split(",") if item.strip()):
        parent_section = parent if parent.startswith("env:") else f"env:{parent}"
        if parser.has_section(parent_section):
            value = _section_value(parser, parent_section, key, set(seen))
            if value:
                return value
    return ""


def _declared_environments(parser: configparser.ConfigParser) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for environment in ENVIRONMENTS:
        section = f"env:{environment}"
        if not parser.has_section(section):
            raise ProductionPlatformIOClosureError(
                f"Firmware project is missing required environment: {environment}"
            )
        platform = _section_value(parser, section, "platform")
        framework = _section_value(parser, section, "framework")
        platform_packages = _section_value(parser, section, "platform_packages")
        if not platform:
            raise ProductionPlatformIOClosureError(
                f"Firmware environment {environment} has no effective platform"
            )
        if not framework:
            raise ProductionPlatformIOClosureError(
                f"Firmware environment {environment} has no effective framework"
            )
        result[environment] = {
            "platform": platform,
            "framework": framework,
            "platform_packages": platform_packages,
        }
    return result


def _platform_package_overrides(value: str) -> dict[str, str]:
    if not value:
        return {}
    result: dict[str, str] = {}
    for raw_line in value.splitlines():
        spec = raw_line.strip()
        if not spec or spec.startswith(";"):
            continue
        if "=" in spec and not spec.startswith(("http://", "https://", "git+")):
            name, spec = spec.split("=", 1)
            name = name.strip()
            spec = spec.strip()
        else:
            name = ""
        if "@" in spec:
            inferred_name, requirement = spec.rsplit("@", 1)
            if not name:
                name = inferred_name.rsplit("/", 1)[-1].strip()
            spec = requirement.strip()
        else:
            if not name:
                raise ProductionPlatformIOClosureError(
                    f"PlatformIO custom package specification is not deterministic: {raw_line!r}"
                )
        if not name or not spec:
            raise ProductionPlatformIOClosureError(
                f"Invalid PlatformIO custom package specification: {raw_line!r}"
            )
        if spec.startswith(("http://", "https://", "git+", "git://", "file://", "symlink://")):
            raise ProductionPlatformIOClosureError(
                f"Production closure does not accept remote/local custom package source: {raw_line!r}"
            )
        result[name] = spec
    return result


def _parse_dependency_spec(name: str, value: Any) -> tuple[str, str]:
    if not isinstance(value, str) or not value.strip():
        raise ProductionPlatformIOClosureError(
            f"Package {name!r} has an invalid dependency specification: {value!r}"
        )
    spec = value.strip()
    if spec.startswith(("http://", "https://", "git+", "git://", "file://", "symlink://")):
        raise ProductionPlatformIOClosureError(
            f"Package {name!r} uses a non-reproducible dependency source: {spec!r}"
        )
    if "@" in spec:
        package_name, requirement = spec.rsplit("@", 1)
        package_name = package_name.rsplit("/", 1)[-1].strip()
        if not package_name or not requirement.strip():
            raise ProductionPlatformIOClosureError(
                f"Package {name!r} has invalid dependency specification: {spec!r}"
            )
        return package_name, requirement.strip()
    return name, spec


def validate_firmware_project(firmware_root: Path, runtime_root: Path) -> dict[str, Any]:
    firmware_root = Path(firmware_root).expanduser().resolve()
    runtime_root = Path(runtime_root).expanduser().resolve()
    parser = _read_ini(firmware_root / "platformio.ini")
    if not (runtime_root / "platforms").is_dir() or not (runtime_root / "packages").is_dir():
        raise ProductionPlatformIOClosureError("PlatformIO runtime must contain platforms/ and packages/")

    environments = _declared_environments(parser)
    packaged_packages = _package_metadata(runtime_root)
    platform_records: dict[str, Any] = {}
    requirements: dict[str, list[str]] = {}
    dependency_sources: dict[str, set[str]] = {}

    for environment, config in environments.items():
        spec = config["platform"]
        version = _exact_version(spec, f"PlatformIO platform for {environment}")
        platform_name = spec.rsplit("@", 1)[0].strip().rsplit("/", 1)[-1]
        if not platform_name:
            raise ProductionPlatformIOClosureError(f"Invalid PlatformIO platform specification: {spec!r}")
        path, metadata = _platform_metadata(runtime_root, platform_name, version)
        platform_records[environment] = {
            "name": platform_name,
            "version": version,
            "framework": config["framework"],
            "metadata": path.relative_to(runtime_root).as_posix(),
        }
        for package, requirement in _platform_packages(metadata, config["framework"]).items():
            requirements.setdefault(package, []).append(requirement)
            dependency_sources.setdefault(package, set()).add(f"platform:{environment}")
        for package, requirement in _platform_package_overrides(config["platform_packages"]).items():
            requirements[package] = [requirement]
            dependency_sources.setdefault(package, set()).add(f"platform_packages:{environment}")

    resolved: dict[str, tuple[str, Path, dict[str, Any]]] = {}
    pending = sorted(requirements)
    processed: set[str] = set()
    while pending:
        name = pending.pop(0)
        if name in processed:
            continue
        processed.add(name)
        package_candidates = packaged_packages.get(name, [])
        package_requirements = requirements.get(name, [])
        matches = [
            candidate
            for candidate in package_candidates
            if all(
                _version_satisfies(candidate[0], req, f"Platform package {name}")
                for req in package_requirements
            )
        ]
        if len(matches) != 1:
            detail = ", ".join(sorted(set(package_requirements)))
            raise ProductionPlatformIOClosureError(
                f"Expected exactly one packaged PlatformIO dependency satisfying {name} requirements [{detail}], found {len(matches)}"
            )
        version, path, data = matches[0]
        resolved[name] = (version, path, data)
        dependencies = data.get("dependencies", {})
        if dependencies is None:
            dependencies = {}
        if not isinstance(dependencies, dict):
            raise ProductionPlatformIOClosureError(
                f"PlatformIO package {name}@{version} has invalid dependencies metadata"
            )
        for dependency_name, dependency_spec in dependencies.items():
            normalized_name, requirement = _parse_dependency_spec(name, dependency_spec)
            requirements.setdefault(normalized_name, []).append(requirement)
            dependency_sources.setdefault(normalized_name, set()).add(f"package:{name}@{version}")
            if normalized_name not in processed and normalized_name not in pending:
                pending.append(normalized_name)
        pending.sort()

    package_records = []
    for name in sorted(resolved):
        version, path, _ = resolved[name]
        package_records.append(
            {
                "name": name,
                "version": version,
                "requirements": ", ".join(sorted(set(requirements[name]))),
                "metadata": path.relative_to(runtime_root).as_posix(),
                "required_by": sorted(dependency_sources.get(name, set())),
            }
        )

    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "environments": list(ENVIRONMENTS),
        "platforms": platform_records,
        "packages": package_records,
        "package_count": len(package_records),
        "host_resolution": False,
        "exact_platform_versions_required": True,
        "package_versions_are_concrete": True,
        "transitive_package_dependencies_validated": True,
        "optional_platform_packages_excluded_unless_selected": True,
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
