#!/usr/bin/env python3
"""Verify that the packaged RoboStudio runtime can build first-flash offline.

This is a production-release gate, not a source-tree compile test.  It uses the
already assembled ``releases/production/RoboStudio`` distribution, a completely
fresh external RoboStudio state root, the bundled Python interpreter, and the
bundled PlatformIO platform/package stores.  Network proxies are deliberately
poisoned so a missing dependency cannot be hidden by the CI/build machine.

The gate also verifies PlatformIO's installation metadata (``.piopm``).  A
``package.json`` alone is not enough for PlatformIO Package Manager to consider
a package installed; losing ``.piopm`` during packaging can make first-flash
silently download hundreds of megabytes on the target PC.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
else:
    ROOT = Path(__file__).resolve().parents[1]

from tools import dependency_closure, production_platformio_closure, release_package, runtime_paths

REPORT_SCHEMA = "antechkids.robostudio.packaged-platformio-offline-first-flash"
REPORT_SCHEMA_VERSION = 1
FORBIDDEN_PROVISIONING_MARKERS = (
    "tool manager: installing",
    "platform manager: installing",
    "library manager: installing",
    "downloading...",
    "downloading ",
)


class OfflineFirstFlashError(RuntimeError):
    pass


def _json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OfflineFirstFlashError(f"Invalid {label}: {path}") from exc
    if not isinstance(value, dict):
        raise OfflineFirstFlashError(f"Invalid {label}: expected JSON object: {path}")
    return value


def _release_artifact(release_dir: Path) -> Path:
    version_path = ROOT / "VERSION"
    if not version_path.is_file():
        raise OfflineFirstFlashError(f"VERSION is missing: {version_path}")
    version = version_path.read_text(encoding="utf-8").strip()
    artifact = release_dir / f"RoboStudio-{version}-Windows.zip"
    if not artifact.is_file():
        raise OfflineFirstFlashError(f"Production ZIP is missing: {artifact}")
    return artifact


def _validate_package_install_metadata(
    distribution: Path,
    closure: dict[str, Any],
    release_manifest: dict[str, Any],
) -> list[dict[str, str]]:
    runtime = distribution / "runtime" / "platformio"
    archived = {str(item.get("path", "")) for item in release_manifest.get("files", [])}
    evidence: list[dict[str, str]] = []
    for record in closure.get("packages", []):
        if not isinstance(record, dict):
            raise OfflineFirstFlashError("PlatformIO closure contains an invalid package record")
        name = str(record.get("name", "")).strip()
        version = str(record.get("version", "")).strip()
        metadata_relative = Path(str(record.get("metadata", "")))
        if not name or not version or metadata_relative.name != "package.json":
            raise OfflineFirstFlashError(f"Invalid PlatformIO package closure record: {record!r}")
        package_root = runtime / metadata_relative.parent
        piopm = package_root / ".piopm"
        if not piopm.is_file():
            raise OfflineFirstFlashError(
                f"Bundled PlatformIO package {name}@{version} is missing installation metadata: {piopm}"
            )
        data = _json(piopm, f"PlatformIO installation metadata for {name}")
        installed_name = str(data.get("name", "")).strip()
        installed_version = str(data.get("version", "")).strip()
        if installed_name != name or installed_version != version:
            raise OfflineFirstFlashError(
                f"Bundled PlatformIO package metadata mismatch for {name}: "
                f"package={name}@{version}, .piopm={installed_name}@{installed_version}"
            )
        archived_piopm = (Path("runtime") / "platformio" / metadata_relative.parent / ".piopm").as_posix()
        if archived_piopm not in archived:
            raise OfflineFirstFlashError(
                f"Production ZIP inventory dropped PlatformIO installation metadata: {archived_piopm}"
            )
        evidence.append(
            {
                "name": name,
                "version": version,
                "metadata": metadata_relative.as_posix(),
                "piopm": archived_piopm,
            }
        )
    if not evidence:
        raise OfflineFirstFlashError("PlatformIO dependency closure resolved no packages")
    return evidence


def _bootstrap_config(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "type": "antechkids.robot.bootstrap",
                "schema_version": 1,
                "wifi": {"ssid": "RoboStudio-Offline-Gate", "password": "offline-test"},
                "ota": {"password": "offline-gate-secret"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _kill_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        process.kill()
    except OSError:
        pass


def _run_offline_bootstrap_build(
    distribution: Path,
    work_root: Path,
    *,
    timeout: float,
) -> tuple[str, Path, float]:
    python = distribution / "runtime" / "bin" / "python.exe"
    if not python.is_file():
        raise OfflineFirstFlashError(f"Bundled Python is missing: {python}")

    firmware_source = distribution / "firmware" / "robot-platform"
    if not firmware_source.is_dir():
        raise OfflineFirstFlashError(f"Packaged firmware project is missing: {firmware_source}")

    project = work_root / "project"
    state = work_root / "state"
    if work_root.exists():
        shutil.rmtree(work_root, ignore_errors=True)
    project.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(firmware_source, project)
    state.mkdir(parents=True, exist_ok=True)

    bootstrap = state / "bootstrap.json"
    _bootstrap_config(bootstrap)

    base_env = os.environ.copy()
    base_env[runtime_paths.STATE_ROOT_ENV] = str(state.resolve())
    base_env[runtime_paths.APPLICATION_HOME_ENV] = str(distribution.resolve())
    base_env[runtime_paths.RUNTIME_MODE_ENV] = "packaged"
    base_env[runtime_paths.DEPENDENCY_MODE_ENV] = "artifact-closed"
    try:
        env, _ = dependency_closure.build_closed_environment(distribution, base_env)
    except dependency_closure.DependencyClosureError as exc:
        raise OfflineFirstFlashError(f"Unable to construct packaged dependency closure: {exc}") from exc

    # Fail closed on any attempted registry/network fallback.  A correct
    # production artifact has every required platform/package locally.
    dead_proxy = "http://127.0.0.1:9"
    env.update(
        {
            "HTTP_PROXY": dead_proxy,
            "HTTPS_PROXY": dead_proxy,
            "ALL_PROXY": dead_proxy,
            "NO_PROXY": "",
            "PLATFORMIO_SETTING_ENABLE_TELEMETRY": "false",
            "PLATFORMIO_DISABLE_UPGRADE_CHECK": "true",
            "PLATFORMIO_DISABLE_PROGRESSBAR": "true",
            "PLATFORMIO_NO_ANSI": "true",
            "ROBOT_BOOTSTRAP_CONFIG": str(bootstrap.resolve()),
            "ROBOT_WIFI_SSID": "RoboStudio-Offline-Gate",
            "ROBOT_WIFI_PASSWORD": "offline-test",
            "ROBOT_OTA_PASSWORD": "offline-gate-secret",
        }
    )

    command = [
        str(python.resolve()),
        "-m",
        "platformio",
        "run",
        "-e",
        "esp32dev_bootstrap",
        "-j",
        "1",
    ]
    started = time.monotonic()
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    try:
        process = subprocess.Popen(
            command,
            cwd=project,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creationflags,
            start_new_session=(os.name != "nt"),
        )
    except OSError as exc:
        raise OfflineFirstFlashError(f"Unable to start bundled PlatformIO: {exc}") from exc

    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        _kill_process_tree(process)
        output, _ = process.communicate()
        raise OfflineFirstFlashError(
            f"Packaged offline first-flash build timed out after {timeout:g}s\n{output[-6000:]}"
        ) from exc

    elapsed = time.monotonic() - started
    normalized = output.casefold()
    provisioning = [marker for marker in FORBIDDEN_PROVISIONING_MARKERS if marker in normalized]
    if provisioning:
        raise OfflineFirstFlashError(
            "Packaged first-flash attempted dependency provisioning "
            f"({', '.join(provisioning)}). Production first-flash must be offline.\n{output[-6000:]}"
        )
    if process.returncode != 0:
        raise OfflineFirstFlashError(
            f"Bundled PlatformIO first-flash build failed with exit code {process.returncode}.\n{output[-6000:]}"
        )

    build_dir = Path(env["PLATFORMIO_BUILD_DIR"])
    firmware = build_dir / "esp32dev_bootstrap" / "firmware.bin"
    if not firmware.is_file() or firmware.stat().st_size <= 0:
        raise OfflineFirstFlashError(
            f"Packaged offline build completed without firmware.bin: {firmware}"
        )
    return output, firmware, elapsed


def verify(
    release_dir: Path,
    *,
    timeout: float = 300.0,
    report_path: Path | None = None,
) -> dict[str, Any]:
    release_dir = Path(release_dir).expanduser().resolve()
    distribution = release_dir / "RoboStudio"
    if not distribution.is_dir():
        raise OfflineFirstFlashError(f"Production distribution is missing: {distribution}")

    artifact = _release_artifact(release_dir)
    manifest = release_package.validate_release_artifact(artifact)
    closure = production_platformio_closure.validate_distribution(distribution)
    package_evidence = _validate_package_install_metadata(distribution, closure, manifest)

    build_root = ROOT / ".build" / "production"
    work_root = build_root / "offline-first-flash-work"
    log_path = build_root / "offline-first-flash.log"
    if report_path is None:
        report_path = build_root / "offline-first-flash-report.json"
    report_path = Path(report_path).expanduser().resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        output, firmware, elapsed = _run_offline_bootstrap_build(
            distribution,
            work_root,
            timeout=timeout,
        )
        log_path.write_text(output, encoding="utf-8")
        report = {
            "schema": REPORT_SCHEMA,
            "schema_version": REPORT_SCHEMA_VERSION,
            "status": "PASS",
            "artifact": str(artifact),
            "distribution": str(distribution),
            "environment": "esp32dev_bootstrap",
            "network_fallback_allowed": False,
            "dependency_provisioning_observed": False,
            "package_install_metadata_verified": True,
            "verified_packages": package_evidence,
            "verified_package_count": len(package_evidence),
            "firmware_size": firmware.stat().st_size,
            "elapsed_seconds": round(elapsed, 3),
            "log": str(log_path),
        }
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report
    finally:
        shutil.rmtree(work_root, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify production RoboStudio packaged PlatformIO offline first-flash closure"
    )
    parser.add_argument(
        "--release-dir",
        type=Path,
        default=ROOT / "releases" / "production",
        help="directory containing RoboStudio distribution and production ZIP",
    )
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    try:
        report = verify(args.release_dir, timeout=args.timeout, report_path=args.report)
    except (OfflineFirstFlashError, Exception) as exc:
        # Keep the public CLI diagnostic compact; detailed PlatformIO output is
        # already included in failures raised by the operational build.
        print(f"Packaged PlatformIO offline first-flash gate: FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "Packaged PlatformIO offline first-flash gate: PASS "
        f"({report['verified_package_count']} packages, {report['elapsed_seconds']}s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
