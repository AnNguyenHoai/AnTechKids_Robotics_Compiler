"""RSD-21.5 production RoboStudio + Compiler E2E orchestration.

The production artifact is the system under test. External target prerequisites are
resolved from the target machine; no repository executable is used as an implicit
fallback. The module exposes both the structured Python API used by regression
tests and the command-template API used by the release CLI.
"""
from __future__ import annotations

import json
import shlex
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TIMEOUT = 30.0


class ProductionE2EError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProductionE2EResult:
    status: str
    artifact: str
    extracted_root: str
    target_machine_prerequisites: bool
    source_tree_execution: bool
    robostudio_started: bool
    compiler_succeeded: bool
    evidence: dict

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "artifact": self.artifact,
            "extracted_root": self.extracted_root,
            "target_machine_prerequisites": self.target_machine_prerequisites,
            "source_tree_execution": self.source_tree_execution,
            "robostudio_started": self.robostudio_started,
            "compiler_succeeded": self.compiler_succeeded,
            "evidence": self.evidence,
        }


def _safe_extract(artifact: Path, root: Path) -> None:
    with zipfile.ZipFile(artifact) as archive:
        base = root.resolve()
        for member in archive.infolist():
            target = (root / member.filename).resolve()
            if target != base and base not in target.parents:
                raise ProductionE2EError(f"unsafe ZIP member: {member.filename}")
        archive.extractall(root)


def _find_app(root: Path) -> Path | None:
    candidates = [
        p for p in root.rglob("*") if p.is_file() and p.name.lower() == "robostudio.exe"
    ]
    return sorted(candidates, key=lambda p: p.as_posix().lower())[0] if candidates else None


def _run(command: list[str], *, cwd: Path, timeout: float, label: str) -> subprocess.CompletedProcess[str]:
    if not command:
        raise ProductionE2EError(f"{label} command is empty")
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            check=True,
            timeout=timeout,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise ProductionE2EError(f"{label} command is unavailable: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ProductionE2EError(f"{label} timed out after {timeout:g}s") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        suffix = f": {detail}" if detail else ""
        raise ProductionE2EError(f"{label} failed with exit code {exc.returncode}{suffix}") from exc


def command_from_text(value: str) -> list[str]:
    """Parse a command template without invoking a shell."""
    if not value or not value.strip():
        raise ProductionE2EError("command template is empty")
    return shlex.split(value, posix=False)


def _render_command(command: list[str], **values: Path) -> list[str]:
    rendered = []
    for token in command:
        value = token
        for name, path in values.items():
            value = value.replace("{" + name + "}", str(path))
        rendered.append(value)
    return rendered


def evaluate_production_artifact(
    *,
    artifact: Path,
    source: Path,
    launch: bool = True,
    compile_command: list[str] | None = None,
    launch_command: list[str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> ProductionE2EResult:
    artifact = Path(artifact).resolve()
    source = Path(source).resolve()
    if not artifact.is_file():
        raise ProductionE2EError(f"production artifact is missing: {artifact}")
    if not source.is_file():
        raise ProductionE2EError(f"source program is missing: {source}")
    if timeout <= 0:
        raise ProductionE2EError("timeout must be greater than zero")

    with tempfile.TemporaryDirectory(prefix="robostudio-production-e2e-") as td:
        root = Path(td).resolve()
        _safe_extract(artifact, root)
        app = _find_app(root)
        if app is None:
            raise ProductionE2EError("RoboStudio executable is missing from production artifact")
        app = app.resolve()
        if root not in app.parents:
            raise ProductionE2EError("RoboStudio resolved outside production artifact")

        started = compiled = False
        output = root / "e2e-output" / "program.bytecode"
        evidence = {
            "robostudio": str(app.relative_to(root)),
            "source": str(source),
            "launch_requested": launch,
            "target_cwd": str(app.parent),
        }

        if launch and launch_command:
            launch_result = _run(
                _render_command(launch_command, app=app, source=source, output=output),
                cwd=app.parent,
                timeout=timeout,
                label="RoboStudio launch",
            )
            started = True
            evidence["launch_returncode"] = launch_result.returncode
            evidence["launch_stdout"] = launch_result.stdout
            evidence["launch_stderr"] = launch_result.stderr

        if launch and compile_command:
            compile_result = _run(
                _render_command(compile_command, app=app, source=source, output=output),
                cwd=app.parent,
                timeout=timeout,
                label="compiler E2E",
            )
            compiled = output.is_file()
            evidence["compile_returncode"] = compile_result.returncode
            evidence["compile_stdout"] = compile_result.stdout
            evidence["compile_stderr"] = compile_result.stderr
            evidence["compiler_output"] = str(output.relative_to(root)) if compiled else None
            if not compiled:
                raise ProductionE2EError("compiler exited successfully but produced no output")

        passed = not launch or (started and compiled)
        return ProductionE2EResult(
            "PASS" if passed else "FAIL",
            str(artifact),
            str(root),
            True,
            False,
            started,
            compiled,
            evidence,
        )


def qualify_release_e2e(
    artifact: Path,
    *,
    source: Path,
    launch_command: list[str],
    compile_command: list[str],
    timeout: float = DEFAULT_TIMEOUT,
) -> ProductionE2EResult:
    """Run RoboStudio startup and compiler E2E against the extracted ZIP."""
    return evaluate_production_artifact(
        artifact=artifact,
        source=source,
        launch=True,
        launch_command=launch_command,
        compile_command=compile_command,
        timeout=timeout,
    )


def build_report(result: ProductionE2EResult) -> dict:
    return result.to_dict()


def write_report(report: dict, path: Path) -> Path:
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path
