#!/usr/bin/env python3
"""Verify that packaged RoboStudio can build and enter USB first-flash offline.

This is a production-release gate, not a source-tree compile test. It uses the
already assembled ``releases/production/RoboStudio`` distribution, a completely
fresh external RoboStudio state root, the bundled Python interpreter, and the
bundled PlatformIO platform/package stores. Network proxies are deliberately
poisoned so a missing dependency cannot be hidden by the CI/build machine.

On Windows the acceptance state intentionally contains whitespace. Real users
commonly have profile names such as ``EASTVN - An Nguyen``; the gate therefore
requires the production dependency alias to escape that profile and remain a
short whitespace-free path before invoking the Xtensa compiler.

The gate also performs a second PlatformIO ``upload`` target against a guaranteed
invalid port. Upload itself must fail, but only *after* PlatformIO reaches the
uploader. This proves upload-time dependencies are packaged without requiring a
physical robot on CI.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
else:
    ROOT = Path(__file__).resolve().parents[1]

from tools import (
    build_isolation,
    dependency_closure,
    deployment_runtime,
    first_flash_runtime_contract,
    production_platformio_closure,
    release_package,
    runtime_paths,
)

REPORT_SCHEMA = "antechkids.robostudio.packaged-platformio-offline-first-flash"
REPORT_SCHEMA_VERSION = 3
FORBIDDEN_PROVISIONING_MARKERS = (
    "tool manager: installing",
    "platform manager: installing",
    "library manager: installing",
    "downloading...",
    "downloading ",
)
UPLOAD_PROBE_PORT = "COM256" if os.name == "nt" else "/dev/robostudio-nonexistent"


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
        archived_piopm = (
            Path("runtime") / "platformio" / metadata_relative.parent / ".piopm"
        ).as_posix()
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


def _acceptance_state_root(work_root: Path) -> Path:
    """Return fresh state that deliberately reproduces a spaced Windows profile."""
    token = f"{os.getpid():x}-{time.time_ns() & 0xFFFFFF:x}"
    if os.name == "nt":
        base = Path(os.environ.get("PUBLIC") or tempfile.gettempdir()) / "RSF"
        return base / "User Profile With Spaces" / token
    return work_root / "state with spaces" / token


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


def _run_platformio(
    command: list[str],
    *,
    project: Path,
    env: dict[str, str],
    timeout: float,
    label: str,
) -> tuple[int, str, float]:
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
        raise OfflineFirstFlashError(f"Unable to start bundled PlatformIO {label}: {exc}") from exc

    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        _kill_process_tree(process)
        output, _ = process.communicate()
        raise OfflineFirstFlashError(
            f"Packaged {label} timed out after {timeout:g}s\n{output[-6000:]}"
        ) from exc
    return process.returncode, output, time.monotonic() - started


def _assert_no_provisioning(output: str, label: str) -> None:
    normalized = output.casefold()
    provisioning = [marker for marker in FORBIDDEN_PROVISIONING_MARKERS if marker in normalized]
    if provisioning:
        raise OfflineFirstFlashError(
            f"Packaged {label} attempted dependency provisioning "
            f"({', '.join(provisioning)}). Production first-flash must be offline.\n{output[-6000:]}"
        )


def _run_offline_bootstrap_build(
    distribution: Path,
    work_root: Path,
    *,
    timeout: float,
) -> tuple[str, str, Path, float, float, dict[str, str], Path]:
    python = distribution / "runtime" / "bin" / "python.exe"
    if not python.is_file():
        raise OfflineFirstFlashError(f"Bundled Python is missing: {python}")

    firmware_source = distribution / "firmware" / "robot-platform"
    if not firmware_source.is_dir():
        raise OfflineFirstFlashError(f"Packaged firmware project is missing: {firmware_source}")

    if work_root.exists():
        shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True, exist_ok=True)
    state = _acceptance_state_root(work_root)
    state.mkdir(parents=True, exist_ok=True)
    project = state / "build" / "bootstrap" / "platformio" / "runs" / "gate" / "firmware"
    project.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(firmware_source, project)

    bootstrap = state / "bootstrap.json"
    _bootstrap_config(bootstrap)

    base_env = os.environ.copy()
    base_env[runtime_paths.STATE_ROOT_ENV] = str(state.resolve())
    base_env[runtime_paths.APPLICATION_HOME_ENV] = str(distribution.resolve())
    base_env[runtime_paths.RUNTIME_MODE_ENV] = "packaged"
    base_env[runtime_paths.DEPENDENCY_MODE_ENV] = "artifact-closed"
    try:
        env, _ = dependency_closure.build_closed_environment(distribution, base_env)
        env = deployment_runtime.prepare_platformio_dependency_aliases(distribution, env)
        env = build_isolation.build_environment("bootstrap", env)
    except (
        dependency_closure.DependencyClosureError,
        deployment_runtime.DeploymentRuntimeError,
        build_isolation.BuildIsolationError,
    ) as exc:
        raise OfflineFirstFlashError(f"Unable to construct packaged dependency closure: {exc}") from exc

    if os.name == "nt":
        alias = env.get(deployment_runtime.PLATFORMIO_DEPENDENCY_ALIAS_ROOT_ENV, "")
        packages_dir = env.get("PLATFORMIO_PACKAGES_DIR", "")
        platforms_dir = env.get("PLATFORMIO_PLATFORMS_DIR", "")
        if not alias or any(char.isspace() for char in alias):
            raise OfflineFirstFlashError(
                f"Windows PlatformIO dependency alias is not whitespace-safe: {alias!r}"
            )
        if any(char.isspace() for char in packages_dir) or any(char.isspace() for char in platforms_dir):
            raise OfflineFirstFlashError(
                "Windows PlatformIO dependency paths still contain whitespace after aliasing: "
                f"platforms={platforms_dir!r}, packages={packages_dir!r}"
            )
        if not any(char.isspace() for char in str(state)):
            raise OfflineFirstFlashError(
                "Windows acceptance state did not exercise the spaced-profile regression scenario"
            )

    # Fail closed on any attempted registry/network fallback. A correct
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

    build_command = [
        str(python.resolve()),
        "-m",
        "platformio",
        "run",
        "-e",
        "esp32dev_bootstrap",
        "-j",
        "1",
    ]
    build_code, build_output, build_elapsed = _run_platformio(
        build_command,
        project=project,
        env=env,
        timeout=timeout,
        label="offline first-flash build",
    )
    _assert_no_provisioning(build_output, "first-flash build")
    if build_code != 0:
        raise OfflineFirstFlashError(
            f"Bundled PlatformIO first-flash build failed with exit code {build_code}.\n{build_output[-6000:]}"
        )

    build_dir = Path(env["PLATFORMIO_BUILD_DIR"])
    firmware = build_dir / "esp32dev_bootstrap" / "firmware.bin"
    if not firmware.is_file() or firmware.stat().st_size <= 0:
        raise OfflineFirstFlashError(
            f"Packaged offline build completed without firmware.bin: {firmware}"
        )

    # Exercise the real USB upload target with the already-built project. The
    # port is deliberately invalid: CI must reach esptool and fail on serial I/O,
    # never while resolving/installing an uploader or recompiling a broken
    # framework path.
    upload_command = [
        str(python.resolve()),
        "-m",
        "platformio",
        "run",
        "-e",
        "esp32dev_bootstrap",
        "-j",
        "1",
        "-t",
        "upload",
        "--upload-port",
        UPLOAD_PROBE_PORT,
    ]
    upload_code, upload_output, upload_elapsed = _run_platformio(
        upload_command,
        project=project,
        env=env,
        timeout=min(timeout, 120.0),
        label="USB upload dependency probe",
    )
    _assert_no_provisioning(upload_output, "USB upload dependency probe")
    normalized_upload = upload_output.casefold()
    if upload_code == 0:
        raise OfflineFirstFlashError(
            f"USB upload probe unexpectedly succeeded on invalid port {UPLOAD_PROBE_PORT}"
        )
    if "uploading" not in normalized_upload or UPLOAD_PROBE_PORT.casefold() not in normalized_upload:
        raise OfflineFirstFlashError(
            "USB upload probe failed before reaching the uploader. "
            f"Expected an upload attempt against {UPLOAD_PROBE_PORT}.\n{upload_output[-6000:]}"
        )

    return (
        build_output,
        upload_output,
        firmware,
        build_elapsed,
        upload_elapsed,
        env,
        state,
    )


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
    try:
        payload = first_flash_runtime_contract.validate_esp32dev_first_flash_payload(
            distribution / "runtime" / "platformio"
        )
        first_flash_runtime_contract.validate_archive_inventory(
            str(item.get("path", "")) for item in manifest.get("files", [])
        )
    except first_flash_runtime_contract.FirstFlashRuntimeContractError as exc:
        raise OfflineFirstFlashError(str(exc)) from exc

    build_root = ROOT / ".build" / "production"
    work_root = build_root / "offline-first-flash-work"
    log_path = build_root / "offline-first-flash.log"
    if report_path is None:
        report_path = build_root / "offline-first-flash-report.json"
    report_path = Path(report_path).expanduser().resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    state: Path | None = None

    try:
        (
            build_output,
            upload_output,
            firmware,
            build_elapsed,
            upload_elapsed,
            env,
            state,
        ) = _run_offline_bootstrap_build(distribution, work_root, timeout=timeout)
        log_path.write_text(
            build_output
            + "\n\n=== USB UPLOAD DEPENDENCY PROBE (EXPECTED INVALID PORT FAILURE) ===\n"
            + upload_output,
            encoding="utf-8",
        )
        alias_root = env.get(deployment_runtime.PLATFORMIO_DEPENDENCY_ALIAS_ROOT_ENV, "")
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
            "first_flash_payload_verified": True,
            "first_flash_payload": payload,
            "spaced_profile_scenario_verified": bool(os.name != "nt" or any(c.isspace() for c in str(state))),
            "windows_short_dependency_alias": alias_root,
            "dependency_alias_whitespace_free": bool(
                os.name != "nt" or (alias_root and not any(c.isspace() for c in alias_root))
            ),
            "platforms_dir": env.get("PLATFORMIO_PLATFORMS_DIR", ""),
            "packages_dir": env.get("PLATFORMIO_PACKAGES_DIR", ""),
            "verified_packages": package_evidence,
            "verified_package_count": len(package_evidence),
            "firmware_size": firmware.stat().st_size,
            "build_elapsed_seconds": round(build_elapsed, 3),
            "usb_upload_dependency_probe": True,
            "usb_upload_probe_port": UPLOAD_PROBE_PORT,
            "usb_upload_probe_reached_uploader": True,
            "upload_probe_elapsed_seconds": round(upload_elapsed, 3),
            "elapsed_seconds": round(build_elapsed + upload_elapsed, 3),
            "log": str(log_path),
        }
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return report
    finally:
        shutil.rmtree(work_root, ignore_errors=True)
        if state is not None:
            shutil.rmtree(state, ignore_errors=True)


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
    except Exception as exc:
        print(f"Packaged PlatformIO offline first-flash gate: FAIL: {exc}", file=sys.stderr)
        return 1
    print(
        "Packaged PlatformIO offline first-flash gate: PASS "
        f"({report['verified_package_count']} packages, {report['elapsed_seconds']}s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
