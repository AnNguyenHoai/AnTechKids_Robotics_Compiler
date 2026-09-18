"""RSD-21.7 real compiler integration regression suite."""
from __future__ import annotations

import json
import sys
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import production_distribution, production_e2e, release_package


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def _make_app(path: Path) -> None:
    path.write_text(
        "import sys\n"
        "if '--self-test' in sys.argv:\n"
        " print('ROBOSTUDIO_E2E_READY')\n"
        " raise SystemExit(0)\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )


def _make_runtime(root: Path) -> tuple[Path, Path]:
    """Create a complete static application-owned PlatformIO closure."""
    runtime_bin = root / "runtime-bin"
    runtime_bin.mkdir(parents=True)
    shutil.copy2(sys.executable, runtime_bin / "python.exe")
    platformio_site = runtime_bin / "Lib" / "site-packages" / "platformio"
    platformio_site.mkdir(parents=True)
    (platformio_site / "__init__.py").write_text("__version__ = 'fixture'\n", encoding="utf-8")

    runtime_platformio = root / "runtime-platformio"
    platform = runtime_platformio / "platforms" / "espressif32"
    platform.mkdir(parents=True)
    (platform / "platform.json").write_text(
        json.dumps(
            {
                "name": "espressif32",
                "version": "6.12.0",
                "frameworks": {"arduino": {"package": "framework-arduinoespressif32"}},
                "packages": {
                    "toolchain-xtensa-esp32": {"version": ">=1.0.0"},
                    "framework-arduinoespressif32": {"version": "1.0.0"},
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    toolchain = runtime_platformio / "packages" / "toolchain-xtensa-esp32"
    toolchain.mkdir(parents=True)
    (toolchain / "package.json").write_text(
        '{"name":"toolchain-xtensa-esp32","version":"1.2.0","dependencies":{}}\n',
        encoding="utf-8",
    )
    framework = runtime_platformio / "packages" / "framework-arduinoespressif32"
    framework.mkdir(parents=True)
    (framework / "package.json").write_text(
        '{"name":"framework-arduinoespressif32","version":"1.0.0","dependencies":{}}\n',
        encoding="utf-8",
    )
    (runtime_platformio / "deployment-runtime.json").write_text(
        json.dumps(
            {
                "schema": "antechkids.robostudio.deployment-runtime",
                "schema_version": 1,
                "platformio_core": {
                    "source_not_embedded": True,
                    "required_directories": ["platforms", "packages"],
                    "file_count": 0,
                },
                "runtime_layout": {
                    "core_dir": "runtime/platformio",
                    "python": "runtime/bin/python.exe",
                    "platformio_module": "platformio",
                },
                "portable_python_required": True,
                "host_virtualenv_included": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return runtime_bin, runtime_platformio


def _make_firmware(root: Path) -> Path:
    firmware = root / "firmware"
    (firmware / "main").mkdir(parents=True)
    (firmware / "platformio.ini").write_text(
        "[platformio]\n"
        "src_dir = main\n\n"
        "[env:esp32dev]\n"
        "platform = espressif32@6.12.0\n"
        "board = esp32dev\n"
        "framework = arduino\n\n"
        "[env:esp32dev_ota]\n"
        "extends = env:esp32dev\n"
        "upload_protocol = espota\n\n"
        "[env:esp32dev_bootstrap]\n"
        "extends = env:esp32dev\n",
        encoding="utf-8",
    )
    (firmware / "wifi_config.py").write_text("# clean production fixture\n", encoding="utf-8")
    (firmware / "main" / "main.cpp").write_text("void setup() {}\nvoid loop() {}\n", encoding="utf-8")
    return firmware


def main() -> int:
    compiler_root = ROOT / "robot-compiler"
    frontend_root = ROOT / "robot-frontend-robosim" / "frontend"
    check("real compiler source exists", (compiler_root / "main.py").is_file())
    check("real RoboSim frontend exists", (frontend_root / "rewriter.py").is_file())

    with tempfile.TemporaryDirectory(prefix="rsd-21-7-test-") as td:
        base = Path(td)
        inputs = base / "inputs"
        inputs.mkdir()
        exe = inputs / "RoboStudio.exe"
        _make_app(exe)
        (inputs / "VERSION").write_text("1.2.3\n", encoding="utf-8")
        resources = inputs / "resources"
        (resources / "robot-isa").mkdir(parents=True)
        (resources / "robot-isa" / "target_profiles.json").write_text('{"targets":[]}\n', encoding="utf-8")
        runtime_bin, runtime_platformio = _make_runtime(inputs)
        firmware = _make_firmware(inputs)
        dist = base / "distribution"

        production_inputs = production_distribution.ProductionDistributionInputs(
            executable=exe,
            runtime_resources=resources,
            version_file=inputs / "VERSION",
            runtime_bin=runtime_bin,
            runtime_platformio=runtime_platformio,
            compiler_root=compiler_root,
            frontend_root=frontend_root,
            firmware_root=firmware,
        )
        result = production_distribution.build_production_distribution(production_inputs, dist)
        manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
        check("production distribution is created", dist.is_dir())
        check("production distribution contains real compiler entry", (dist / "compiler" / "main.py").is_file())
        check("production distribution contains frontend", (dist / "compiler" / "frontend" / "rewriter.py").is_file())
        check("production distribution contains firmware", (dist / "firmware" / "robot-platform" / "platformio.ini").is_file())
        check("compiler is recorded", manifest["compiler"] == "compiler/main.py")
        check("contract is recorded", manifest["compiler_contract"] == "compiler/robostudio_bridge.py")
        check("bundled Python is packaged", (dist / "runtime" / "bin" / "python.exe").is_file())
        check("bundled PlatformIO is packaged", (dist / "runtime" / "platformio" / "platforms").is_dir() and (dist / "runtime" / "platformio" / "packages").is_dir())
        check("runtime deployment manifest is packaged", (dist / "runtime" / "platformio" / "deployment-runtime.json").is_file())

        artifact = base / "release.zip"
        release = release_package.build_release(dist, artifact)
        with zipfile.ZipFile(artifact) as archive:
            names = set(archive.namelist())
        check("ZIP contains compiler", "compiler/main.py" in names)
        check("ZIP contains contract", "compiler/robostudio_bridge.py" in names)
        check("ZIP contains frontend", "compiler/frontend/rewriter.py" in names)
        check("ZIP contains bundled Python", "runtime/bin/python.exe" in names)
        check("ZIP contains firmware", "firmware/robot-platform/platformio.ini" in names)
        check("ZIP contains bundled PlatformIO", "runtime/platformio/deployment-runtime.json" in names and ("runtime/platformio/platforms/" in names or any(name.startswith("runtime/platformio/platforms/") for name in names)))
        check("ZIP validates", release_package.validate_release_artifact(artifact, release.manifest)["production_boundary"] is True)

        source = base / "sample.py"
        source.write_text("forward(50)\nwait(100)\nstop()\n", encoding="utf-8")
        result = production_e2e.evaluate_production_artifact(
            artifact=artifact,
            source=source,
            launch=True,
            launch_command=["{python}", "{app}", "--self-test"],
            compile_command=["{python}", "{compiler}", "--file", "{source}", "--output", "{output}"],
        )
        report = result.to_dict()
        compiler_output = Path(report["evidence"]["compiler_output"]).as_posix() if report["evidence"]["compiler_output"] else None
        check("RoboStudio starts from extracted ZIP", report["robostudio_started"] is True)
        check("real compiler executes", report["compiler_succeeded"] is True)
        check("compiler output produced", compiler_output == "e2e-output/program.h")
        check("E2E PASS", report["status"] == "PASS")

        # Regression guard: corrupting the packaged Python must make the E2E fail.
        broken_artifact = base / "release-broken-python.zip"
        with zipfile.ZipFile(artifact, "r") as source_zip, zipfile.ZipFile(broken_artifact, "w", compression=zipfile.ZIP_DEFLATED) as target_zip:
            for item in source_zip.infolist():
                payload = source_zip.read(item)
                if item.filename == "runtime/bin/python.exe":
                    payload = b"not-a-python-executable"
                target_zip.writestr(item, payload)
        try:
            production_e2e.evaluate_production_artifact(
                artifact=broken_artifact,
                source=source,
                launch=True,
                launch_command=["{python}", "{app}", "--self-test"],
                compile_command=["{python}", "{compiler}", "--file", "{source}", "--output", "{output}"],
            )
        except production_e2e.ProductionE2EError:
            print("PASS: broken bundled Python is rejected")
        else:
            raise AssertionError("broken bundled Python must make production E2E fail")

    print("RSD-21.7 Real Compiler Integration checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
