#!/usr/bin/env python3
"""B2.5 real clean-machine end-to-end acceptance runner.

The automated phase proves the portable software path from an extracted
production artifact through RoboStudio startup, explicit USB/COM qualification,
compile and physical USB upload.  It deliberately cannot claim that a robot
actually behaved correctly or that an operator exercised the real GUI flow.
Those facts require an explicit second-phase operator confirmation on the clean
Windows machine.

Final PASS therefore requires both:

1. automated artifact-owned launch/qualification/deploy + immutable release, and
2. operator confirmation of clean-machine setup, real GUI flow and robot result.

The module is packaged inside the release and is runnable with the bundled
Python.  It never searches host PATH for Python/PlatformIO/compiler tooling.
"""
from __future__ import annotations

import sys

# Direct execution from the extracted artifact must not create __pycache__ in
# the immutable release.  ``-B`` is also used by the documented command, but
# this protects imports even when an operator omits that flag.
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Callable, Mapping

_APPLICATION_ROOT = Path(__file__).resolve().parent.parent
if str(_APPLICATION_ROOT) not in sys.path:
    sys.path.insert(0, str(_APPLICATION_ROOT))

from tools import dependency_closure, deployment_runtime, runtime_paths, target_machine_qualification

SCHEMA = "antechkids.robostudio.clean-machine-physical-e2e"
SCHEMA_VERSION = 1
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_PENDING = "PENDING_OPERATOR_CONFIRMATION"
PROJECT_NAME = "b2-5-clean-machine-e2e"


class CleanMachineE2EError(RuntimeError):
    """Raised when B2.5 acceptance cannot produce trustworthy evidence."""


def _canonical(path: Path | str) -> Path:
    return Path(os.path.normcase(os.path.realpath(os.path.abspath(os.path.expanduser(str(path))))))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _require_outside(path: Path, root: Path, label: str) -> Path:
    candidate = _canonical(path)
    artifact_root = _canonical(root)
    if candidate == artifact_root or _is_relative_to(candidate, artifact_root):
        raise CleanMachineE2EError(f"{label} must be outside the immutable production artifact")
    return candidate


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def release_tree_digest(root: Path) -> tuple[str, int]:
    """Fingerprint every release file without depending on filesystem mtimes."""
    root = _canonical(root)
    digest = hashlib.sha256()
    count = 0
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().casefold()):
        if path.is_symlink():
            raise CleanMachineE2EError(
                f"Production artifact contains unsupported symlink: {path.relative_to(root).as_posix()}"
            )
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        content_hash = _sha256_file(path)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(path.stat().st_size).encode("ascii"))
        digest.update(b"\0")
        digest.update(content_hash.encode("ascii"))
        digest.update(b"\n")
        count += 1
    return digest.hexdigest(), count


def _load_distribution_manifest(root: Path) -> dict[str, object]:
    path = root / "distribution-manifest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CleanMachineE2EError(f"Invalid production distribution manifest: {path}") from exc
    if payload.get("production_boundary") is not True:
        raise CleanMachineE2EError("B2.5 requires a production-boundary distribution")
    if payload.get("deployment_tools") != "tools":
        raise CleanMachineE2EError("Production distribution does not declare packaged deployment tools")
    return payload


