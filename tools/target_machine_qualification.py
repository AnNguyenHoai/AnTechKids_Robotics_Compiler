"""RSD-21.4 target-machine-aware release qualification.

The gate validates the host contract for a production RoboStudio release.
Python and PlatformIO are prerequisites installed by the target user; they are
not copied from the build machine and are not treated as release payload.
The qualification is read-only and never installs or mutates host tooling.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Mapping

from tools import target_machine_prerequisites

SCHEMA = "antechkids.robostudio.target-machine-qualification"
SCHEMA_VERSION = 1


class TargetMachineQualificationError(RuntimeError):
    """Raised when the target-machine prerequisite contract is not satisfied."""


@dataclass(frozen=True)
class PrerequisiteResult:
    name: str
    required_for: tuple[str, ...]
    required: bool
    available: bool
    executable: str | None
    version_output: str | None
    validation: str


@dataclass(frozen=True)
class TargetMachineQualificationReport:
    scope: str
    passed: bool
    automated_checks_passed: bool
    manual_checks_required: bool
    prerequisites: tuple[PrerequisiteResult, ...]


def _run_version(command: tuple[str, ...], env: Mapping[str, str] | None) -> tuple[bool, str | None]:
    """Run a read-only prerequisite version command without shell expansion."""
    try:
        completed = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env=dict(env) if env is not None else None,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, None
    output = (completed.stdout or completed.stderr).strip()
    return completed.returncode == 0, output or None


def _check_item(item: target_machine_prerequisites.TargetMachinePrerequisite, env: Mapping[str, str] | None) -> PrerequisiteResult:
    if item.kind is target_machine_prerequisites.PrerequisiteKind.DRIVER:
        return PrerequisiteResult(
            name=item.name,
            required_for=tuple(scope.value for scope in item.required_for),
            required=True,
            available=False,
            executable=None,
            version_output=None,
            validation="manual",
        )

    executable = shutil.which(item.command[0], path=(env or {}).get("PATH") if env is not None else None)
    if executable is None:
        return PrerequisiteResult(
            name=item.name,
            required_for=tuple(scope.value for scope in item.required_for),
            required=True,
            available=False,
            executable=None,
            version_output=None,
            validation="missing",
        )

    available, output = _run_version(item.command, env)
    return PrerequisiteResult(
        name=item.name,
        required_for=tuple(scope.value for scope in item.required_for),
        required=True,
        available=available,
        executable=executable,
        version_output=output,
        validation="command-pass" if available else "command-failed",
    )


def qualify_target_machine(
    *,
    scope: target_machine_prerequisites.RequirementScope | str = target_machine_prerequisites.RequirementScope.COMPILE,
    env: Mapping[str, str] | None = None,
) -> TargetMachineQualificationReport:
    """Qualify the target host for the requested release usage scope.

    ``compile`` validates Python. ``hardware`` validates both Python and
    PlatformIO and records the ESP32 driver as a manual check. The driver is
    intentionally not guessed from the host because USB/UART bridge hardware
    differs between boards.
    """
    target_machine_prerequisites.validate_contract()
    scope = target_machine_prerequisites.RequirementScope(scope)
    items = target_machine_prerequisites.for_scope(scope)
    results = tuple(_check_item(item, env) for item in items)
    automated = all(item.available for item in results if item.validation != "manual")
    manual_required = any(item.validation == "manual" for item in results)
    return TargetMachineQualificationReport(
        scope=scope.value,
        passed=automated,
        automated_checks_passed=automated,
        manual_checks_required=manual_required,
        prerequisites=results,
    )


def require_target_machine(
    *,
    scope: target_machine_prerequisites.RequirementScope | str = target_machine_prerequisites.RequirementScope.COMPILE,
    env: Mapping[str, str] | None = None,
) -> TargetMachineQualificationReport:
    """Run qualification and raise with actionable prerequisite diagnostics."""
    report = qualify_target_machine(scope=scope, env=env)
    if not report.passed:
        missing = [item.name for item in report.prerequisites if item.validation in {"missing", "command-failed"}]
        detail = ", ".join(missing) if missing else "unknown prerequisite failure"
        raise TargetMachineQualificationError(
            f"Target machine is not qualified for {report.scope}: {detail}"
        )
    return report


def to_dict(report: TargetMachineQualificationReport) -> dict[str, object]:
    """Serialize stable qualification evidence without exposing host secrets."""
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "setup_contract": {
            "schema": target_machine_prerequisites.SCHEMA,
            "schema_version": target_machine_prerequisites.SCHEMA_VERSION,
            "supported_host_os": target_machine_prerequisites.SUPPORTED_HOST_OS,
            "path_policy": target_machine_prerequisites.PATH_POLICY,
        },
        "scope": report.scope,
        "passed": report.passed,
        "automated_checks_passed": report.automated_checks_passed,
        "manual_checks_required": report.manual_checks_required,
        "prerequisites": [
            {
                "name": item.name,
                "required_for": list(item.required_for),
                "required": item.required,
                "available": item.available,
                "executable": item.executable,
                "version_output": item.version_output,
                "validation": item.validation,
            }
            for item in report.prerequisites
        ],
    }


def write_report(report: TargetMachineQualificationReport, path) -> None:
    """Write machine-readable target-machine qualification evidence."""
    from pathlib import Path

    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(to_dict(report), indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Qualify target-machine prerequisites for RoboStudio")
    parser.add_argument("--scope", choices=[scope.value for scope in target_machine_prerequisites.RequirementScope], default="compile")
    parser.add_argument("--report", type=str)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    report = qualify_target_machine(scope=args.scope)
    if args.report:
        write_report(report, args.report)
    if args.as_json:
        print(json.dumps(to_dict(report), indent=2))
    else:
        print(f"RSD-21.4 target-machine qualification: {'PASS' if report.passed else 'FAIL'}")
        for item in report.prerequisites:
            status = item.validation
            if item.version_output:
                status = f"{status}: {item.version_output}"
            print(f"{item.name}: {status}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
