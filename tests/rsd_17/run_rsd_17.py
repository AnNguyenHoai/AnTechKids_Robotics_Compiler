"""RSD-17 production distribution builder tests."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import production_distribution, production_artifact_boundary


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"PASS: {name}")


def expect_error(name: str, fn, expected: str) -> None:
    try:
        fn()
    except production_distribution.ProductionDistributionError as exc:
        check(name, expected in str(exc))
    else:
        raise AssertionError(f"{name}: validation unexpectedly succeeded")


def make_inputs(root: Path) -> production_distribution.ProductionDistributionInputs:
    executable = root / "app-build" / "RoboStudio.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"production-executable")
    (executable.parent / "Qt6Core.dll").write_bytes(b"application-local-dll")

    version = root / "VERSION"
    version.write_text("7.2.0\n", encoding="utf-8")

    compiler = root / "compiler"
    (compiler / "compiler").mkdir(parents=True)
    (compiler / "main.py").write_text("print('compiler')\n", encoding="utf-8")
    (compiler / "compiler" / "__init__.py").write_text("", encoding="utf-8")
    (compiler / "robostudio_bridge.py").write_text("def compile_request(request):\n    return request\n", encoding="utf-8")

    frontend = root / "frontend"
    frontend.mkdir()
    (frontend / "__init__.py").write_text("", encoding="utf-8")
    (frontend / "rewriter.py").write_text("def rewrite(source):\n    return source\n", encoding="utf-8")

    resources = root / "resources"
    profile = resources / "robot-isa" / "target_profiles.json"
    profile.parent.mkdir(parents=True)
    profile.write_text('{"targets": []}\n', encoding="utf-8")

    firmware = root / "firmware"
    (firmware / "main").mkdir(parents=True)
    (firmware / "main" / "main.cpp").write_text("void setup() {}\nvoid loop() {}\n", encoding="utf-8")
    (firmware / "wifi_config.py").write_text("Import('env')\n", encoding="utf-8")
    (firmware / "platformio.ini").write_text(
        "[platformio]\n"
        "src_dir = main\n\n"
        "[env:esp32dev]\n"
        "platform = espressif32@6.12.0\n"
        "board = esp32dev\n"
        "framework = arduino\n\n"
        "[env:esp32dev_bootstrap]\n"
        "extends = env:esp32dev\n\n"
        "[env:esp32dev_ota]\n"
        "extends = env:esp32dev\n"
        "upload_protocol = espota\n",
        encoding="utf-8",
    )

    runtime_bin = root / "runtime-bin"
    (runtime_bin / "Lib" / "site-packages" / "platformio").mkdir(parents=True)
    (runtime_bin / "Lib" / "encodings").mkdir(parents=True)
    (runtime_bin / "python.exe").write_bytes(b"portable-python")
    (runtime_bin / "python310.dll").write_bytes(b"portable-python-runtime-dll")
    (runtime_bin / "Lib" / "encodings" / "__init__.py").write_text("", encoding="utf-8")
    (runtime_bin / "Lib" / "site-packages" / "platformio" / "__init__.py").write_text("__version__ = 'test'\n", encoding="utf-8")

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
        ) + "\n",
        encoding="utf-8",
    )
    toolchain = runtime_platformio / "packages" / "toolchain-xtensa-esp32"
    toolchain.mkdir(parents=True)
    (toolchain / "package.json").write_text('{"name": "toolchain-xtensa-esp32", "version": "1.2.0", "dependencies": {}}\n', encoding="utf-8")
    framework_package = runtime_platformio / "packages" / "framework-arduinoespressif32"
    framework_package.mkdir(parents=True)
    (framework_package / "package.json").write_text('{"name": "framework-arduinoespressif32", "version": "1.0.0", "dependencies": {}}\n', encoding="utf-8")
    (runtime_platformio / "deployment-runtime.json").write_text(
        json.dumps(
            {
                "schema": "antechkids.robostudio.deployment-runtime",
                "schema_version": 1,
                "platformio_core": {"source_not_embedded": True, "required_directories": ["platforms", "packages"], "file_count": 0},
                "runtime_layout": {"core_dir": "runtime/platformio", "python": "runtime/bin/python.exe", "platformio_module": "platformio"},
                "portable_python_required": True,
                "host_virtualenv_included": False,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    from tools import runtime_resources
    runtime_resources.write_resource_manifest(resources)

    return production_distribution.ProductionDistributionInputs(
        executable=executable,
        runtime_resources=resources,
        version_file=version,
        runtime_bin=runtime_bin,
        runtime_platformio=runtime_platformio,
        compiler_root=compiler,
        frontend_root=frontend,
        firmware_root=firmware,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="robostudio-rsd17-") as temp:
        root = Path(temp)
        inputs = make_inputs(root)
        output = root / "distribution"

        old_cwd = Path.cwd()
        os.chdir(root / "app-build")
        try:
            result = production_distribution.build_production_distribution(inputs, output)
        finally:
            os.chdir(old_cwd)

        check("production distribution is created", result.distribution_root.is_dir())
        check("application is copied", (output / "RoboStudio.exe").is_file())
        check("application-local DLL is copied", (output / "Qt6Core.dll").is_file())
        check("repository VERSION is integrated", (output / "VERSION").read_text(encoding="utf-8").strip() == "7.2.0")
        check("bundled Python is included", (output / "runtime" / "bin" / "python.exe").is_file())
        check("bundled Python runtime DLL is included", (output / "runtime" / "bin" / "python310.dll").is_file())
        check("bundled Python stdlib is included", (output / "runtime" / "bin" / "Lib" / "encodings" / "__init__.py").is_file())
        check("bundled PlatformIO is included", (output / "runtime" / "platformio" / "platforms").is_dir())
        check("deployment runtime manifest is included", (output / "runtime" / "platformio" / "deployment-runtime.json").is_file())
        check("runtime resources are included", (output / "runtime" / "resources" / "robot-isa" / "target_profiles.json").is_file())
        check("application-owned compiler is included", (output / "compiler" / "main.py").is_file())
        check("compiler contract is included", (output / "compiler" / "robostudio_bridge.py").is_file())
        check("RoboSim frontend is included", (output / "compiler" / "frontend" / "rewriter.py").is_file())
        check("production firmware is included", (output / "firmware" / "robot-platform" / "platformio.ini").is_file())
        check("production artifact boundary passes", production_artifact_boundary.validate_distribution_root(output)["status"] == "PASS")

        manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
        check("distribution manifest records application", manifest["application"] == "RoboStudio.exe")
        check("distribution manifest records production portability", manifest["portable"] is False)
        check("distribution manifest records application-local DLL", any(item["path"] == "Qt6Core.dll" for item in manifest["files"]))
        check("distribution VERSION is not source-relative", Path(manifest["files"][0]["path"]).is_absolute() is False)
        check("distribution manifest records compiler", manifest["compiler"] == "compiler/main.py")
        check("distribution manifest records compiler contract", manifest["compiler_contract"] == "compiler/robostudio_bridge.py")

        missing_dll = root / "missing-python-dll"
        import shutil
        shutil.copytree(inputs.runtime_bin, missing_dll)
        (missing_dll / "python310.dll").unlink()
        bad_runtime = production_distribution.ProductionDistributionInputs(
            executable=inputs.executable, runtime_resources=inputs.runtime_resources,
            version_file=inputs.version_file, runtime_bin=missing_dll,
            runtime_platformio=inputs.runtime_platformio, compiler_root=inputs.compiler_root,
            frontend_root=inputs.frontend_root, firmware_root=inputs.firmware_root,
        )
        expect_error("missing Python runtime DLL is rejected", lambda: production_distribution.build_production_distribution(bad_runtime, root / "bad-runtime-output"), "runtime DLL")

        missing_version = production_distribution.ProductionDistributionInputs(
            executable=inputs.executable, runtime_resources=inputs.runtime_resources,
            version_file=root / "missing-VERSION", runtime_bin=inputs.runtime_bin,
            runtime_platformio=inputs.runtime_platformio, compiler_root=inputs.compiler_root,
            frontend_root=inputs.frontend_root, firmware_root=inputs.firmware_root,
        )
        expect_error("missing production VERSION is rejected", lambda: production_distribution.build_production_distribution(missing_version, root / "bad-version"), "VERSION")

        bad_compiler = root / "bad-compiler"
        bad_compiler.mkdir()
        bad_inputs = production_distribution.ProductionDistributionInputs(
            executable=inputs.executable, runtime_resources=inputs.runtime_resources,
            version_file=inputs.version_file, runtime_bin=inputs.runtime_bin,
            runtime_platformio=inputs.runtime_platformio, compiler_root=bad_compiler,
            frontend_root=inputs.frontend_root, firmware_root=inputs.firmware_root,
        )
        expect_error("invalid application-owned compiler is rejected", lambda: production_distribution.build_production_distribution(bad_inputs, root / "bad-compiler-output"), "application-owned compiler")

        forbidden = output / "runtime" / "bin" / ".venv"
        forbidden.mkdir(parents=True)
        try:
            production_artifact_boundary.validate_distribution_root(output)
        except production_artifact_boundary.ProductionArtifactBoundaryError as exc:
            check("developer virtualenv payload is rejected by production boundary", ".venv" in str(exc))
        else:
            raise AssertionError("developer virtualenv payload is not rejected")

    print("RSD-17 production distribution checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