def validate_clean_machine_context(
    *,
    application_root: Path | None = None,
    python_executable: Path | None = None,
    source: Path,
    evidence: Path,
) -> dict[str, object]:
    """Validate artifact ownership and external mutable/input paths."""
    root = _canonical(application_root or _APPLICATION_ROOT)
    if not root.is_dir():
        raise CleanMachineE2EError(f"Production artifact root is missing: {root}")
    manifest = _load_distribution_manifest(root)
    application = str(manifest.get("application", "")).strip()
    if not application or Path(application).name != application or Path(application).suffix.lower() != ".exe":
        raise CleanMachineE2EError("Distribution manifest does not identify a valid RoboStudio executable")

    required_files = {
        "RoboStudio executable": root / application,
        "bundled Python": root / "runtime" / "bin" / "python.exe",
        "compiler contract": root / "compiler" / "robostudio_bridge.py",
        "USB deploy runtime": root / "tools" / "deploy_robot.py",
        "B2.5 acceptance runtime": root / "tools" / "clean_machine_physical_e2e.py",
        "firmware project": root / "firmware" / "robot-platform" / "platformio.ini",
    }
    missing = [f"{label}: {path}" for label, path in required_files.items() if not path.is_file()]
    if missing:
        raise CleanMachineE2EError("Production artifact is incomplete: " + "; ".join(missing))

    expected_python = _canonical(required_files["bundled Python"])
    actual_python = _canonical(python_executable or Path(sys.executable))
    if actual_python != expected_python:
        raise CleanMachineE2EError(
            "B2.5 must run with runtime/bin/python.exe from the extracted artifact; host Python is not accepted"
        )

    source = _canonical(source)
    if not source.is_file() or source.suffix.lower() != ".py":
        raise CleanMachineE2EError("B2.5 source must be an existing external .py file")
    _require_outside(source, root, "Student source")
    evidence = _require_outside(evidence, root, "Acceptance evidence")

    return {
        "root": root,
        "application": application,
        "application_path": required_files["RoboStudio executable"],
        "python_path": expected_python,
        "deploy_path": required_files["USB deploy runtime"],
        "source": source,
        "evidence": evidence,
    }


def build_acceptance_environment(
    root: Path,
    *,
    base_env: Mapping[str, str] | None = None,
) -> tuple[dict[str, str], dependency_closure.DependencyClosureReport]:
    """Create an artifact-closed environment even when invoked directly by Python."""
    inherited = dict(os.environ if base_env is None else base_env)
    inherited[runtime_paths.APPLICATION_HOME_ENV] = str(_canonical(root))
    inherited[runtime_paths.RUNTIME_MODE_ENV] = "packaged"
    inherited[runtime_paths.DEPENDENCY_MODE_ENV] = "artifact-closed"
    try:
        return dependency_closure.build_closed_environment(root, inherited)
    except dependency_closure.DependencyClosureError as exc:
        raise CleanMachineE2EError(f"Unable to seal B2.5 execution environment: {exc}") from exc


def _qualification_summary(report: object) -> dict[str, object]:
    if isinstance(report, Mapping):
        payload = dict(report)
    else:
        payload = target_machine_qualification.to_dict(report)  # type: ignore[arg-type]
    preflight = payload.get("flash_preflight")
    selected = ""
    driver_visible = False
    if isinstance(preflight, Mapping):
        selected_data = preflight.get("selected_port")
        if isinstance(selected_data, Mapping):
            selected = str(selected_data.get("port", ""))
        driver_visible = preflight.get("driver_visibility_proven") is True
    return {
        "scope": str(payload.get("scope", "flash")),
        "passed": payload.get("passed") is True,
        "automated_checks_passed": payload.get("automated_checks_passed") is True,
        "selected_port": selected,
        "driver_visibility_proven": driver_visible,
    }


def _default_qualification_runner(port: str, env: Mapping[str, str]) -> object:
    return target_machine_qualification.require_target_machine(
        scope="flash",
        env=env,
        serial_port=port,
    )


def _default_process_runner(command, *, cwd, env, timeout):
    return deployment_runtime.run_process(command, cwd=cwd, env=env, timeout=timeout)


def _process_result_payload(result: object, *, expected_marker: str | None = None) -> dict[str, object]:
    returncode = int(getattr(result, "returncode", 1))
    output = str(getattr(result, "output", ""))
    return {
        "status": STATUS_PASS if returncode == 0 else STATUS_FAIL,
        "returncode": returncode,
        "expected_marker_seen": True if expected_marker is None else expected_marker in output,
    }


