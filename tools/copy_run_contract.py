"""B2.6 copy-and-run contract for portable RoboStudio releases.

The contract is deliberately data-only and travels inside the production ZIP.
It tells both humans and automated validators which entry points and runtime
assets belong to the artifact, which state is external, and which host tools
must not be required.  All artifact paths are relative so the release remains
relocatable after copy/extract on another Windows machine.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping

SCHEMA = "antechkids.robostudio.copy-run-contract"
SCHEMA_VERSION = 1
CONTRACT_NAME = "copy-run-contract.json"
DELIVERY_MODEL = "copy-extract-run"
PRIMARY_LAUNCHER = "RoboStudio.cmd"
BUNDLED_PYTHON = "runtime/bin/python.exe"
BUNDLED_PLATFORMIO = "runtime/platformio"
COMPILER_ENTRY = "compiler/main.py"
FIRMWARE_ROOT = "firmware/robot-platform"
PHYSICAL_E2E_TOOL = "tools/clean_machine_physical_e2e.py"
STATE_ROOT_ENV = "ROBOSTUDIO_STATE_ROOT"
DEFAULT_WINDOWS_STATE = "%LOCALAPPDATA%/RoboStudio"


class CopyRunContractError(RuntimeError):
    """Raised when a production copy-and-run contract is invalid."""


def _safe_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CopyRunContractError(f"{label} must be a non-empty relative artifact path")
    normalized = value.strip().replace("\\", "/")
    if normalized.startswith("/") or (len(normalized) >= 2 and normalized[1] == ":"):
        raise CopyRunContractError(f"{label} must not contain an absolute path: {value}")
    path = PurePosixPath(normalized)
    if ".." in path.parts or "." in path.parts:
        raise CopyRunContractError(f"{label} must stay inside the extracted artifact: {value}")
    return path.as_posix()


def _load_version(root: Path) -> str:
    path = root / "VERSION"
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise CopyRunContractError(f"Copy-and-run VERSION is missing: {path}") from exc
    if not value or "\n" in value or "\r" in value:
        raise CopyRunContractError(f"Copy-and-run VERSION is invalid: {path}")
    return value


def build_contract(root: Path, *, application: str) -> dict[str, Any]:
    """Build the canonical contract from an assembled distribution root."""
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise CopyRunContractError(f"Production distribution not found: {root}")
    application = _safe_relative(application, "application")
    if PurePosixPath(application).name != application or not application.lower().endswith(".exe"):
        raise CopyRunContractError("Copy-and-run application must be a root-level Windows executable")
    if not (root / application).is_file():
        raise CopyRunContractError(f"Copy-and-run application is missing: {application}")

    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "delivery_model": DELIVERY_MODEL,
        "platform": "windows",
        "application": application,
        "application_version": _load_version(root),
        "entrypoints": {
            "primary": PRIMARY_LAUNCHER,
            "executable": application,
            "acceptance_probe": [application, "--acceptance-probe"],
            "physical_e2e_runner": [BUNDLED_PYTHON, "-I", "-B", PHYSICAL_E2E_TOOL],
        },
        "runtime": {
            "ownership": "artifact",
            "dependency_mode": "artifact-closed",
            "python": BUNDLED_PYTHON,
            "platformio": BUNDLED_PLATFORMIO,
            "compiler": COMPILER_ENTRY,
            "firmware": FIRMWARE_ROOT,
        },
        "state": {
            "ownership": "external-user-state",
            "inside_artifact_allowed": False,
            "windows_default": DEFAULT_WINDOWS_STATE,
            "override_environment": STATE_ROOT_ENV,
        },
        "host_requirements": {
            "source_checkout": False,
            "python": False,
            "node": False,
            "platformio": False,
            "compiler_toolchain": False,
            "developer_environment": False,
            "usb_driver_for_flash": True,
            "physical_robot_for_final_acceptance": True,
        },
        "relocation": {
            "absolute_build_paths_allowed": False,
            "current_working_directory_dependency": False,
            "copy_to_another_machine_supported": True,
        },
        "acceptance": {
            "physical_e2e_tool": PHYSICAL_E2E_TOOL,
            "final_pass_requires_operator_confirmation": True,
        },
    }


def _expect_false(mapping: Mapping[str, Any], keys: Iterable[str], label: str) -> None:
    for key in keys:
        if mapping.get(key) is not False:
            raise CopyRunContractError(f"{label}.{key} must be false")


def _require_member(member_names: set[str], relative: str, *, directory: bool = False) -> None:
    relative = _safe_relative(relative, "contract member")
    if directory:
        prefix = relative.rstrip("/") + "/"
        if not any(name.startswith(prefix) for name in member_names):
            raise CopyRunContractError(f"Copy-and-run ZIP payload is missing directory: {relative}")
    elif relative not in member_names:
        raise CopyRunContractError(f"Copy-and-run ZIP payload is missing file: {relative}")


def validate_payload(
    payload: Mapping[str, Any],
    *,
    expected_application: str | None = None,
    expected_version: str | None = None,
    member_names: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Validate contract semantics without trusting the build machine."""
    if payload.get("schema") != SCHEMA or payload.get("schema_version") != SCHEMA_VERSION:
        raise CopyRunContractError("Unsupported copy-and-run contract schema")
    if payload.get("delivery_model") != DELIVERY_MODEL or payload.get("platform") != "windows":
        raise CopyRunContractError("Copy-and-run contract must describe a Windows copy-extract-run release")

    application = _safe_relative(payload.get("application"), "application")
    if PurePosixPath(application).name != application or not application.lower().endswith(".exe"):
        raise CopyRunContractError("Copy-and-run application must be a root-level Windows executable")
    if expected_application is not None and application != expected_application:
        raise CopyRunContractError("Copy-and-run application disagrees with distribution/release manifest")
    version = payload.get("application_version")
    if not isinstance(version, str) or not version.strip():
        raise CopyRunContractError("Copy-and-run contract must declare application_version")
    if expected_version is not None and version != expected_version:
        raise CopyRunContractError("Copy-and-run application version disagrees with release manifest")

    entrypoints = payload.get("entrypoints")
    runtime = payload.get("runtime")
    state = payload.get("state")
    host = payload.get("host_requirements")
    relocation = payload.get("relocation")
    acceptance = payload.get("acceptance")
    for value, label in (
        (entrypoints, "entrypoints"), (runtime, "runtime"), (state, "state"),
        (host, "host_requirements"), (relocation, "relocation"), (acceptance, "acceptance"),
    ):
        if not isinstance(value, Mapping):
            raise CopyRunContractError(f"Copy-and-run contract {label} must be an object")

    assert isinstance(entrypoints, Mapping)
    assert isinstance(runtime, Mapping)
    assert isinstance(state, Mapping)
    assert isinstance(host, Mapping)
    assert isinstance(relocation, Mapping)
    assert isinstance(acceptance, Mapping)

    if _safe_relative(entrypoints.get("primary"), "entrypoints.primary") != PRIMARY_LAUNCHER:
        raise CopyRunContractError("Primary copy-and-run launcher must be RoboStudio.cmd")
    if _safe_relative(entrypoints.get("executable"), "entrypoints.executable") != application:
        raise CopyRunContractError("Executable entrypoint disagrees with application")
    if entrypoints.get("acceptance_probe") != [application, "--acceptance-probe"]:
        raise CopyRunContractError("Acceptance probe command is not canonical")
    if entrypoints.get("physical_e2e_runner") != [BUNDLED_PYTHON, "-I", "-B", PHYSICAL_E2E_TOOL]:
        raise CopyRunContractError("Physical E2E runner must use bundled isolated Python")

    expected_runtime = {
        "ownership": "artifact",
        "dependency_mode": "artifact-closed",
        "python": BUNDLED_PYTHON,
        "platformio": BUNDLED_PLATFORMIO,
        "compiler": COMPILER_ENTRY,
        "firmware": FIRMWARE_ROOT,
    }
    for key, expected in expected_runtime.items():
        if runtime.get(key) != expected:
            raise CopyRunContractError(f"runtime.{key} must be {expected!r}")
    for key in ("python", "platformio", "compiler", "firmware"):
        _safe_relative(runtime.get(key), f"runtime.{key}")

    if state.get("ownership") != "external-user-state" or state.get("inside_artifact_allowed") is not False:
        raise CopyRunContractError("Mutable state must be external to the extracted artifact")
    if state.get("windows_default") != DEFAULT_WINDOWS_STATE or state.get("override_environment") != STATE_ROOT_ENV:
        raise CopyRunContractError("Mutable-state location contract is not canonical")

    _expect_false(
        host,
        ("source_checkout", "python", "node", "platformio", "compiler_toolchain", "developer_environment"),
        "host_requirements",
    )
    if host.get("usb_driver_for_flash") is not True or host.get("physical_robot_for_final_acceptance") is not True:
        raise CopyRunContractError("Hardware-only host prerequisites are not declared correctly")
    _expect_false(relocation, ("absolute_build_paths_allowed", "current_working_directory_dependency"), "relocation")
    if relocation.get("copy_to_another_machine_supported") is not True:
        raise CopyRunContractError("Release must explicitly support relocation to another machine")
    if _safe_relative(acceptance.get("physical_e2e_tool"), "acceptance.physical_e2e_tool") != PHYSICAL_E2E_TOOL:
        raise CopyRunContractError("Physical E2E tool path is not canonical")
    if acceptance.get("final_pass_requires_operator_confirmation") is not True:
        raise CopyRunContractError("Physical acceptance must require explicit operator confirmation")

    if member_names is not None:
        names = {str(name).replace("\\", "/").lstrip("./") for name in member_names}
        for relative in (PRIMARY_LAUNCHER, application, BUNDLED_PYTHON, COMPILER_ENTRY, PHYSICAL_E2E_TOOL, "VERSION"):
            _require_member(names, relative)
        for relative in (BUNDLED_PLATFORMIO, FIRMWARE_ROOT):
            _require_member(names, relative, directory=True)

    return dict(payload)


