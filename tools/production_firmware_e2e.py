"""RSD-30 production firmware-build E2E harness.

The production ZIP is the system under test. The harness extracts it, validates
its PlatformIO closure, copies the packaged firmware template into an isolated
writable workspace, optionally installs a generated program header, and runs
PlatformIO exclusively through the packaged Python runtime.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

from tools import production_platformio_closure

DEFAULT_TIMEOUT = 600.0


class ProductionFirmwareE2EError(RuntimeError):
    """Raised when the production firmware build qualification fails."""


@dataclass(frozen=True)
class ProductionFirmwareE2EResult:
    status: str
    artifact: str
    environment: str
    firmware: str
    firmware_size: int
    firmware_sha256: str
    evidence: dict

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict:
        return {
            "schema": "antechkids.robostudio.production-firmware-build-e2e",
            "schema_version": 1,
            "status": self.status,
            "artifact": self.artifact,
            "environment": self.environment,
            "firmware": self.firmware,
            "firmware_size": self.firmware_size,
            "firmware_sha256": self.firmware_sha256,
            "evidence": self.evidence,
        }


def _safe_extract(artifact: Path, root: Path) -> None:
    with zipfile.ZipFile(artifact) as archive:
        base = root.resolve()
        for member in archive.infolist():
            target = (root / member.filename).resolve()
            if target != base and base not in target.parents:
                raise ProductionFirmwareE2EError(f"unsafe ZIP member: {member.filename}")
        archive.extractall(root)


def _find_root(root: Path) -> Path:
    candidates = [root, *[p for p in root.iterdir() if p.is_dir()]]
    matches = [p for p in candidates if (p / "firmware" / "robot-platform" / "platformio.ini").is_file()]
    if len(matches) != 1:
        raise ProductionFirmwareE2EError(
            f"Expected exactly one production distribution root containing firmware/robot-platform, found {len(matches)}"
        )
    return matches[0]


def _safe_project_name(value: str) -> str:
    name = str(value).strip()
    if not name or Path(name).name != name or "/" in name or "\\" in name or name in {".", ".."}:
        raise ProductionFirmwareE2EError(f"Invalid build project name: {value!r}")
    return name


def _copy_template(source: Path, destination: Path) -> None:
    forbidden = {".git", ".pio", "penv", ".venv", "__pycache__", ".pytest_cache"}
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        if any(part.lower() in forbidden for part in relative.parts):
            continue
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def _install_header(header: Path, workspace: Path) -> Path:
    if not header.is_file() or header.stat().st_size <= 0:
        raise ProductionFirmwareE2EError(f"Generated firmware header is missing or empty: {header}")
    target = workspace / "main" / "src" / "Application" / "generated_program.h"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(header, target)
    return target


def _platformio_command(python: Path) -> list[str]:
    if not python.is_file():
        raise ProductionFirmwareE2EError(f"Bundled Python runtime is missing: {python}")
    if python.name.lower() != "python.exe":
        raise ProductionFirmwareE2EError(f"Production firmware E2E requires bundled Windows Python: {python}")
    return [str(python), "-m", "platformio", "run"]


def _build_environment(platformio_root: Path, workspace_root: Path, host_environment: dict[str, str] | None) -> dict[str, str]:
    env = dict(os.environ if host_environment is None else host_environment)
    env.update({
        "PLATFORMIO_CORE_DIR": str(platformio_root),
        "PLATFORMIO_PLATFORMS_DIR": str(platformio_root / "platforms"),
        "PLATFORMIO_PACKAGES_DIR": str(platformio_root / "packages"),
        "PLATFORMIO_WORKSPACE_DIR": str(workspace_root / "pio-workspace"),
        "PLATFORMIO_BUILD_DIR": str(workspace_root / "pio-build"),
        "PLATFORMIO_LIBDEPS_DIR": str(workspace_root / "pio-libdeps"),
        "PLATFORMIO_CACHE_DIR": str(workspace_root / "pio-cache"),
        "PLATFORMIO_BUILD_CACHE_DIR": str(workspace_root / "pio-build-cache"),
        "PLATFORMIO_SHARED_DIR": str(workspace_root / "pio-shared"),
        "PLATFORMIO_NO_ANSI": "true",
        "PLATFORMIO_DISABLE_PROGRESSBAR": "true",
        "PLATFORMIO_SETTING_ENABLE_TELEMETRY": "false",
    })
    env.pop("PLATFORMIO_HOME", None)
    return env


def _run(command: list[str], *, cwd: Path, env: dict[str, str], timeout: float) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, cwd=cwd, env=env, check=True, timeout=timeout, text=True, capture_output=True, shell=False)
    except FileNotFoundError as exc:
        raise ProductionFirmwareE2EError(f"Bundled PlatformIO command is unavailable: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ProductionFirmwareE2EError(f"Production firmware build timed out after {timeout:g}s") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise ProductionFirmwareE2EError(f"Production firmware build failed with exit code {exc.returncode}: {detail}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_production_firmware(artifact: Path, *, environment: str = "esp32dev", header: Path | None = None, project_name: str = "production-e2e", timeout: float = DEFAULT_TIMEOUT, host_environment: dict[str, str] | None = None) -> ProductionFirmwareE2EResult:
    artifact = Path(artifact).expanduser().resolve()
    if not artifact.is_file():
        raise ProductionFirmwareE2EError(f"Production artifact is missing: {artifact}")
    if environment not in {"esp32dev", "esp32dev_bootstrap", "esp32dev_ota"}:
        raise ProductionFirmwareE2EError(f"Unsupported production environment: {environment}")
    if timeout <= 0:
        raise ProductionFirmwareE2EError("timeout must be greater than zero")
    project_name = _safe_project_name(project_name)

    with tempfile.TemporaryDirectory(prefix="robostudio-production-firmware-e2e-") as td:
        extracted = Path(td) / "extracted"
        extracted.mkdir()
        _safe_extract(artifact, extracted)
        root = _find_root(extracted)
        firmware_template = root / "firmware" / "robot-platform"
        platformio_root = root / "runtime" / "platformio"
        python = root / "runtime" / "bin" / "python.exe"

        try:
            closure = production_platformio_closure.validate_distribution(root)
        except production_platformio_closure.ProductionPlatformIOClosureError as exc:
            raise ProductionFirmwareE2EError(f"PlatformIO dependency closure failed: {exc}") from exc

        workspace_root = Path(td) / "workspace" / project_name
        workspace_root.mkdir(parents=True)
        firmware_workspace = workspace_root / "firmware"
        _copy_template(firmware_template, firmware_workspace)
        generated_header = _install_header(header, firmware_workspace) if header else None
        env = _build_environment(platformio_root, workspace_root, host_environment)
        command = _platformio_command(python) + ["-e", environment]
        result = _run(command, cwd=firmware_workspace, env=env, timeout=timeout)

        firmware = workspace_root / "pio-build" / environment / "firmware.bin"
        if not firmware.is_file() or firmware.stat().st_size <= 0:
            raise ProductionFirmwareE2EError(f"PlatformIO exited successfully but firmware artifact is missing or empty: {firmware}")
        if (firmware_template / ".pio").exists():
            raise ProductionFirmwareE2EError("Production firmware template was mutated with .pio build state")
        if (platformio_root / ".pio").exists():
            raise ProductionFirmwareE2EError("Packaged PlatformIO runtime was mutated with .pio build state")

        evidence = {
            "bundled_python": str(python.relative_to(root)),
            "platformio_runtime": str(platformio_root.relative_to(root)),
            "firmware_template": str(firmware_template.relative_to(root)),
            "workspace": str(workspace_root),
            "environment": environment,
            "platformio_command": command,
            "cwd": str(firmware_workspace),
            "closure": closure,
            "header": str(generated_header.relative_to(workspace_root)) if generated_header else None,
            "build_returncode": result.returncode,
            "build_stdout": result.stdout,
            "build_stderr": result.stderr,
            "host_python_used": False,
            "host_platformio_resolution": False,
        }
        return ProductionFirmwareE2EResult("PASS", str(artifact), environment, str(firmware.relative_to(workspace_root)), firmware.stat().st_size, _sha256(firmware), evidence)


def write_report(result: ProductionFirmwareE2EResult, path: Path) -> Path:
    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build firmware using the production ZIP runtime")
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--environment", choices=("esp32dev", "esp32dev_bootstrap", "esp32dev_ota"), default="esp32dev")
    parser.add_argument("--header", type=Path)
    parser.add_argument("--project-name", default="production-e2e")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        result = build_production_firmware(args.artifact, environment=args.environment, header=args.header, project_name=args.project_name, timeout=args.timeout)
        if args.report:
            write_report(result, args.report)
    except ProductionFirmwareE2EError as exc:
        print(f"RSD-30 production firmware E2E: FAIL: {exc}")
        return 1
    print("RSD-30 production firmware E2E: PASS")
    print(f"Firmware: {result.firmware}")
    print(f"SHA-256: {result.firmware_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
