"""RSD-21.5 production RoboStudio + Compiler end-to-end qualification.

This module operates on the release ZIP as the system under test. It extracts
that ZIP into an isolated temporary directory and executes explicitly supplied
application commands from the extracted release. It does not import the
repository's application code, use the developer working tree, install tools,
or mutate the target machine.

The real RoboStudio executable is supplied by the release artifact. Since this
repository does not own the GUI executable build, the launch/compile command
syntax is supplied by the target RoboStudio build through command templates.
The placeholders are {app}, {source}, and {output}.
"""
from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from tools import release_package

SCHEMA = "antechkids.robostudio.production-e2e"
SCHEMA_VERSION = 1
DEFAULT_TIMEOUT = 60.0


class ProductionE2EError(RuntimeError):
    """Raised when the production artifact cannot complete E2E qualification."""


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ProductionE2EResult:
    artifact: Path
    application: Path
    source: Path
    output: Path
    launch: CommandResult
    compile: CommandResult
    output_produced: bool
    output_size: int

    @property
    def passed(self) -> bool:
        return (
            self.launch.returncode == 0
            and self.compile.returncode == 0
            and self.output_produced
            and self.output_size > 0
        )


def _run(command: Sequence[str], *, cwd: Path, timeout: float, env: dict[str, str] | None = None) -> CommandResult:
    try:
        completed = subprocess.run(
            list(command), cwd=cwd, capture_output=True, text=True,
            timeout=timeout, check=False, shell=False, env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return CommandResult(tuple(command), 1, "", str(exc))
    return CommandResult(tuple(command), completed.returncode, completed.stdout or "", completed.stderr or "")


def run_application(command: Sequence[str], *, cwd: Path | None = None, timeout: float = DEFAULT_TIMEOUT) -> CommandResult:
    """Run one explicit production application command without shell expansion."""
    return _run(command, cwd=cwd or Path.cwd(), timeout=timeout)


def _render(template: Sequence[str], *, app: Path, source: Path, output: Path) -> list[str]:
    values = {"{app}": str(app), "{source}": str(source), "{output}": str(output)}
    return [next((token.replace(k, v) for k, v in values.items() if k in token), token) for token in template]


def _extract(artifact: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(artifact, "r") as archive:
        archive.extractall(destination)
    return destination


def _resolve_application(extracted_root: Path, manifest: dict[str, object]) -> Path:
    application = str(manifest.get("application") or "")
    if not application:
        raise ProductionE2EError("Release manifest does not declare the RoboStudio application")
    matches = [p for p in extracted_root.rglob(application) if p.is_file()]
    if len(matches) != 1:
        raise ProductionE2EError(f"Expected exactly one packaged application executable '{application}', found {len(matches)}")
    return matches[0]


def qualify_release_e2e(
    artifact: Path, *, source: Path, launch_command: Sequence[str],
    compile_command: Sequence[str], timeout: float = DEFAULT_TIMEOUT,
) -> ProductionE2EResult:
    """Run RoboStudio startup and compiler execution against the extracted ZIP."""
    artifact = Path(artifact).expanduser().resolve()
    source = Path(source).expanduser().resolve()
    if not source.is_file():
        raise ProductionE2EError(f"Missing E2E sample source: {source}")
    try:
        manifest = release_package.validate_release_artifact(artifact)
    except release_package.ReleasePackageError as exc:
        raise ProductionE2EError(f"Release artifact validation failed: {exc}") from exc

    with tempfile.TemporaryDirectory(prefix="robostudio-rsd21-5-") as temp:
        extracted = _extract(artifact, Path(temp))
        app = _resolve_application(extracted, manifest)
        workdir = app.parent
        output = Path(temp) / "e2e-output" / "program.bytecode"
        output.parent.mkdir(parents=True, exist_ok=True)
        launch = run_application(_render(launch_command, app=app, source=source, output=output), cwd=workdir, timeout=timeout)
        compile_result = run_application(_render(compile_command, app=app, source=source, output=output), cwd=workdir, timeout=timeout)
        output_produced = output.is_file()
        output_size = output.stat().st_size if output_produced else 0
        return ProductionE2EResult(artifact, app, source, output, launch, compile_result, output_produced, output_size)


def build_report(result: ProductionE2EResult) -> dict[str, object]:
    """Create stable, machine-readable E2E evidence."""
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if result.passed else "FAIL",
        "qualified": result.passed,
        "target_machine": True,
        "artifact": result.artifact.name,
        "artifact_sha256": _sha256(result.artifact),
        "host_prerequisites_packaged": False,
        "robostudio": {
            "application": result.application.name,
            "started": result.launch.returncode == 0,
            "returncode": result.launch.returncode,
            "stdout": result.launch.stdout,
            "stderr": result.launch.stderr,
        },
        "compiler": {
            "executed": result.compile.returncode == 0,
            "returncode": result.compile.returncode,
            "output_produced": result.output_produced,
            "output_size": result.output_size,
            "stdout": result.compile.stdout,
            "stderr": result.compile.stderr,
        },
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_report(report: dict[str, object], path: Path) -> Path:
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return destination


def command_from_text(value: str) -> list[str]:
    """Parse a command template without invoking a shell."""
    if not value.strip():
        raise ProductionE2EError("E2E command must not be empty")
    return shlex.split(value, posix=os.name != "nt")


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Run RoboStudio + Compiler E2E against a production release ZIP")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--launch-command", required=True, help="command template containing {app}")
    parser.add_argument("--compile-command", required=True, help="command template containing {app}, {source}, {output}")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    args = parser.parse_args(argv)
    try:
        result = qualify_release_e2e(args.artifact, source=args.source, launch_command=command_from_text(args.launch_command), compile_command=command_from_text(args.compile_command), timeout=args.timeout)
        report = build_report(result)
        if args.report:
            write_report(report, args.report)
    except ProductionE2EError as exc:
        print(f"RSD-21.5 RoboStudio + Compiler E2E: FAIL: {exc}")
        return 1
    print(f"RSD-21.5 RoboStudio + Compiler E2E: {report['status']}")
    print(f"Artifact: {args.artifact.resolve()}")
    print(f"RoboStudio started: {report['robostudio']['started']}")
    print(f"Compiler executed: {report['compiler']['executed']}")
    print(f"Compiler output: {report['compiler']['output_produced']}")
    if args.report:
        print(f"E2E report: {args.report.resolve()}")
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