def write_contract(root: Path, *, application: str) -> Path:
    root = Path(root).expanduser().resolve()
    payload = build_contract(root, application=application)
    path = root / CONTRACT_NAME
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def load_contract(path: Path) -> dict[str, Any]:
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CopyRunContractError(f"Invalid copy-and-run contract: {path}") from exc
    if not isinstance(payload, dict):
        raise CopyRunContractError("Copy-and-run contract root must be an object")
    return payload


def validate_distribution(root: Path, *, manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Validate the on-disk contract and every artifact-relative target it names."""
    root = Path(root).expanduser().resolve()
    payload = load_contract(root / CONTRACT_NAME)
    expected_application = str(manifest.get("application")) if manifest is not None else None
    expected_version = _load_version(root)
    validated = validate_payload(
        payload,
        expected_application=expected_application,
        expected_version=expected_version,
    )
    required_files = (PRIMARY_LAUNCHER, validated["application"], BUNDLED_PYTHON, COMPILER_ENTRY, PHYSICAL_E2E_TOOL)
    for relative in required_files:
        if not (root / relative).is_file():
            raise CopyRunContractError(f"Copy-and-run artifact file is missing: {relative}")
    for relative in (BUNDLED_PLATFORMIO, FIRMWARE_ROOT):
        if not (root / relative).is_dir():
            raise CopyRunContractError(f"Copy-and-run artifact directory is missing: {relative}")
    if not (root / BUNDLED_PLATFORMIO / "platforms").is_dir() or not (root / BUNDLED_PLATFORMIO / "packages").is_dir():
        raise CopyRunContractError("Bundled PlatformIO must contain platforms and packages")
    return validated
