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
        with patch.dict(os.environ, {runtime_paths.APPLICATION_HOME_ENV: str(root)}, clear=False):
            with patch.object(deployment_runtime, "is_frozen", return_value=True):
                env = deployment_runtime.deployment_runtime_environment({"PATH": "host-path"})
                core = root / "runtime" / "platformio"
                check("frozen deployment core is application-owned", env["PLATFORMIO_CORE_DIR"] == str(core))
                check("platform packages are isolated", env["PLATFORMIO_PACKAGES_DIR"] == str(core / "packages"))
                check("platforms are isolated", env["PLATFORMIO_PLATFORMS_DIR"] == str(core / "platforms"))
                check("build workspace is isolated", env["PLATFORMIO_WORKSPACE_DIR"] == str(core / "workspace"))
                check("PlatformIO upgrade checks are disabled", env["PLATFORMIO_DISABLE_UPGRADE_CHECK"] == "true")
                check("deployment output has no ANSI", env["PLATFORMIO_NO_ANSI"] == "true")
                check("host PATH is preserved for child-process compatibility", env["PATH"] == "host-path")

            runtime = root / "runtime" / "platformio"
            (runtime / "platforms").mkdir(parents=True)
            (runtime / "packages").mkdir(parents=True)
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
