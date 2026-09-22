from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import deployment_runtime, package_deployment_runtime, runtime_paths


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def _packaged_base_env(state: Path) -> dict[str, str]:
    """Build a hostile packaged fixture without deleting required OS identity.

    Production dependency closure intentionally strips host tool lookup, but on
    Windows the short PlatformIO dependency alias is created through the
    OS-owned ``cmd.exe`` under ``SystemRoot\\System32``. Keep only the Windows
    system-root identity needed to locate that trusted OS helper; do not restore
    the host PATH or any host PlatformIO/Python state.
    """
    env = {"PATH": "host-path", runtime_paths.STATE_ROOT_ENV: str(state)}
    if os.name == "nt":
        system_root = os.environ.get("SystemRoot") or os.environ.get("WINDIR")
        if not system_root:
            raise AssertionError("Windows RSD-04 fixture requires SystemRoot/WINDIR")
        env["SystemRoot"] = system_root
        env["WINDIR"] = system_root
        public = os.environ.get("PUBLIC")
        if public:
            env["PUBLIC"] = public
    return env


def _prepare_esp32_payload(packages: Path) -> None:
    """Create the minimum physical ESP32 package contract for this fixture.

    RSD-04 tests path/state ownership, not PlatformIO package installation. Its
    packaged-runtime fixture must nevertheless satisfy the same fail-closed
    physical deployment contract as a real production artifact before calling
    ``validate_deployment_runtime``.
    """
    framework = packages / deployment_runtime.ESP32_FRAMEWORK_PACKAGE
    for relative in (
        Path(".piopm"),
        Path("cores") / "esp32" / "Arduino.h",
        Path("variants") / "esp32" / "pins_arduino.h",
    ):
        path = framework / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("fixture\n", encoding="utf-8")

    for name in deployment_runtime.ESP32_USB_TOOL_PACKAGES:
        metadata = packages / name / ".piopm"
        metadata.parent.mkdir(parents=True, exist_ok=True)
        metadata.write_text("{}\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "RoboStudio"
        state = Path(temp) / "RoboStudio State"
        root.mkdir()
        (root / "runtime" / "bin").mkdir(parents=True)
        (root / "runtime" / "platformio" / "platforms").mkdir(parents=True)
        packages = root / "runtime" / "platformio" / "packages"
        packages.mkdir(parents=True)
        _prepare_esp32_payload(packages)

        with patch.dict(os.environ, {runtime_paths.APPLICATION_HOME_ENV: str(root)}, clear=False):
            with patch.object(deployment_runtime, "is_frozen", return_value=True):
                env = deployment_runtime.deployment_runtime_environment(
                    _packaged_base_env(state)
                )
                payload = root / "runtime" / "platformio"
                mutable_core = state / "platformio" / "core"
                check(
                    "frozen deployment core state is external",
                    Path(env["PLATFORMIO_CORE_DIR"]).resolve() == mutable_core.resolve(),
                )
                check(
                    "frozen deployment core state is outside application",
                    root.resolve() not in Path(env["PLATFORMIO_CORE_DIR"]).resolve().parents,
                )
                check(
                    "platform packages remain application-owned",
                    Path(env["PLATFORMIO_PACKAGES_DIR"]).resolve()
                    == (payload / "packages").resolve(),
                )
                check(
                    "platforms remain application-owned",
                    Path(env["PLATFORMIO_PLATFORMS_DIR"]).resolve()
                    == (payload / "platforms").resolve(),
                )
                if os.name == "nt":
                    alias_root = Path(
                        env[deployment_runtime.PLATFORMIO_DEPENDENCY_ALIAS_ROOT_ENV]
                    ).resolve()
                    check(
                        "Windows short dependency alias is external",
                        root.resolve() not in alias_root.parents
                        and alias_root != root.resolve(),
                    )
                    check(
                        "Windows short dependency alias contains no whitespace",
                        not any(char.isspace() for char in str(alias_root)),
                    )
                    check(
                        "Windows package alias resolves to immutable payload",
                        Path(env["PLATFORMIO_PACKAGES_DIR"]).resolve()
                        == (payload / "packages").resolve(),
                    )
                    check(
                        "Windows platform alias resolves to immutable payload",
                        Path(env["PLATFORMIO_PLATFORMS_DIR"]).resolve()
                        == (payload / "platforms").resolve(),
                    )
                check(
                    "default mutable workspace is external",
                    Path(env["PLATFORMIO_WORKSPACE_DIR"]).resolve()
                    == (state / "platformio" / "workspace").resolve(),
                )
                check(
                    "PlatformIO upgrade checks are disabled",
                    env["PLATFORMIO_DISABLE_UPGRADE_CHECK"] == "true",
                )
                check("deployment output has no ANSI", env["PLATFORMIO_NO_ANSI"] == "true")
                check(
                    "frozen deployment enables dependency closure",
                    env["ROBOSTUDIO_DEPENDENCY_MODE"] == "artifact-closed",
                )
                check("host PATH is not inherited by packaged runtime", env["PATH"] != "host-path")

            with patch.object(deployment_runtime, "is_frozen", return_value=False):
                dev_env = deployment_runtime.deployment_runtime_environment({"PATH": "host-path"})
                check("source development preserves host PATH", dev_env["PATH"] == "host-path")

            runtime = root / "runtime" / "platformio"
            check(
                "runtime validation accepts complete immutable payload layout",
                deployment_runtime.validate_deployment_runtime() == runtime,
            )

            source = Path(temp) / "pio-home"
            (source / "platforms" / "espressif32").mkdir(parents=True)
            (source / "packages" / "framework-arduinoespressif32").mkdir(parents=True)
            (source / "packages" / "tool-esptoolpy").mkdir(parents=True)
            (source / "platforms" / "espressif32" / "package.json").write_text(
                "{}", encoding="utf-8"
            )
            (source / "packages" / "tool-esptoolpy" / "package.json").write_text(
                "{}", encoding="utf-8"
            )
            manifest = package_deployment_runtime.package_runtime(source, runtime)
            check("packager writes runtime manifest", (runtime / "deployment-runtime.json").is_file())
            check(
                "packager copies platform metadata",
                (runtime / "platforms" / "espressif32" / "package.json").is_file(),
            )
            check(
                "packager copies upload tool package",
                (runtime / "packages" / "tool-esptoolpy" / "package.json").is_file(),
            )
            check("manifest declares portable Python", manifest["portable_python_required"] is True)
            check("host penv is excluded", manifest["host_virtualenv_included"] is False)

            bad = Path(temp) / "bad-pio-home"
            (bad / "platforms").mkdir(parents=True)
            (bad / "packages").mkdir(parents=True)
            (bad / "penv").mkdir()
            try:
                package_deployment_runtime.package_runtime(
                    bad, Path(temp) / "bad-output"
                )
            except RuntimeError as exc:
                check(
                    "packager rejects host-specific penv",
                    "Refusing to package PlatformIO penv" in str(exc),
                )
            else:
                raise AssertionError("host-specific penv was unexpectedly accepted")

    print("RSD-04 deployment runtime checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