def _automated_stage_passed(payload: Mapping[str, object]) -> bool:
    automated = payload.get("automated")
    integrity = payload.get("release_integrity")
    contract = payload.get("clean_machine_contract")
    if not isinstance(automated, Mapping) or not isinstance(integrity, Mapping) or not isinstance(contract, Mapping):
        return False
    launch = automated.get("robostudio_launch")
    qualification = automated.get("target_qualification")
    deployment = automated.get("deployment")
    return (
        isinstance(launch, Mapping)
        and launch.get("status") == STATUS_PASS
        and isinstance(qualification, Mapping)
        and qualification.get("passed") is True
        and qualification.get("driver_visibility_proven") is True
        and isinstance(deployment, Mapping)
        and deployment.get("status") == STATUS_PASS
        and deployment.get("expected_marker_seen") is True
        and integrity.get("unchanged") is True
        and contract.get("bundled_python_verified") is True
        and contract.get("host_path_inherited") is False
        and contract.get("working_directory_external") is True
    )


def _status_from_confirmation(payload: Mapping[str, object]) -> str:
    if not _automated_stage_passed(payload):
        return STATUS_FAIL
    confirmation = payload.get("operator_confirmation")
    if not isinstance(confirmation, Mapping):
        return STATUS_PENDING
    values = [
        str(confirmation.get("clean_machine", "pending")),
        str(confirmation.get("ui_flow", "pending")),
        str(confirmation.get("robot_execution", "pending")),
    ]
    if any(value == "fail" for value in values):
        return STATUS_FAIL
    if all(value == "pass" for value in values) and str(confirmation.get("note", "")).strip():
        return STATUS_PASS
    return STATUS_PENDING


def validate_evidence_payload(payload: Mapping[str, object]) -> dict[str, object]:
    """Validate schema and fail-closed status semantics."""
    if payload.get("schema") != SCHEMA or payload.get("schema_version") != SCHEMA_VERSION:
        raise CleanMachineE2EError("Unsupported B2.5 clean-machine evidence schema")
    expected = _status_from_confirmation(payload)
    actual = str(payload.get("status", ""))
    if actual != expected:
        raise CleanMachineE2EError(
            f"B2.5 evidence status is inconsistent: expected {expected}, got {actual or 'missing'}"
        )
    return dict(payload)


def write_evidence(payload: Mapping[str, object], destination: Path, root: Path) -> Path:
    path = _require_outside(destination, root, "Acceptance evidence")
    path.parent.mkdir(parents=True, exist_ok=True)
    validated = validate_evidence_payload(payload)
    path.write_text(json.dumps(validated, indent=2) + "\n", encoding="utf-8")
    return path


