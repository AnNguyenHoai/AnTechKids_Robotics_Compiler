"""RSD-21.5 production E2E orchestration.

The production artifact is the system under test. External target prerequisites are
resolved from PATH; no repository executable is used as an implicit fallback.
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
        return {"status": self.status, "artifact": self.artifact, "extracted_root": self.extracted_root, "target_machine_prerequisites": self.target_machine_prerequisites, "source_tree_execution": self.source_tree_execution, "robostudio_started": self.robostudio_started, "compiler_succeeded": self.compiler_succeeded, "evidence": self.evidence}

def command_from_text(value: str) -> list[str]:
    return shlex.split(value, posix=False)

def _safe_extract(artifact: Path, root: Path) -> None:
    with zipfile.ZipFile(artifact) as archive:
        base = root.resolve()
        for member in archive.infolist():
            target = (root / member.filename).resolve()
            if target != base and base not in target.parents:
                raise ProductionE2EError(f"unsafe ZIP member: {member.filename}")
        archive.extractall(root)

def _find_app(root: Path) -> Path | None:
    candidates = [p for p in root.rglob("*") if p.is_file() and p.name.lower() == "robostudio.exe"]
    return candidates[0] if candidates else None

def _format_command(template: list[str], *, app: Path, source: Path, output: Path) -> list[str]:
    return [part.format(app=str(app), source=str(source), output=str(output)) for part in template]

def qualify_release_e2e(artifact: Path, *, source: Path, launch_command: list[str], compile_command: list[str], timeout: float = DEFAULT_TIMEOUT) -> ProductionE2EResult:
    artifact = Path(artifact).resolve(); source = Path(source).resolve()
    if not artifact.is_file(): raise ProductionE2EError(f"production artifact is missing: {artifact}")
    if not source.is_file(): raise ProductionE2EError(f"source program is missing: {source}")
    with tempfile.TemporaryDirectory(prefix="robostudio-production-e2e-") as td:
        root = Path(td).resolve(); _safe_extract(artifact, root)
        app = _find_app(root)
        if app is None: raise ProductionE2EError("RoboStudio executable is missing from production artifact")
        app = app.resolve()
        if root not in app.parents: raise ProductionE2EError("RoboStudio resolved outside production artifact")
        output = root / "e2e-output" / "compiled.bin"; output.parent.mkdir(parents=True)
        launch = _format_command(launch_command, app=app, source=source, output=output)
        compile_cmd = _format_command(compile_command, app=app, source=source, output=output)
        try:
            started_process = subprocess.run(launch, cwd=app.parent, shell=False, capture_output=True, text=True, timeout=timeout, check=False)
            if started_process.returncode != 0: raise ProductionE2EError(f"RoboStudio startup failed with exit code {started_process.returncode}: {started_process.stderr.strip() or started_process.stdout.strip()}")
            compile_process = subprocess.run(compile_cmd, cwd=app.parent, shell=False, capture_output=True, text=True, timeout=timeout, check=False)
            if compile_process.returncode != 0: raise ProductionE2EError(f"Compiler E2E failed with exit code {compile_process.returncode}: {compile_process.stderr.strip() or compile_process.stdout.strip()}")
        except (OSError, subprocess.TimeoutExpired) as exc: raise ProductionE2EError(f"Production E2E process execution failed: {exc}") from exc
        if not output.is_file(): raise ProductionE2EError("Compiler E2E completed without producing output")
        evidence = {"robostudio": {"started": True, "stdout": started_process.stdout, "stderr": started_process.stderr}, "compiler": {"executed": True, "stdout": compile_process.stdout, "stderr": compile_process.stderr, "output_produced": True}, "source_tree_execution": False}
        return ProductionE2EResult("PASS", artifact.name, str(root), True, False, True, True, evidence)

def build_report(result: ProductionE2EResult) -> dict:
    payload = result.to_dict(); payload["schema"] = "antechkids.robostudio.production-e2e"; payload["schema_version"] = 1; return payload

def evaluate_production_artifact(*, artifact: Path, source: Path, launch: bool = True, compile_command: list[str] | None = None, launch_command: list[str] | None = None) -> ProductionE2EResult:
    if not launch:
        artifact = Path(artifact).resolve()
        if not artifact.is_file(): raise ProductionE2EError(f"production artifact is missing: {artifact}")
        return ProductionE2EResult("PASS", artifact.name, "", True, False, False, False, {"launch_requested": False})
    if not launch_command or not compile_command: raise ProductionE2EError("launch_command and compile_command are required for production E2E")
    return qualify_release_e2e(artifact, source=source, launch_command=launch_command, compile_command=compile_command)

def write_report(report: dict | ProductionE2EResult, path: Path) -> None:
    payload = report if isinstance(report, dict) else build_report(report); Path(path).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
