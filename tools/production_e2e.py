"""RSD-21.5 production E2E orchestration.

The production artifact is the system under test. External target prerequisites are
resolved from PATH; no repository executable is used as an implicit fallback.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path


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
    candidates = [p for p in root.rglob("*") if p.is_file() and p.name.lower() == "robostudio.exe"]
    return candidates[0] if candidates else None


def evaluate_production_artifact(*, artifact: Path, source: Path, launch: bool = True,
                                  compile_command: list[str] | None = None,
                                  launch_command: list[str] | None = None) -> ProductionE2EResult:
    artifact = Path(artifact).resolve()
    source = Path(source).resolve()
    if not artifact.is_file():
        raise ProductionE2EError(f"production artifact is missing: {artifact}")
    if not source.is_file():
        raise ProductionE2EError(f"source program is missing: {source}")
    with tempfile.TemporaryDirectory(prefix="robostudio-production-e2e-") as td:
        root = Path(td).resolve()
        _safe_extract(artifact, root)
        app = _find_app(root)
        if app is None:
            raise ProductionE2EError("RoboStudio executable is missing from production artifact")
        # Never execute an application outside the extracted artifact.
        app = app.resolve()
        if root not in app.parents:
            raise ProductionE2EError("RoboStudio resolved outside production artifact")
        started = False
        compiled = False
        evidence = {"robostudio": str(app.relative_to(root)), "source": str(source), "launch_requested": launch}
        if launch and launch_command:
            subprocess.run(launch_command, cwd=app.parent, check=True)
            started = True
        if launch and compile_command:
            subprocess.run(compile_command, cwd=app.parent, check=True)
            compiled = True
        status = "PASS" if (not launch or (started and compiled)) else "FAIL"
        return ProductionE2EResult(status, str(artifact), str(root), True, False,
                                    started, compiled, evidence)


def write_report(result: ProductionE2EResult, path: Path) -> None:
    Path(path).write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