def run_clean_machine_e2e(
    *,
    port: str,
    source: Path,
    evidence: Path,
    timeout: float = deployment_runtime.DEFAULT_PROCESS_TIMEOUT_SECONDS,
    application_root: Path | None = None,
    python_executable: Path | None = None,
    base_env: Mapping[str, str] | None = None,
    qualification_runner: Callable[[str, Mapping[str, str]], object] | None = None,
    process_runner: Callable[..., object] | None = None,
) -> dict[str, object]:
    """Run the automated half of B2.5 and leave physical truth pending."""
    selected_port = (port or "").strip()
    if not selected_port:
        raise CleanMachineE2EError("B2.5 requires an explicit USB/COM port")
    if timeout <= 0:
        raise CleanMachineE2EError("B2.5 timeout must be greater than zero")

    context = validate_clean_machine_context(
        application_root=application_root,
        python_executable=python_executable,
        source=source,
        evidence=evidence,
    )
    root = context["root"]
    assert isinstance(root, Path)
    closed_env, closure = build_acceptance_environment(root, base_env=base_env)
    state_root = runtime_paths.prepare_user_data_root(
        base_env=closed_env,
        application_root_override=root,
        enforce_external=True,
    )
    work_root = state_root / "acceptance" / PROJECT_NAME
    work_root.mkdir(parents=True, exist_ok=True)
    _require_outside(work_root, root, "Acceptance working directory")

    before_hash, before_count = release_tree_digest(root)
    runner = process_runner or _default_process_runner
    qualifier = qualification_runner or _default_qualification_runner

    launch_payload: dict[str, object] = {"status": STATUS_FAIL, "returncode": None}
    qualification_payload: dict[str, object] = {
        "scope": "flash",
        "passed": False,
        "automated_checks_passed": False,
        "selected_port": "",
        "driver_visibility_proven": False,
    }
    deployment_payload: dict[str, object] = {
        "status": STATUS_FAIL,
        "returncode": None,
        "expected_marker_seen": False,
    }
    failure = ""

    try:
        launch_result = runner(
            [str(context["application_path"]), "--acceptance-probe"],
            cwd=work_root,
            env=closed_env,
            timeout=min(timeout, 60.0),
        )
        launch_payload = _process_result_payload(launch_result)
        if launch_payload["status"] != STATUS_PASS:
            raise CleanMachineE2EError("RoboStudio acceptance probe did not start successfully")

        qualification_payload = _qualification_summary(qualifier(selected_port, closed_env))
        if not qualification_payload["passed"]:
            raise CleanMachineE2EError("Target machine is not qualified for USB flash")
        if not qualification_payload["driver_visibility_proven"]:
            raise CleanMachineE2EError("USB/UART driver visibility was not proven")
        if str(qualification_payload.get("selected_port", "")).casefold() != selected_port.casefold():
            raise CleanMachineE2EError("Target qualification did not confirm the explicitly selected port")

        deploy_command = [
            str(context["python_path"]),
            str(context["deploy_path"]),
            "--input",
            str(context["source"]),
            "--mode",
            "usb",
            "--port",
            selected_port,
            "--process-timeout",
            str(timeout),
        ]
        deploy_result = runner(
            deploy_command,
            cwd=work_root,
            env=closed_env,
            timeout=timeout + 30.0,
        )
        deployment_payload = _process_result_payload(deploy_result, expected_marker="DEPLOYMENT PASS")
        if deployment_payload["status"] != STATUS_PASS or not deployment_payload["expected_marker_seen"]:
            raise CleanMachineE2EError("Packaged compile/USB deployment did not complete successfully")
    except Exception as exc:
        failure = str(exc)

    after_hash, after_count = release_tree_digest(root)
    unchanged = before_hash == after_hash and before_count == after_count
    if not unchanged and not failure:
        failure = "Production release tree changed during B2.5 execution"

    payload: dict[str, object] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_FAIL,
        "application": {
            "executable": str(context["application"]),
            "launch_probe": "--acceptance-probe",
        },
        "source": {
            "name": Path(context["source"]).name,
            "sha256": _sha256_file(Path(context["source"])),
        },
        "serial_port": selected_port,
        "clean_machine_contract": {
            "bundled_python_verified": True,
            "host_path_inherited": False,
            "source_checkout_required": False,
            "global_python_required": False,
            "global_platformio_required": False,
            "working_directory_external": True,
            "mutable_state_external": True,
            "dependency_mode": closed_env.get(runtime_paths.DEPENDENCY_MODE_ENV),
            "artifact_path_entries": dependency_closure.path_evidence(closure)["artifact_path_entries"],
        },
        "automated": {
            "robostudio_launch": launch_payload,
            "target_qualification": qualification_payload,
            "deployment": deployment_payload,
        },
        "release_integrity": {
            "before_sha256": before_hash,
            "after_sha256": after_hash,
            "file_count_before": before_count,
            "file_count_after": after_count,
            "unchanged": unchanged,
        },
        "operator_confirmation": {
            "clean_machine": "pending",
            "ui_flow": "pending",
            "robot_execution": "pending",
            "note": "",
        },
        "failure": failure,
    }
    payload["status"] = _status_from_confirmation(payload)
    write_evidence(payload, Path(context["evidence"]), root)
    return validate_evidence_payload(payload)


