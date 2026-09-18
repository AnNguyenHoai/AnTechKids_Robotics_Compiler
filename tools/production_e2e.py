"""Production RoboStudio + Compiler E2E orchestration.

The production ZIP is the system under test. RoboStudio, the application-owned
compiler, and the application-owned Python runtime are resolved from the
extracted artifact.
"""
from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TIMEOUT = 30.0
COMPILER_ENTRY = Path("compiler") / "main.py"
PYTHON_ENTRY = Path("runtime") / "bin" / "python.exe"


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
    artifact_sha256: str = ""

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "artifact": self.artifact,
            "artifact_sha256": self.artifact_sha256,
            "extracted_root": self.extracted_root,
            "target_machine_prerequisites": self.target_machine_prerequisites,
            "source_tree_execution": self.source_tree_execution,
            "robostudio_started": self.robostudio_started,
            "compiler_succeeded": self.compiler_succeeded,
            "evidence": self.evidence,
        }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    return sorted(candidates, key=lambda p: p.as_posix().lower())[0] if candidates else None


def _find_compiler(root: Path) -> Path | None:
    candidate = root / COMPILER_ENTRY
    return candidate if candidate.is_file() else None


def _find_python(root: Path) -> Path | None:
    candidate = root / PYTHON_ENTRY
    return candidate if candidate.is_file() else None


def _run(command: list[str], *, cwd: Path, timeout: float, label: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    if not command:
        raise ProductionE2EError(f"{label} command is empty")
    try:
        return subprocess.run(command, cwd=cwd, env=env, check=True, timeout=timeout, text=True, capture_output=True, shell=False)
    except FileNotFoundError as exc:
        raise ProductionE2EError(f"{label} command is unavailable: {command[0]}") from exc
    except OSError as exc:
        winerror = getattr(exc, "winerror", None)
        if winerror is not None:
            detail = f"WinError {winerror}"
        elif exc.errno is not None:
            detail = f"errno {exc.errno}"
        else:
            detail = type(exc).__name__
        raise ProductionE2EError(f"{label} could not start ({detail})") from exc
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


def _artifact_relative(root: Path, path: Path) -> str:
    """Return artifact evidence paths in ZIP-style POSIX form on every host."""
    return path.relative_to(root).as_posix()


def evaluate_production_artifact(
    *,
    artifact: Path,
    source: Path,
    launch: bool = True,
    compile_command: list[str] | None = None,
    launch_command: list[str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    environment: dict[str, str] | None = None,
) -> ProductionE2EResult:
    artifact = Path(artifact).resolve()
    source = Path(source).resolve()
    if not artifact.is_file():
        raise ProductionE2EError(f"production artifact is missing: {artifact}")
    if not source.is_file():
        raise ProductionE2EError(f"source program is missing: {source}")
    if timeout <= 0:
        raise ProductionE2EError("timeout must be greater than zero")
    artifact_sha256 = _sha256(artifact)

    with tempfile.TemporaryDirectory(prefix="robostudio-production-e2e-") as td:
        root = Path(td).resolve()
        _safe_extract(artifact, root)
        app = _find_app(root)
        if app is None:
            raise ProductionE2EError("RoboStudio executable is missing from production artifact")
        app = app.resolve()
        if root not in app.parents:
            raise ProductionE2EError("RoboStudio resolved outside production artifact")
        compiler = _find_compiler(root)
        bundled_python = _find_python(root)
        if compiler is None and compile_command:
            raise ProductionE2EError("application-owned compiler entry point is missing from production artifact")
        if bundled_python is None and (compile_command or launch_command):
            raise ProductionE2EError("application-owned Python runtime is missing from production artifact")

        started = compiled = False
        output = root / "e2e-output" / "program.h"
        output.parent.mkdir(parents=True, exist_ok=True)
        evidence = {
            "robostudio": _artifact_relative(root, app),
            "compiler": _artifact_relative(root, compiler) if compiler else None,
            "bundled_python": _artifact_relative(root, bundled_python) if bundled_python else None,
            "source": str(source),
            "launch_requested": launch,
            "target_cwd": str(app.parent),
            "compiler_output_contract": _artifact_relative(root, output),
        }

        values = {
            "app": app,
            "compiler": compiler or root / COMPILER_ENTRY,
            "python": bundled_python or root / PYTHON_ENTRY,
            "source": source,
            "output": output,
        }
        if launch and launch_command:
            launch_result = _run(_render_command(launch_command, **values), cwd=app.parent, timeout=timeout, label="RoboStudio launch", env=environment)
            started = True
            evidence["launch_returncode"] = launch_result.returncode
            evidence["launch_stdout"] = launch_result.stdout
            evidence["launch_stderr"] = launch_result.stderr

        if compile_command:
            compile_result = _run(_render_command(compile_command, **values), cwd=app.parent, timeout=timeout, label="compiler E2E", env=environment)
            compiled = output.is_file() and output.stat().st_size > 0
            evidence["compile_returncode"] = compile_result.returncode
            evidence["compile_stdout"] = compile_result.stdout
            evidence["compile_stderr"] = compile_result.stderr
            evidence["compiler_output"] = _artifact_relative(root, output) if compiled else None
            evidence["compiler_output_size"] = output.stat().st_size if compiled else 0
            if not compiled:
                raise ProductionE2EError("compiler exited successfully but produced no output")

        passed = (not launch or started) and (not compile_command or compiled)
        # This harness validates the application-owned artifact itself; it does not
        # require external target-machine prerequisites such as USB drivers or hardware.
        return ProductionE2EResult(
            status="PASS" if passed else "FAIL",
            artifact=str(artifact),
            extracted_root=str(root),
            target_machine_prerequisites=False,
            source_tree_execution=False,
            robostudio_started=started,
            compiler_succeeded=compiled,
            evidence=evidence,
            artifact_sha256=artifact_sha256,
        )


def qualify_release_e2e(artifact: Path, *, source: Path, launch_command: list[str], compile_command: list[str], timeout: float = DEFAULT_TIMEOUT) -> ProductionE2EResult:
    """Run RoboStudio startup and the packaged compiler against an extracted ZIP."""
    return evaluate_production_artifact(artifact=artifact, source=source, launch=True, launch_command=launch_command, compile_command=compile_command, timeout=timeout)


def build_report(result: ProductionE2EResult) -> dict:
    return result.to_dict()


def write_report(report: dict, path: Path) -> Path:
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path
