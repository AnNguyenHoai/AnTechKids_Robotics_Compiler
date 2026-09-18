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


def main() -> int:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "RoboStudio"
        root.mkdir()
        (root / "runtime" / "bin").mkdir(parents=True)
        (root / "runtime" / "platformio" / "platforms").mkdir(parents=True)
        (root / "runtime" / "platformio" / "packages").mkdir(parents=True)
        with patch.dict(os.environ, {runtime_paths.APPLICATION_HOME_ENV: str(root)}, clear=False):
            with patch.object(deployment_runtime, "is_frozen", return_value=True):
                env = deployment_runtime.deployment_runtime_environment({"PATH": "host-path"})
                core = root / "runtime" / "platformio"
                check("frozen deployment core is application-owned", Path(env["PLATFORMIO_CORE_DIR"]).resolve() == core.resolve())
                check("platform packages are isolated", Path(env["PLATFORMIO_PACKAGES_DIR"]).resolve() == (core / "packages").resolve())
                check("platforms are isolated", Path(env["PLATFORMIO_PLATFORMS_DIR"]).resolve() == (core / "platforms").resolve())
                check("build workspace is isolated", Path(env["PLATFORMIO_WORKSPACE_DIR"]).resolve() == (core / "workspace").resolve())
                check("PlatformIO upgrade checks are disabled", env["PLATFORMIO_DISABLE_UPGRADE_CHECK"] == "true")
                check("deployment output has no ANSI", env["PLATFORMIO_NO_ANSI"] == "true")
                check("frozen deployment enables dependency closure", env["ROBOSTUDIO_DEPENDENCY_MODE"] == "artifact-closed")
                check("host PATH is not inherited by packaged runtime", env["PATH"] != "host-path")

            with patch.object(deployment_runtime, "is_frozen", return_value=False):
                dev_env = deployment_runtime.deployment_runtime_environment({"PATH": "host-path"})
                check("source development preserves host PATH", dev_env["PATH"] == "host-path")

            runtime = root / "runtime" / "platformio"
            check("runtime validation accepts complete layout", deployment_runtime.validate_deployment_runtime() == runtime)

            source = Path(temp) / "pio-home"
            (source / "platforms" / "espressif32").mkdir(parents=True)
            (source / "packages" / "framework-arduinoespressif32").mkdir(parents=True)
            (source / "packages" / "tool-esptoolpy").mkdir(parents=True)
            (source / "platforms" / "espressif32" / "package.json").write_text("{}", encoding="utf-8")
            (source / "packages" / "tool-esptoolpy" / "package.json").write_text("{}", encoding="utf-8")
            manifest = package_deployment_runtime.package_runtime(source, runtime)
            check("packager writes runtime manifest", (runtime / "deployment-runtime.json").is_file())
            check("packager copies platform metadata", (runtime / "platforms" / "espressif32" / "package.json").is_file())
            check("packager copies upload tool package", (runtime / "packages" / "tool-esptoolpy" / "package.json").is_file())
            check("manifest declares portable Python", manifest["portable_python_required"] is True)
            check("host penv is excluded", manifest["host_virtualenv_included"] is False)

            bad = Path(temp) / "bad-pio-home"
            (bad / "platforms").mkdir(parents=True)
            (bad / "packages").mkdir(parents=True)
            (bad / "penv").mkdir()
            try:
                package_deployment_runtime.package_runtime(bad, Path(temp) / "bad-output")
            except RuntimeError as exc:
                check("packager rejects host-specific penv", "Refusing to package PlatformIO penv" in str(exc))
            else:
                raise AssertionError("host-specific penv was unexpectedly accepted")

    print("RSD-04 deployment runtime checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