def load_evidence(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CleanMachineE2EError(f"Invalid B2.5 evidence file: {path}") from exc
    if not isinstance(payload, dict):
        raise CleanMachineE2EError("B2.5 evidence must be a JSON object")
    return validate_evidence_payload(payload)


def confirm_operator_evidence(
    *,
    evidence: Path,
    clean_machine: str,
    ui_flow: str,
    robot_execution: str,
    note: str,
    application_root: Path | None = None,
) -> dict[str, object]:
    """Convert pending evidence to PASS/FAIL only after real operator checks."""
    root = _canonical(application_root or _APPLICATION_ROOT)
    evidence_path = _require_outside(evidence, root, "Acceptance evidence")
    payload = load_evidence(evidence_path)
    if not _automated_stage_passed(payload):
        raise CleanMachineE2EError("Operator confirmation cannot override a failed automated B2.5 stage")

    values = {
        "clean_machine": clean_machine,
        "ui_flow": ui_flow,
        "robot_execution": robot_execution,
    }
    if any(value not in {"pass", "fail"} for value in values.values()):
        raise CleanMachineE2EError("Operator confirmation values must be pass or fail")
    note = note.strip()
    if not note:
        raise CleanMachineE2EError("Operator confirmation requires a non-empty observation note")

    current_hash, current_count = release_tree_digest(root)
    integrity = payload.get("release_integrity")
    if not isinstance(integrity, Mapping):
        raise CleanMachineE2EError("B2.5 evidence is missing release-integrity data")
    if current_hash != integrity.get("after_sha256") or current_count != integrity.get("file_count_after"):
        raise CleanMachineE2EError("Production release changed after automated B2.5 execution; confirmation rejected")

    payload["operator_confirmation"] = {**values, "note": note}
    payload["status"] = _status_from_confirmation(payload)
    write_evidence(payload, evidence_path, root)
    return validate_evidence_payload(payload)


def _print_payload(payload: Mapping[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2))
        return
    print(f"B2.5 clean-machine physical E2E: {payload['status']}")
    if payload.get("failure"):
        print(str(payload["failure"]))
    if payload["status"] == STATUS_PENDING:
        print("Automated stage passed. Confirm clean machine + real GUI flow + robot behavior after observation.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="B2.5 real clean-machine RoboStudio/robot acceptance")
    sub = parser.add_subparsers(dest="command", required=True)

    run_parser = sub.add_parser("run", help="launch, qualify, compile and physically USB-flash; write pending evidence")
    run_parser.add_argument("--port", required=True)
    run_parser.add_argument("--source", required=True, type=Path)
    run_parser.add_argument("--evidence", required=True, type=Path)
    run_parser.add_argument("--timeout", type=float, default=deployment_runtime.DEFAULT_PROCESS_TIMEOUT_SECONDS)
    run_parser.add_argument("--json", action="store_true", dest="as_json")

    confirm_parser = sub.add_parser("confirm", help="record clean-machine, GUI and robot observations after the physical run")
    confirm_parser.add_argument("--evidence", required=True, type=Path)
    confirm_parser.add_argument("--clean-machine", required=True, choices=("pass", "fail"))
    confirm_parser.add_argument("--ui-flow", required=True, choices=("pass", "fail"))
    confirm_parser.add_argument("--robot-result", required=True, choices=("pass", "fail"))
    confirm_parser.add_argument("--note", required=True)
    confirm_parser.add_argument("--json", action="store_true", dest="as_json")

    validate_parser = sub.add_parser("validate", help="validate an existing B2.5 evidence file")
    validate_parser.add_argument("--evidence", required=True, type=Path)
    validate_parser.add_argument("--json", action="store_true", dest="as_json")

    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            payload = run_clean_machine_e2e(
                port=args.port,
                source=args.source,
                evidence=args.evidence,
                timeout=args.timeout,
            )
            _print_payload(payload, args.as_json)
            return 0 if payload["status"] == STATUS_PENDING else 1
        if args.command == "confirm":
            payload = confirm_operator_evidence(
                evidence=args.evidence,
                clean_machine=args.clean_machine,
                ui_flow=args.ui_flow,
                robot_execution=args.robot_result,
                note=args.note,
            )
            _print_payload(payload, args.as_json)
            return 0 if payload["status"] == STATUS_PASS else 1
        payload = load_evidence(args.evidence)
        _print_payload(payload, args.as_json)
        return 0
    except CleanMachineE2EError as exc:
        print(f"B2.5 clean-machine physical E2E: FAIL\n{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
