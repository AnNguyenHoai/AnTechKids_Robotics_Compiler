"""RSD-23 one-command production build regression suite."""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import one_command_production_build


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def make_runtime(root: Path) -> tuple[Path, Path]:
    runtime_bin = root / "python-runtime"
    runtime_bin.mkdir(parents=True)
    (runtime_bin / "python.exe").write_bytes(b"RSD23-PYTHON")
    module = runtime_bin / "Lib" / "site-packages" / "platformio"
    module.mkdir(parents=True)
    (module / "__init__.py").write_text("__version__ = 'fixture'\n", encoding="utf-8")

    platformio = root / "platformio-runtime"
    (platformio / "platforms").mkdir(parents=True)
    (platformio / "packages").mkdir(parents=True)
    (platformio / "platforms" / "fixture.txt").write_text("platform\n", encoding="utf-8")
    (platformio / "packages" / "fixture.txt").write_text("package\n", encoding="utf-8")
    return runtime_bin, platformio


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="rsd-23-test-") as td:
        root = Path(td)
        inputs = root / "inputs"
        inputs.mkdir()
        executable = inputs / "RoboStudio.exe"
        executable.write_bytes(b"RSD23-ROBOSTUDIO")
        (inputs / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        resources = inputs / "resources"
        resources.mkdir()
        (resources / "target_profiles.json").write_text('{"targets": []}\n', encoding="utf-8")
        runtime_bin, runtime_platformio = make_runtime(inputs)
        output = root / "release"

        result = one_command_production_build.build(
            executable=executable,
            runtime_bin=runtime_bin,
            runtime_platformio=runtime_platformio,
            runtime_resources=resources,
            version_file=inputs / "VERSION",
            source_revision="rsd23-fixture-revision",
            output=output,
        )
        distribution = output / "RoboStudio"
        manifest = json.loads((distribution / "distribution-manifest.json").read_text(encoding="utf-8"))
        deployment = json.loads((distribution / "runtime" / "platformio" / "deployment-runtime.json").read_text(encoding="utf-8"))

        check("build reports RSD-23 application-owned runtime", result["rsd23"]["runtime_model"] == "application-owned")
        check("portable Python is bundled", (distribution / "runtime" / "bin" / "python.exe").is_file())
        check("PlatformIO platforms are bundled", (distribution / "runtime" / "platformio" / "platforms").is_dir())
        check("PlatformIO packages are bundled", (distribution / "runtime" / "platformio" / "packages").is_dir())
        check("PlatformIO module is bundled", (distribution / "runtime" / "bin" / "Lib" / "site-packages" / "platformio" / "__init__.py").is_file())
        check("deployment manifest is normalized", deployment["portable_python_required"] is True)
        check("deployment manifest excludes host virtualenv", deployment["host_virtualenv_included"] is False)
        check("distribution is marked production boundary", manifest["production_boundary"] is True)
        check("distribution records bundled runtime", manifest["portable"] is True)
        check("release artifact exists", Path(result["artifact"]).is_file())

        with zipfile.ZipFile(result["artifact"]) as archive:
            names = set(archive.namelist())
        check("ZIP contains bundled Python", "runtime/bin/python.exe" in names)
        check("ZIP contains PlatformIO deployment manifest", "runtime/platformio/deployment-runtime.json" in names)
        check("ZIP contains PlatformIO platforms", any(name.startswith("runtime/platformio/platforms/") for name in names))
        check("ZIP contains PlatformIO packages", any(name.startswith("runtime/platformio/packages/") for name in names))

        # Source runtime must remain unchanged: deployment manifest is generated only in staging.
        check("source PlatformIO input remains untouched", not (runtime_platformio / "deployment-runtime.json").exists())

    print("RSD-23 one-command production build checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
